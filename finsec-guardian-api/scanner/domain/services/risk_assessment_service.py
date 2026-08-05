from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar

from scanner.domain.entities.finding import Finding
from scanner.domain.enums import RiskLevel, Severity
from scanner.domain.exceptions import DomainValidationError
from scanner.domain.value_objects.risk_summary import RiskSummary


class RiskAssessmentService:
    """
    Domain service responsible for assessing the security posture
    of a collection of Findings.

    Contains stateless domain logic for evaluating overall risk, deployment eligibility,
    severity distributions, and aggregate risk scores.
    """

    _RISK_MAP: ClassVar[tuple[tuple[Severity, RiskLevel], ...]] = (
        (Severity.CRITICAL, RiskLevel.CRITICAL),
        (Severity.HIGH, RiskLevel.HIGH),
        (Severity.MEDIUM, RiskLevel.MEDIUM),
    )

    _BLOCKING_RISKS: ClassVar[frozenset[RiskLevel]] = frozenset(
        {
            RiskLevel.CRITICAL,
            RiskLevel.HIGH,
        }
    )

    # ==========================================================
    # Public API
    # ==========================================================

    @classmethod
    def count_by_severity(
        cls,
        findings: Iterable[Finding],
        severity: Severity,
    ) -> int:
        """
        Count the number of findings having the specified severity.

        Raises:
            DomainValidationError: If severity is not a Severity or items are not Findings.
        """
        if not isinstance(severity, Severity):
            raise DomainValidationError(
                "Severity must be a valid Severity enum instance."
            )

        validated = cls._validate_findings(findings)
        return sum(finding.severity is severity for finding in validated)

    @classmethod
    def severity_distribution(
        cls,
        findings: Iterable[Finding],
    ) -> dict[Severity, int]:
        """
        Return the distribution of findings by severity.

        Every severity level is included, even if its count is zero.
        """
        validated = cls._validate_findings(findings)
        return cls._severity_distribution_from_validated(validated)

    @classmethod
    def overall_risk(
        cls,
        findings: Iterable[Finding],
    ) -> RiskLevel:
        """
        Determine overall risk represented by a collection of findings.
        The highest severity present determines the overall risk level.
        """
        validated = cls._validate_findings(findings)
        return cls._overall_risk_from_validated(validated)

    @classmethod
    def has_blocking_findings(
        cls,
        findings: Iterable[Finding],
    ) -> bool:
        """
        Determine whether findings contain deployment-blocking vulnerabilities.
        A finding is considered blocking if its overall risk matches the blocking policy.
        """
        validated = cls._validate_findings(findings)
        return cls._has_blocking_from_validated(validated)

    @classmethod
    def can_deploy(
        cls,
        findings: Iterable[Finding],
    ) -> bool:
        """Determine whether the target is eligible for deployment."""
        return not cls.has_blocking_findings(findings)

    @classmethod
    def weighted_risk_score(
        cls,
        findings: Iterable[Finding],
    ) -> float:
        """
        Calculate the aggregate weighted risk score for a collection of findings.

        NOTE: Uses Severity.weight as the canonical risk weighting.
        """
        validated = cls._validate_findings(findings)
        return sum(finding.severity.weight for finding in validated)

    @classmethod
    def average_confidence(
        cls,
        findings: Iterable[Finding],
    ) -> float:
        """Calculate the average confidence weight of all findings (0.0 to 1.0)."""
        validated = cls._validate_findings(findings)
        if not validated:
            return 0.0

        return sum(f.confidence.weight for f in validated) / len(validated)

    @classmethod
    def risk_summary(
        cls,
        findings: Iterable[Finding],
    ) -> RiskSummary:
        """
        Produce an immutable RiskSummary describing overall security posture.

        Materializes and validates the collection once, then performs a single
        aggregation pass to compute all risk metrics.
        """
        validated = cls._validate_findings(findings)
        distribution, weighted_score, total_confidence = cls._accumulate(validated)

        total_count = len(validated)
        avg_confidence = (total_confidence / total_count) if total_count > 0 else 0.0
        overall_risk = cls._risk_level_from_distribution(distribution)
        has_blocking = overall_risk in cls._BLOCKING_RISKS

        return RiskSummary(
            overall_risk=overall_risk,
            finding_count=total_count,
            critical=distribution[Severity.CRITICAL],
            high=distribution[Severity.HIGH],
            medium=distribution[Severity.MEDIUM],
            low=distribution[Severity.LOW],
            weighted_score=weighted_score,
            average_confidence=avg_confidence,
            has_blocking_findings=has_blocking,
            can_deploy=not has_blocking,
        )

    # ==========================================================
    # Internal Domain Helpers & Accumulators
    # ==========================================================

    @classmethod
    def _accumulate(
        cls,
        findings: tuple[Finding, ...],
    ) -> tuple[dict[Severity, int], float, float]:
        """Perform a single aggregation pass over pre-validated findings."""
        distribution = cls._empty_distribution()
        weighted_score = 0.0
        total_confidence = 0.0

        for finding in findings:
            distribution[finding.severity] += 1
            weighted_score += finding.severity.weight
            total_confidence += finding.confidence.weight

        return distribution, weighted_score, total_confidence

    @classmethod
    def _severity_distribution_from_validated(
        cls,
        findings: tuple[Finding, ...],
    ) -> dict[Severity, int]:
        distribution = cls._empty_distribution()
        for finding in findings:
            distribution[finding.severity] += 1
        return distribution

    @classmethod
    def _overall_risk_from_validated(
        cls,
        findings: tuple[Finding, ...],
    ) -> RiskLevel:
        distribution = cls._severity_distribution_from_validated(findings)
        return cls._risk_level_from_distribution(distribution)

    @classmethod
    def _has_blocking_from_validated(
        cls,
        findings: tuple[Finding, ...],
    ) -> bool:
        overall = cls._overall_risk_from_validated(findings)
        return overall in cls._BLOCKING_RISKS

    @staticmethod
    def _validate_findings(
        findings: Iterable[Finding],
    ) -> tuple[Finding, ...]:
        """
        Validate and materialize input findings into a concrete tuple.

        Materializing to a tuple prevents generator exhaustion bugs during multi-step evaluation.
        """
        if findings is None or isinstance(findings, (str, bytes)):
            raise DomainValidationError(
                "Findings must be an iterable of Finding objects."
            )

        try:
            materialized = tuple(findings)
        except TypeError:
            raise DomainValidationError(
                "Findings must be an iterable of Finding objects."
            )

        for finding in materialized:
            if not isinstance(finding, Finding):
                raise DomainValidationError(
                    f"All items must be Finding instances, got {type(finding).__name__}."
                )

        return materialized

    @staticmethod
    def _empty_distribution() -> dict[Severity, int]:
        return {severity: 0 for severity in Severity}

    @classmethod
    def _risk_level_from_distribution(
        cls,
        distribution: dict[Severity, int],
    ) -> RiskLevel:
        for severity, risk_level in cls._RISK_MAP:
            if distribution.get(severity, 0) > 0:
                return risk_level

        return RiskLevel.LOW