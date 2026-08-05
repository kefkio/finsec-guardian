from __future__ import annotations

from dataclasses import dataclass

from scanner.domain.enums import (
    RecommendationPriority,
    RemediationEffort,
)
from scanner.domain.exceptions import DomainValidationError


@dataclass(frozen=True, slots=True)
class RecommendationTemplate:
    """
    Immutable Value Object representing the canonical remediation
    knowledge associated with a vulnerability type.

    RecommendationTemplate forms part of the domain knowledge base and
    is consumed by RecommendationService when constructing
    Recommendations from Findings.

    It intentionally contains no runtime scan data.
    """

    identifier: str
    title: str
    description: str
    remediation: str

    priority: RecommendationPriority
    effort: RemediationEffort

    cwe: str | None = None
    swc: str | None = None
    owasp: str | None = None

    references: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()

    requires_manual_review: bool = False
    automation_available: bool = False
    estimated_fix_hours: float | None = None

    def __post_init__(self) -> None:
        """
        Validate construction invariants and normalize fields.
        """
        self._validate_and_strip("identifier", self.identifier)
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

        # Normalize collection parameters
        if isinstance(self.references, (list, set)):
            object.__setattr__(self, "references", tuple(self.references))
        elif not isinstance(self.references, tuple):
            raise DomainValidationError(
                "references must be a tuple or compatible iterable."
            )

        if isinstance(self.tags, (list, set)):
            object.__setattr__(self, "tags", tuple(self.tags))
        elif not isinstance(self.tags, tuple):
            raise DomainValidationError(
                "tags must be a tuple or compatible iterable."
            )

        if not isinstance(self.requires_manual_review, bool):
            raise DomainValidationError(
                "requires_manual_review must be a boolean."
            )

        if not isinstance(self.automation_available, bool):
            raise DomainValidationError(
                "automation_available must be a boolean."
            )

        if (
            self.estimated_fix_hours is not None
            and not isinstance(
                self.estimated_fix_hours,
                (int, float),
            )
        ):
            raise DomainValidationError(
                "estimated_fix_hours must be numeric."
            )

        if (
            self.estimated_fix_hours is not None
            and self.estimated_fix_hours < 0
        ):
            raise DomainValidationError(
                "estimated_fix_hours cannot be negative."
            )

        for reference in self.references:
            self._validate_non_empty(reference, "reference")

        for tag in self.tags:
            self._validate_non_empty(tag, "tag")

        # Normalize optional classifications
        self._normalize_optional_identifier("cwe", self.cwe)
        self._normalize_optional_identifier("swc", self.swc)
        self._normalize_optional_identifier("owasp", self.owasp)

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
        """Validate that a string value is non-empty."""
        if not isinstance(value, str):
            raise DomainValidationError(
                f"{field_name} must be a string."
            )

        if not value.strip():
            raise DomainValidationError(
                f"{field_name} cannot be empty."
            )

    # ==========================================================
    # Derived Properties
    # ==========================================================

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
    def has_tags(self) -> bool:
        return bool(self.tags)

    @property
    def has_estimated_fix_time(self) -> bool:
        return self.estimated_fix_hours is not None

    @property
    def is_automatable(self) -> bool:
        return self.automation_available

    @property
    def requires_manual_intervention(self) -> bool:
        """
        Returns True when remediation cannot be fully automated.
        """
        return (
            self.requires_manual_review
            or not self.automation_available
        )

    @property
    def classification_count(self) -> int:
        """
        Returns the number of security classification systems
        associated with this recommendation.
        """
        return sum(
            (
                self.has_cwe,
                self.has_swc,
                self.has_owasp,
            )
        )