"""
Defines the supported smart contract analyzers.

This module contains the AnalyzerType enumeration, representing
the static and dynamic analysis tools capable of producing
security findings within the FinSec Guardian platform.
"""

from __future__ import annotations

from .base import DomainEnum


class AnalyzerType(DomainEnum):
    """
    Represents the analyzer that produced a security finding.

    Using an enumeration ensures that every finding is associated
    with a recognised analysis engine, improving consistency,
    traceability, and reporting.
    """

    SLITHER = "slither"
    MYTHRIL = "mythril"
    ECHIDNA = "echidna"
    HEURISTIC = "heuristic"
    MANUAL = "manual"

    _PRIORITY = {
        "slither": 1,
        "mythril": 2,
        "echidna": 3,
        "heuristic": 4,
        "manual": 5,
    }

    @property
    def priority(self) -> int:
        """
        Returns the execution/reporting priority of the analyzer.

        Lower numbers indicate higher priority.
        """
        return self._PRIORITY[self.value]

    @property
    def is_static(self) -> bool:
        """
        Returns True if the analyzer performs static analysis.
        """
        return self in {
            AnalyzerType.SLITHER,
            AnalyzerType.HEURISTIC,
        }

    @property
    def is_dynamic(self) -> bool:
        """
        Returns True if the analyzer performs dynamic analysis.
        """
        return self in {
            AnalyzerType.MYTHRIL,
            AnalyzerType.ECHIDNA,
        }

    @property
    def is_manual(self) -> bool:
        """
        Returns True if the finding originated from manual review.
        """
        return self is AnalyzerType.MANUAL