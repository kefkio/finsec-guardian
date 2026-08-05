from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Callable, ClassVar

from scanner.domain.entities import Entity
from scanner.domain.enums import (
    AnalyzerType,
    Confidence,
    RiskLevel,
    Severity,
)
from scanner.domain.enums.base import DomainEnum
from scanner.domain.exceptions import DomainValidationError
from scanner.domain.value_objects.source_location import SourceLocation
from scanner.domain.value_objects.vulnerability_signature import (
    VulnerabilitySignature,
)


def _utc_now() -> datetime:
    """
    Returns the current UTC timestamp.

    The clock is injectable to make the domain deterministic during
    testing.
    """
    return datetime.now(UTC)


class FindingStatus(DomainEnum):
    """
    Represents the lifecycle state of a Finding.
    """

    NEW = "new"

    CONFIRMED = "confirmed"

    FALSE_POSITIVE = "false_positive"

    SUPPRESSED = "suppressed"

    RESOLVED = "resolved"

    @property
    def is_open(self) -> bool:
        return self in (
            FindingStatus.NEW,
            FindingStatus.CONFIRMED,
        )

    @property
    def is_closed(self) -> bool:
        return not self.is_open


@dataclass(
    slots=True,
    kw_only=True,
    eq=False,
)
class Finding(Entity):
    """
    Represents a vulnerability discovered during smart contract analysis.

    A Finding is a rich Domain Entity.

    Identity is independent of attribute values and the entity may evolve
    during its lifecycle through verification, assignment, suppression,
    confirmation and resolution.

    Business invariants are enforced immediately during construction.
    """

    # ==========================================================
    # Vulnerability Metadata
    # ==========================================================

    title: str

    description: str

    recommendation: str

    # ==========================================================
    # Classification
    # ==========================================================

    severity: Severity

    confidence: Confidence

    risk_level: RiskLevel

    # ==========================================================
    # Analyzer Metadata
    # ==========================================================

    analyzer: AnalyzerType

    # ==========================================================
    # Location
    # ==========================================================

    location: SourceLocation

    signature: VulnerabilitySignature

    # ==========================================================
    # Classification Standards
    # ==========================================================

    cwe_id: str | None = None

    swc_id: str | None = None

    owasp_category: str | None = None

    cvss_score: float | None = None

    # ==========================================================
    # Workflow
    # ==========================================================

    status: FindingStatus = FindingStatus.NEW

    assigned_to: str | None = None

    verified_by: str | None = None

    resolved_by: str | None = None

    # ==========================================================
    # Audit Metadata
    # ==========================================================

    created_at: datetime = field(
        default_factory=_utc_now,
    )

    updated_at: datetime = field(
        default_factory=_utc_now,
    )

    closed_at: datetime | None = None

    clock: Callable[[], datetime] = field(
        default=_utc_now,
        repr=False,
        compare=False,
    )

    # ==========================================================
    # Class Constants
    # ==========================================================

    _STALE_AFTER_DAYS: ClassVar[int] = 30

    def __post_init__(self) -> None:
        """
        Validate the entity immediately after creation.
        """
        self._validate_text_fields()
        self._validate_types()
        self._validate_business_rules()

    # ==========================================================
    # Validation
    # ==========================================================

    def _validate_text_fields(self) -> None:
        """
        Validate all textual fields.
        """
        fields = {
            "Title": self.title,
            "Description": self.description,
            "Recommendation": self.recommendation,
        }

        for name, value in fields.items():

            if not isinstance(value, str):
                raise DomainValidationError(
                    f"{name} must be a string."
                )

            if not value.strip():
                raise DomainValidationError(
                    f"{name} cannot be empty."
                )

        if len(self.title) > 200:
            raise DomainValidationError(
                "Title cannot exceed 200 characters."
            )

    def _validate_types(self) -> None:
        """
        Validate all enum and value-object fields.
        """
        validations = (
            (self.severity, Severity, "severity"),
            (self.confidence, Confidence, "confidence"),
            (self.risk_level, RiskLevel, "risk level"),
            (self.analyzer, AnalyzerType, "analyzer"),
            (self.location, SourceLocation, "source location"),
            (
                self.signature,
                VulnerabilitySignature,
                "vulnerability signature",
            ),
            (self.status, FindingStatus, "finding status"),
        )

        for value, expected_type, name in validations:
            if not isinstance(value, expected_type):
                raise DomainValidationError(
                    f"Invalid {name}."
                )

    def _validate_business_rules(self) -> None:
        """
        Validate business invariants.
        """

        if (
            self.severity is Severity.CRITICAL
            and self.risk_level is not RiskLevel.CRITICAL
        ):
            raise DomainValidationError(
                "Critical findings must have a critical risk level."
            )

        if (
            self.severity is Severity.HIGH
            and self.risk_level.priority < RiskLevel.HIGH.priority
        ):
            raise DomainValidationError(
                "High severity findings cannot have a lower risk level."
            )

        if self.cvss_score is not None:

            if not (0.0 <= self.cvss_score <= 10.0):
                raise DomainValidationError(
                    "CVSS score must be between 0.0 and 10.0."
                )

    # ==========================================================
    # Internal Helpers
    # ==========================================================

    def _touch(self) -> None:
        """
        Updates the modification timestamp.
        """
        self.updated_at = self.clock()


    # ==========================================================
    # Identity
    # ==========================================================

    @property
    def fingerprint(self) -> str:
        """
        Returns the canonical fingerprint used to uniquely
        identify this finding.
        """
        return self.signature.value

    # ==========================================================
    # Presentation
    # ==========================================================

    @property
    def summary(self) -> str:
        """
        Returns a concise human-readable summary.
        """
        return (
            f"[{self.severity.display_name}] "
            f"{self.title} "
            f"({self.location})"
        )

    # ==========================================================
    # Lifecycle Operations
    # ==========================================================

    def assign_to(self, assignee: str) -> None:
        """
        Assign the finding to a user.

        Raises:
            DomainValidationError:
                If the finding has already been closed or the assignee
                is invalid.
        """
        if self.status.is_closed:
            raise DomainValidationError(
                "Closed findings cannot be reassigned."
            )

        if not isinstance(assignee, str) or not assignee.strip():
            raise DomainValidationError(
                "Assignee cannot be empty."
            )

        self.assigned_to = assignee.strip()
        self._touch()

    def confirm(self) -> None:
        """
        Marks the finding as confirmed.

        Raises:
            DomainValidationError:
                If the finding is not NEW.
        """
        if self.status is not FindingStatus.NEW:
            raise DomainValidationError(
                "Only new findings may be confirmed."
            )

        self.status = FindingStatus.CONFIRMED
        self._touch()

    def verify(self, verifier: str) -> None:
        """
        Records verification of the finding.

        Verification is only permitted while the finding
        remains open.

        Raises:
            DomainValidationError:
                If the finding is closed or the verifier
                is invalid.
        """
        if self.status.is_closed:
            raise DomainValidationError(
                "Closed findings cannot be verified."
            )

        if not isinstance(verifier, str) or not verifier.strip():
            raise DomainValidationError(
                "Verifier cannot be empty."
            )

        self.verified_by = verifier.strip()
        self._touch()

    def suppress(self) -> None:
        """
        Suppresses the finding.

        A suppressed finding is intentionally ignored,
        typically because it is an accepted risk.

        Raises:
            DomainValidationError:
                If the finding is already closed.
        """
        if self.status.is_closed:
            raise DomainValidationError(
                "Finding has already been closed."
            )

        self.status = FindingStatus.SUPPRESSED
        self._close()

    def mark_false_positive(self) -> None:
        """
        Marks the finding as a false positive.

        Raises:
            DomainValidationError:
                If the finding has already been closed.
        """
        if self.status.is_closed:
            raise DomainValidationError(
                "Finding has already been closed."
            )

        self.status = FindingStatus.FALSE_POSITIVE
        self._close()

    def resolve(self, resolver: str) -> None:
        """
        Resolves the finding.

        Raises:
            DomainValidationError:
                If the finding has already been closed or
                the resolver is invalid.
        """
        if self.status.is_closed:
            raise DomainValidationError(
                "Finding has already been closed."
            )

        if not isinstance(resolver, str) or not resolver.strip():
            raise DomainValidationError(
                "Resolver cannot be empty."
            )

        self.resolved_by = resolver.strip()
        self.status = FindingStatus.RESOLVED
        self._close()

    # ==========================================================
    # Query Properties
    # ==========================================================

    @property
    def is_new(self) -> bool:
        """Returns True if the finding has not yet been triaged."""
        return self.status is FindingStatus.NEW

    @property
    def is_confirmed(self) -> bool:
        """Returns True if the finding has been confirmed."""
        return self.status is FindingStatus.CONFIRMED

    @property
    def is_open(self) -> bool:
        """Returns True if the finding remains active."""
        return self.status.is_open

    @property
    def is_closed(self) -> bool:
        """Returns True if the finding has been closed."""
        return self.status.is_closed

    @property
    def is_resolved(self) -> bool:
        """Returns True if the finding has been resolved."""
        return self.status is FindingStatus.RESOLVED

    @property
    def age(self) -> timedelta:
        """
        Returns how long the finding has existed.

        For closed findings this is the time from creation until closure.
        For open findings it is the current elapsed time.
        """
        end = self.closed_at or self.clock()
        return end - self.created_at

    @property
    def days_open(self) -> int:
        """
        Returns the age of the finding in whole days.
        """
        return self.age.days

    @property
    def is_stale(self) -> bool:
        """
        Returns True if the finding has remained open longer than the
        configured threshold.
        """
        return (
            self.is_open
            and self.days_open >= self._STALE_AFTER_DAYS
        )


    @property
    def display_name(self) -> str:
        """
        Friendly display name.
        """
        return self.title

    # ==========================================================
    # Equality Helpers
    # ==========================================================

    def matches(self, other: Finding) -> bool:
        """
        Returns True if two findings represent the same vulnerability.

        Equality is determined by their vulnerability signature.
        """
        if not isinstance(other, Finding):
            return False

        return self.signature == other.signature

    def same_location(self, other: Finding) -> bool:
        """
        Returns True if two findings refer to the same source location.
        """
        if not isinstance(other, Finding):
            return False

        return self.location == other.location

    def same_analyzer(self, other: Finding) -> bool:
        """
        Returns True if two findings were produced by the same analyzer.
        """
        if not isinstance(other, Finding):
            return False

        return self.analyzer is other.analyzer

    # ==========================================================
    # Internal Helpers
    # ==========================================================


    def _close(self) -> None:
        """
        Closes the finding and records the closure timestamp.
        """
        self.closed_at = self.clock()
        self._touch()

    def merge(self, other: Finding) -> None:
        """
        Merges another finding into this one.

        The merge operation updates the current finding's attributes
        with the most recent information from the other finding.

        Raises:
            DomainValidationError:
                If the findings do not represent the same vulnerability.
        """
        if not self.matches(other):
            raise DomainValidationError(
                "Cannot merge findings with different signatures."
            )

        # Update attributes with the most recent information
        if other.updated_at > self.updated_at:
            self.title = other.title
            self.description = other.description
            self.recommendation = other.recommendation
            self.severity = other.severity
            self.confidence = other.confidence
            self.risk_level = other.risk_level
            self.analyzer = other.analyzer
            self.location = other.location
            self.signature = other.signature
            self.status = other.status
            self.assigned_to = other.assigned_to
            self.verified_by = other.verified_by
            self.resolved_by = other.resolved_by
            self.created_at = min(self.created_at, other.created_at)
            self.updated_at = max(self.updated_at, other.updated_at)
            if other.closed_at is not None:
                self.closed_at = max(
                    filter(None, [self.closed_at, other.closed_at])
                )