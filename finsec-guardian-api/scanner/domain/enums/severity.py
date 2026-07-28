from scanner.domain.enums.base import DomainEnum


class Severity(DomainEnum):
    """
    Represents the severity level of a security finding.

    Severity reflects the potential impact of a vulnerability
    if it is successfully exploited.
    """

    CRITICAL = ("critical", 1)
    HIGH = ("high", 2)
    MEDIUM = ("medium", 3)
    LOW = ("low", 4)
    INFORMATIONAL = ("informational", 5)

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
        Numeric priority used for sorting.

        Lower numbers indicate higher severity.
        """
        return self._priority

    @property
    def is_high_risk(self) -> bool:
        """
        Returns True for Critical and High severity findings.
        """
        return (
            self is Severity.CRITICAL
            or self is Severity.HIGH
        )