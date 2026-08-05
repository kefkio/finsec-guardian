from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from scanner.domain.entities import Finding
from scanner.domain.enums import AnalyzerType, Severity
from scanner.domain.exceptions import DomainValidationError


@dataclass(frozen=True, slots=True)
class CorrelationGroup:
    """
    Immutable Value Object representing a group of semantically
    related security findings.

    CorrelationGroup is produced by FindingCorrelationService and
    represents findings believed to belong to the same attack path,
    exploit chain, or security concern.
    """

    _MIN_SCORE: ClassVar[float] = 0.0
    _MAX_SCORE: ClassVar[float] = 1.0

    findings: tuple[Finding, ...]
    correlation_score: float
    reason: str

    def __post_init__(self) -> None:
        """
        Validate construction invariants.
        """

        object.__setattr__(
            self,
            "findings",
            tuple(self.findings),
        )

        if not self.findings:
            raise DomainValidationError(
                "CorrelationGroup must contain at least one Finding."
            )

        for index, finding in enumerate(self.findings):
            if not isinstance(finding, Finding):
                raise DomainValidationError(
                    f"Item {index} is not a Finding."
                )

        if len(set(self.findings)) != len(self.findings):
            raise DomainValidationError(
                "CorrelationGroup cannot contain duplicate Finding instances."
            )

        if (
            not isinstance(self.correlation_score, (int, float))
            or not (
                self._MIN_SCORE
                <= self.correlation_score
                <= self._MAX_SCORE
            )
        ):
            raise DomainValidationError(
                "correlation_score must be between 0.0 and 1.0."
            )

        if (
            not isinstance(self.reason, str)
            or not self.reason.strip()
        ):
            raise DomainValidationError(
                "reason must be a non-empty string."
            )

    # ==========================================================
    # Canonical Finding
    # ==========================================================

    @property
    def primary_finding(self) -> Finding:
        """
        Returns the canonical finding representing this group.
        """
        return self.findings[0]

    @property
    def identifier(self) -> str:
        """
        Stable identifier derived from the canonical finding.
        """
        return str(self.primary_finding.signature)

    # ==========================================================
    # Aggregate Information
    # ==========================================================

    @property
    def size(self) -> int:
        return len(self.findings)

    @property
    def contracts(self) -> frozenset[str]:
        return frozenset(
            finding.location.contract_name
            for finding in self.findings
            if getattr(
                finding.location,
                "contract_name",
                None,
            )
        )

    @property
    def files(self) -> frozenset[str]:
        return frozenset(
            finding.location.filename
            for finding in self.findings
        )

    @property
    def analyzers(self) -> frozenset[AnalyzerType]:
        return frozenset(
            finding.analyzer
            for finding in self.findings
        )

    @property
    def highest_severity(self) -> Severity:
        """
        Highest severity represented in this group.
        """
        return min(
            (
                finding.severity
                for finding in self.findings
            ),
            key=lambda severity: severity.priority,
        )

    @property
    def average_confidence(self) -> float:
        return round(
            sum(
                finding.confidence.weight
                for finding in self.findings
            )
            / len(self.findings),
            2,
        )

    @property
    def confidence(self) -> float:
        """
        Alias for average_confidence.
        """
        return self.average_confidence

    @property
    def consensus_score(self) -> float:
        """
        Measures analyzer consensus.

        1.0 means every finding came from a different analyzer.
        Lower values indicate repeated findings from fewer analyzers.
        """
        return round(
            len(self.analyzers) / len(self.findings),
            2,
        )

    # ==========================================================
    # Relationship Characteristics
    # ==========================================================

    @property
    def is_cross_analyzer(self) -> bool:
        return len(self.analyzers) > 1

    @property
    def is_cross_file(self) -> bool:
        return len(self.files) > 1

    @property
    def is_cross_contract(self) -> bool:
        return len(self.contracts) > 1

    # ==========================================================
    # Collection Behaviour
    # ==========================================================

    def __contains__(self, finding: Finding) -> bool:
        return finding in self.findings

    def __len__(self) -> int:
        return len(self.findings)

    def __iter__(self):
        return iter(self.findings)

    def __bool__(self) -> bool:
        return bool(self.findings)

    # ==========================================================
    # Ordering
    # ==========================================================

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, CorrelationGroup):
            return NotImplemented

        return (
            self.highest_severity.priority,
            -self.correlation_score,
            -self.size,
        ) > (
            other.highest_severity.priority,
            -other.correlation_score,
            -other.size,
        )