from __future__ import annotations

from scanner.domain.enums.base import DomainEnum


class Severity(DomainEnum):
    """
    Represents the impact of a security finding.

    Severity describes the potential damage a vulnerability could cause
    if exploited. It is independent of confidence, which expresses how
    certain an analyzer is that the finding is a true positive.
    """

    # Type annotations for static analyzers (Pylance, Pyright, mypy)
    _priority: int
    _weight: int

    CRITICAL = ("critical", 1, 5)
    HIGH = ("high", 2, 4)
    MEDIUM = ("medium", 3, 3)
    LOW = ("low", 4, 2)
    INFORMATIONAL = ("informational", 5, 1)

    def __new__(
        cls,
        value: str,
        priority: int,
        weight: int,
    ):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj._priority = priority
        obj._weight = weight
        return obj

    @property
    def priority(self) -> int:
        """
        Numeric ordering of severity.

        Lower values represent more severe findings.
        """
        return self._priority

    @property
    def weight(self) -> int:
        """
        Relative contribution of this severity to the aggregate
        risk score.
        """
        return self._weight

    @property
    def is_blocking(self) -> bool:
        """
        Returns True if this severity should block deployment.
        """
        return self in (
            Severity.CRITICAL,
            Severity.HIGH,
        )

    @property
    def is_high_risk(self) -> bool:
        """
        Returns True for HIGH and CRITICAL severities.
        """
        return self.is_blocking