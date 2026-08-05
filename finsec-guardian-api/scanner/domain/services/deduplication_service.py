from __future__ import annotations

from collections import defaultdict
from typing import ClassVar, Iterable

from scanner.domain.entities import Finding
from scanner.domain.exceptions import DomainValidationError
from scanner.domain.value_objects.vulnerability_signature import (
    VulnerabilitySignature,
)


class DeduplicationService:
    """
    Stateless Domain Service responsible for identifying, grouping,
    deduplicating, and merging security findings based on their
    VulnerabilitySignature.

    This service operates on the semantic identity of findings rather
    than their database identity.

    Responsibilities
    ----------------
    • Detect duplicate findings.
    • Remove duplicate findings.
    • Locate duplicate findings.
    • Group findings by signature.
    • Merge semantically identical findings.

    The service is intentionally stateless and therefore exposes only
    class methods.
    """

    _EMPTY: ClassVar[tuple[Finding, ...]] = ()

    # ==========================================================
    # Validation
    # ==========================================================

    @staticmethod
    def _validate_findings(
        findings: Iterable[Finding],
        *,
        parameter_name: str = "findings",
    ) -> tuple[Finding, ...]:
        """
        Materialize an iterable into a tuple and validate every item.

        Raises
        ------
        DomainValidationError
            If the iterable is None or contains non-Finding objects.
        """
        if findings is None:
            raise DomainValidationError(
                f"'{parameter_name}' cannot be None."
            )

        materialized = tuple(findings)

        for index, item in enumerate(materialized):
            if not isinstance(item, Finding):
                raise DomainValidationError(
                    f"Item at index {index} in "
                    f"'{parameter_name}' is not a Finding."
                )

        return materialized

    # ==========================================================
    # Internal Helpers
    # ==========================================================

    @classmethod
    def _signature_groups(
        cls,
        findings: tuple[Finding, ...],
    ) -> dict[VulnerabilitySignature, list[Finding]]:
        """
        Group findings by VulnerabilitySignature.

        This helper underpins every deduplication operation.
        """
        grouped: dict[
            VulnerabilitySignature,
            list[Finding],
        ] = defaultdict(list)

        for finding in findings:
            grouped[finding.signature].append(finding)

        return grouped

    # ==========================================================
    # Public API
    # ==========================================================

    @classmethod
    def is_duplicate(
        cls,
        finding: Finding,
        findings: Iterable[Finding],
    ) -> bool:
        """
        Determine whether another finding with the same signature
        already exists.

        The supplied finding itself is ignored.
        """
        if not isinstance(finding, Finding):
            raise DomainValidationError(
                "'finding' must be a Finding."
            )

        materialized = cls._validate_findings(findings)

        return any(
            existing.signature == finding.signature
            for existing in materialized
            if existing is not finding
        )

    @classmethod
    def remove_duplicates(
        cls,
        findings: Iterable[Finding],
    ) -> tuple[Finding, ...]:
        """
        Remove duplicate findings while preserving insertion order.

        The first occurrence of every signature is retained.
        """
        materialized = cls._validate_findings(findings)

        if not materialized:
            return cls._EMPTY

        grouped = cls._signature_groups(materialized)

        return tuple(
            group[0]
            for group in grouped.values()
        )

    @classmethod
    def find_duplicates(
        cls,
        findings: Iterable[Finding],
    ) -> tuple[Finding, ...]:
        """
        Return only duplicate findings.

        The first occurrence of each signature is excluded.
        """
        materialized = cls._validate_findings(findings)

        if not materialized:
            return cls._EMPTY

        grouped = cls._signature_groups(materialized)

        duplicates: list[Finding] = []

        for group in grouped.values():
            if len(group) > 1:
                duplicates.extend(group[1:])

        return tuple(duplicates)

    @classmethod
    def group_duplicates(
        cls,
        findings: Iterable[Finding],
    ) -> dict[
        VulnerabilitySignature,
        tuple[Finding, ...],
    ]:
        """
        Group findings by VulnerabilitySignature.

        Every signature is represented exactly once.
        """
        materialized = cls._validate_findings(findings)

        if not materialized:
            return {}

        grouped = cls._signature_groups(materialized)

        return {
            signature: tuple(group)
            for signature, group in grouped.items()
        }

    @classmethod
    def merge_duplicates(
        cls,
        findings: Iterable[Finding],
    ) -> tuple[Finding, ...]:
        """
        Merge duplicate findings into canonical findings.

        Duplicate findings are merged using Finding.merge(),
        allowing the entity to determine how metadata such as
        confidence, ownership, verification status, and audit
        history should be preserved.

        Notes
        -----
        This method assumes Finding.merge() has been implemented.
        """
        materialized = cls._validate_findings(findings)

        if not materialized:
            return cls._EMPTY

        grouped = cls._signature_groups(materialized)

        merged: list[Finding] = []

        for group in grouped.values():

            canonical = group[0]

            for duplicate in group[1:]:
                canonical = canonical.merge(duplicate)

            merged.append(canonical)

        return tuple(merged)

    @classmethod
    def validate_correlation_group(
        cls,
        correlation_group: Iterable[Finding],
    ) -> bool:
        """
        Validate that a correlation group contains no duplicate
        Finding instances.

        Returns
        -------
        bool
            True if the group is valid, False otherwise.
        """
        if not isinstance(correlation_group, Iterable):
            raise DomainValidationError(
                "CorrelationGroup must be an iterable."
            )

        correlation_group = tuple(correlation_group)

        if len({id(finding) for finding in correlation_group}) != len(
            correlation_group
        ):
            raise DomainValidationError(
                "CorrelationGroup cannot contain duplicate Finding instances."
            )

        return True