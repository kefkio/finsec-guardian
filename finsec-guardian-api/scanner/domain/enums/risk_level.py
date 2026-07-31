from scanner.domain.enums.base import DomainEnum


class RiskLevel(DomainEnum):
    """
    Represents the overall risk posed by a security finding or
    an analyzed smart contract.

    Unlike Severity, RiskLevel is a composite assessment that may
    incorporate factors such as severity, confidence,
    exploitability, business impact, and environmental context.
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
        Numeric priority.

        Higher numbers represent higher overall risk.
        """
        return self._priority

    @property
    def is_high_risk(self) -> bool:
        """
        Returns True for High and Critical risk levels.
        """
        return (
            self is RiskLevel.HIGH
            or self is RiskLevel.CRITICAL
        )

    @property
    def requires_immediate_attention(self) -> bool:
        """
        Returns True if the risk level warrants immediate action.
        """
        return self is RiskLevel.CRITICAL

    @property
    def overall_risk(self) -> RiskLevel:
        """
        Returns the overall risk level, which is the same as the instance itself.
        This property is provided for semantic clarity in contexts where
        the overall risk level is being assessed.
        """
        if not self._findings:
            return RiskLevel.VERY_LOW
        return max(self._findings, key=lambda f: f.risk_level.priority).risk