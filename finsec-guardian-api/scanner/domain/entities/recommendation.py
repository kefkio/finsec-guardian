from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from scanner.domain.enums import (
    RecommendationPriority,
    RemediationEffort,
)
from scanner.domain.exceptions import DomainValidationError
from scanner.domain.value_objects import RecommendationTemplate


@dataclass(frozen=True, slots=True)
class Recommendation:
    """
    Immutable domain entity representing an actionable remediation
    recommendation generated from one or more security findings.
    """

    title: str
    description: str
    remediation: str

    priority: RecommendationPriority
    effort: RemediationEffort

    cwe: str | None = None
    swc: str | None = None
    owasp: str | None = None

    references: tuple[str, ...] = ()

    requires_manual_review: bool = False

    def __post_init__(self) -> None:
        # Standardize and validate required string fields
        self._validate_and_strip("title", self.title)
        self._validate_and_strip("description", self.description)
        self._validate_and_strip("remediation", self.remediation)

        if not isinstance(self.priority, RecommendationPriority):
            raise DomainValidationError(
                "priority must be a RecommendationPriority."
            )

        if not isinstance(self.effort, RemediationEffort):
            raise DomainValidationError(
                "effort must be a RemediationEffort."
            )

        if not isinstance(self.requires_manual_review, bool):
            raise DomainValidationError(
                "requires_manual_review must be a boolean."
            )

        # Handle reference collection normalization
        if isinstance(self.references, (list, set)):
            object.__setattr__(self, "references", tuple(self.references))
        elif not isinstance(self.references, tuple):
            raise DomainValidationError(
                "references must be a tuple or compatible iterable."
            )

        for ref in self.references:
            self._validate_non_empty(ref, "reference")

        # Normalize optional identifiers (empty strings -> None)
        self._normalize_optional_identifier("cwe", self.cwe)
        self._normalize_optional_identifier("swc", self.swc)
        self._normalize_optional_identifier("owasp", self.owasp)

    @classmethod
    def from_template(
        cls,
        template: RecommendationTemplate,
    ) -> Recommendation:
        """
        Factory for constructing a Recommendation from an immutable
        RecommendationTemplate.
        """
        return cls(
            title=template.title,
            description=template.description,
            remediation=template.remediation,
            priority=template.priority,
            effort=template.effort,
            cwe=template.cwe,
            swc=template.swc,
            owasp=template.owasp,
            references=template.references,
            requires_manual_review=template.requires_manual_review,
        )

    def _validate_and_strip(self, field_name: str, value: str) -> None:
        """Validates that a required string field is non-empty and strips whitespace."""
        self._validate_non_empty(value, field_name)
        object.__setattr__(self, field_name, value.strip())

    def _normalize_optional_identifier(
        self, field_name: str, value: str | None
    ) -> None:
        """Strips whitespace from optional identifiers, setting blank strings to None."""
        if value is None:
            return

        if not isinstance(value, str):
            raise DomainValidationError(
                f"{field_name} must be a string or None."
            )

        stripped = value.strip()
        object.__setattr__(self, field_name, stripped if stripped else None)

    @staticmethod
    def _validate_non_empty(
        value: str,
        field_name: str,
    ) -> None:
        if not isinstance(value, str):
            raise DomainValidationError(
                f"{field_name} must be a string."
            )

        if not value.strip():
            raise DomainValidationError(
                f"{field_name} cannot be empty."
            )

    @property
    def has_cwe(self) -> bool:
        return bool(self.cwe)

    @property
    def has_swc(self) -> bool:
        return bool(self.swc)

    @property
    def has_owasp(self) -> bool:
        return bool(self.owasp)

    @property
    def has_references(self) -> bool:
        return bool(self.references)

    @property
    def has_external_classification(self) -> bool:
        return self.has_cwe or self.has_swc or self.has_owasp

    @property
    def classification_count(self) -> int:
        return sum(
            (
                self.has_cwe,
                self.has_swc,
                self.has_owasp,
            )
        )

    @property
    def is_immediate(self) -> bool:
        return self.priority is RecommendationPriority.HIGH

    @property
    def requires_manual_intervention(self) -> bool:
        return self.requires_manual_review