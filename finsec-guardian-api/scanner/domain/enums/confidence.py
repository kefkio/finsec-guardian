from scanner.domain.enums.base import DomainEnum


class Confidence(DomainEnum):
    """
    Represents the confidence level assigned to a security finding.

    Confidence reflects how certain an analyzer is that a reported
    issue is a true positive.

    It is independent of severity. For example, an analyzer may report
    a Critical issue with Low confidence if it cannot prove the finding
    conclusively.
    """

    HIGH = ("high", 1, 1.00)
    MEDIUM = ("medium", 2, 0.75)
    LOW = ("low", 3, 0.50)

    def __new__(
        cls,
        value: str,
        priority: int,
        weight: float,
    ):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj._priority = priority
        obj._weight = weight
        return obj

    @property
    def priority(self) -> int:
        """
        Numeric priority used for sorting.

        Lower numbers indicate higher confidence.
        """
        return self._priority

    @property
    def weight(self) -> float:
        """
        Returns the confidence weighting used during
        risk score calculation.

        The weight acts as a multiplier that adjusts the
        contribution of a finding to the overall risk score.
        """
        return self._weight

    @property
    def is_high_confidence(self) -> bool:
        """
        Returns True if this represents a high-confidence finding.
        """
        return self is Confidence.HIGH