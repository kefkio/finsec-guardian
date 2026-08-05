from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from scanner.domain.enums import RiskLevel, Severity
from scanner.domain.exceptions import DomainValidationError


@dataclass(frozen=True, slots=True)
class RiskSummary:
    """
    Immutable Value Object representing the aggregate security posture
    of a completed scan.

    RiskSummary is produced exclusively by RiskAssessmentService and
    captures the distribution of findings, the overall risk level,
    deployment readiness, and aggregate metrics used by reporting and
    decision-making components.

    Because it is a Value Object, equality is determined solely by its
    attributes rather than by identity.
    """

    _MAX_SEVERITY_WEIGHT: ClassVar[int] = Severity.CRITICAL.weight

    overall_risk: RiskLevel

    finding_count: int

    critical: int
    high: int
    medium: int
    low: int
    informational: int = 0

    weighted_score: float = 0.0

    average_confidence: float = 0.0

    has_blocking_findings: bool = False

    def __post_init__(self) -> None:
        """
        Validate construction invariants.
        """

        if not isinstance(self.overall_risk, RiskLevel):
            raise DomainValidationError(
                "overall_risk must be a RiskLevel instance."
            )

        if not isinstance(self.has_blocking_findings, bool):
            raise DomainValidationError(
                "has_blocking_findings must be a boolean."
            )

        count_fields = (
            ("finding_count", self.finding_count),
            ("critical", self.critical),
            ("high", self.high),
            ("medium", self.medium),
            ("low", self.low),
            ("informational", self.informational),
        )

        for name, value in count_fields:

            if not isinstance(value, int) or isinstance(value, bool):
                raise DomainValidationError(
                    f"{name} must be an integer."
                )

            if value < 0:
                raise DomainValidationError(
                    f"{name} cannot be negative."
                )

        if (
            not isinstance(self.weighted_score, (int, float))
            or self.weighted_score < 0
        ):
            raise DomainValidationError(
                "weighted_score must be a non-negative number."
            )

        if (
            not isinstance(self.average_confidence, (int, float))
            or not (0.0 <= self.average_confidence <= 1.0)
        ):
            raise DomainValidationError(
                "average_confidence must be between 0.0 and 1.0."
            )

        total = (
            self.critical
            + self.high
            + self.medium
            + self.low
            + self.informational
        )

        if total != self.finding_count:
            raise DomainValidationError(
                f"finding_count ({self.finding_count}) "
                f"does not equal the total severity count ({total})."
            )

        # ------------------------------------------------------
        # Validate overall risk consistency
        # ------------------------------------------------------

        expected_risk = (
            RiskLevel.VERY_LOW
            if self.finding_count == 0
            else RiskLevel.LOW
        )

        if self.critical > 0:
            expected_risk = RiskLevel.CRITICAL
        elif self.high > 0:
            expected_risk = RiskLevel.HIGH
        elif self.medium > 0:
            expected_risk = RiskLevel.MEDIUM

        if self.overall_risk != expected_risk:
            raise DomainValidationError(
                "overall_risk is inconsistent with the "
                "supplied severity distribution."
            )

        # ------------------------------------------------------
        # Validate deployment blocking consistency
        # ------------------------------------------------------

        expected_blocking = (
            self.critical > 0
            or self.high > 0
        )

        if self.has_blocking_findings != expected_blocking:
            raise DomainValidationError(
                "has_blocking_findings is inconsistent with "
                "the supplied severity distribution."
            )

    # ==========================================================
    # Derived Properties
    # ==========================================================

    @property
    def can_deploy(self) -> bool:
        """
        Returns True when the assessed risk permits deployment.
        """
        return not self.has_blocking_findings

    @property
    def has_findings(self) -> bool:
        """
        Returns True if any findings exist.
        """
        return self.finding_count > 0

    @property
    def has_critical_findings(self) -> bool:
        return self.critical > 0

    @property
    def has_high_findings(self) -> bool:
        return self.high > 0

    @property
    def has_medium_findings(self) -> bool:
        return self.medium > 0

    @property
    def has_low_findings(self) -> bool:
        return self.low > 0

    @property
    def has_informational_findings(self) -> bool:
        return self.informational > 0

    @property
    def is_clean(self) -> bool:
        """
        Returns True when no findings were detected.
        """
        return self.finding_count == 0

    @property
    def is_high_risk(self) -> bool:
        """
        Returns True if the overall risk is HIGH or CRITICAL.
        """
        return self.overall_risk.is_high_risk

    @property
    def risk_percentage(self) -> float:
        """
        Returns the normalized risk percentage.

        The percentage is calculated relative to the theoretical
        maximum weighted score (all findings being CRITICAL).

        The result is defensively capped at 100%.
        """
        if self.finding_count == 0:
            return 0.0

        maximum = (
            self.finding_count
            * self._MAX_SEVERITY_WEIGHT
        )

        percentage = (
            self.weighted_score / maximum
        ) * 100

        return round(
            min(percentage, 100.0),
            2,
        )

    @property
    def severity_distribution(self) -> dict[Severity, int]:
        """
        Returns the severity distribution.
        """
        return {
            Severity.CRITICAL: self.critical,
            Severity.HIGH: self.high,
            Severity.MEDIUM: self.medium,
            Severity.LOW: self.low,
            Severity.INFORMATIONAL: self.informational,
        }

    @property
    def average_weight(self) -> float:
        if self.finding_count == 0:
            return 0.0

        return round(
            self.weighted_score / self.finding_count,
            2,
        )

    def __bool__(self) -> bool:
        """
        Truthiness indicates whether any findings exist.
        """
        return self.has_findings