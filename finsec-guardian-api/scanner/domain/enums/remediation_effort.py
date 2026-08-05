"""
Defines remediation effort estimates.

RemediationEffort represents the estimated engineering effort
required to implement a remediation recommendation.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from .base import DomainEnum


class RemediationEffort(DomainEnum):
    """
    Relative engineering effort required to implement
    a recommendation.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @property
    def weight(self) -> int:
        """
        Numeric effort used for deterministic comparisons.

        Higher values indicate greater implementation effort.
        """
        return _EFFORT_WEIGHTS[self]

    @property
    def is_quick_win(self) -> bool:
        """
        Returns True when the recommendation is inexpensive
        to implement.
        """
        return self is RemediationEffort.LOW

    @property
    def is_medium_effort(self) -> bool:
        """Returns True for medium implementation effort."""
        return self is RemediationEffort.MEDIUM

    @property
    def is_high_effort(self) -> bool:
        """Returns True for high implementation effort."""
        return self is RemediationEffort.HIGH

    @property
    def display_name(self) -> str:
        """Human-readable representation."""
        return self.value.title()


# ==========================================================
# Immutable Effort Metadata
# ==========================================================

_EFFORT_WEIGHTS: Mapping[RemediationEffort, int] = MappingProxyType(
    {
        RemediationEffort.LOW: 1,
        RemediationEffort.MEDIUM: 2,
        RemediationEffort.HIGH: 3,
    }
)