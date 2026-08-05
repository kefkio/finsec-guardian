"""
Defines recommendation priority levels.

RecommendationPriority represents the urgency with which a remediation
recommendation should be addressed.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from .base import DomainEnum


class RecommendationPriority(DomainEnum):
    """
    Priority assigned to a remediation recommendation.
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @property
    def weight(self) -> int:
        """
        Numeric priority used for deterministic sorting.

        Higher values indicate higher priority.
        """
        return _PRIORITY_WEIGHTS[self]

    @property
    def is_high(self) -> bool:
        """Returns True for high-priority recommendations."""
        return self is RecommendationPriority.HIGH

    @property
    def is_medium(self) -> bool:
        """Returns True for medium-priority recommendations."""
        return self is RecommendationPriority.MEDIUM

    @property
    def is_low(self) -> bool:
        """Returns True for low-priority recommendations."""
        return self is RecommendationPriority.LOW

    @property
    def display_name(self) -> str:
        """Human-readable representation."""
        return self.value.title()


# ==========================================================
# Immutable Priority Metadata
# ==========================================================

_PRIORITY_WEIGHTS: Mapping[RecommendationPriority, int] = MappingProxyType(
    {
        RecommendationPriority.HIGH: 3,
        RecommendationPriority.MEDIUM: 2,
        RecommendationPriority.LOW: 1,
    }
)