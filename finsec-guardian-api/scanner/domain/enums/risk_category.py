from __future__ import annotations

from scanner.domain.enums.base import DomainEnum


class RiskCategory(DomainEnum):
    """High-level risk categories used for dashboards and reporting."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    STORAGE = "storage"
    ARITHMETIC = "arithmetic"
    RANDOMNESS = "randomness"
    LOGIC = "logic"
    GAS = "gas"
    STYLE = "style"
    OTHER = "other"
