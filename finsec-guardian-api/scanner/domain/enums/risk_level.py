from __future__ import annotations

from functools import total_ordering

from scanner.domain.enums.base import DomainEnum
from scanner.domain.enums.severity import Severity


@total_ordering
class RiskLevel(DomainEnum):
    """
    Represents the overall security risk posed by a vulnerability,
    scan, or assessed target.

    RiskLevel is distinct from Severity.

    Severity describes the technical impact of an individual finding,
    whereas RiskLevel represents the overall business risk after
    considering factors such as severity, confidence, exploitability,
    and environmental context.
    """

    VERY_LOW = ("very_low", 1)

    LOW = ("low", 2)

    MEDIUM = ("medium", 3)

    HIGH = ("high", 4)

    CRITICAL = ("critical", 5)

    def __new__(
        cls,
        value: str,
        priority: int,
    ):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj._priority = priority
        return obj

    @property
    def priority(self) -> int:
        """
        Numeric ordering priority.

        Larger values represent higher overall risk.
        """
        return self._priority

    @property
    def weight(self) -> int:
        """
        Alias for the numeric risk priority used by scoring heuristics.
        """
        return self.priority

    @classmethod
    def from_severity(cls, severity: Severity) -> "RiskLevel":
        """
        Map a technical severity to an overall business risk level.
        """
        mapping = {
            Severity.CRITICAL: cls.CRITICAL,
            Severity.HIGH: cls.HIGH,
            Severity.MEDIUM: cls.MEDIUM,
            Severity.LOW: cls.LOW,
            Severity.INFORMATIONAL: cls.VERY_LOW,
        }
        return mapping[severity]

    @property
    def is_low_risk(self) -> bool:
        """
        Returns True for VERY_LOW and LOW.
        """
        return self in (
            RiskLevel.VERY_LOW,
            RiskLevel.LOW,
        )

    @property
    def is_medium_risk(self) -> bool:
        """
        Returns True for MEDIUM.
        """
        return self is RiskLevel.MEDIUM

    @property
    def is_high_risk(self) -> bool:
        """
        Returns True for HIGH and CRITICAL.
        """
        return self in (
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        )

    @property
    def requires_immediate_attention(self) -> bool:
        """
        Returns True when remediation should begin immediately.
        """
        return self is RiskLevel.CRITICAL

    @property
    def is_deployment_blocking(self) -> bool:
        """
        Returns True if this risk level blocks deployment.
        """
        return self in (
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        )

    def __lt__(self, other: object) -> bool:
        """
        Enables natural ordering of RiskLevel values.
        """
        if not isinstance(other, RiskLevel):
            return NotImplemented

        return self.priority < other.priority