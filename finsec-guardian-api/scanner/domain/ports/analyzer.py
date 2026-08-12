from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from scanner.domain.entities import Finding
from scanner.domain.value_objects.analysis_request import AnalysisRequest


class AnalyzerPort(ABC):
    """
    Port defining the contract for security analysis engines.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique machine-readable identifier for the analyzer adapter.
        """
        ...

    @abstractmethod
    async def analyze(
        self,
        request: AnalysisRequest,
    ) -> Sequence[Finding]:
        """
        Asynchronously analyze the target request and return findings.
        """
        ...
