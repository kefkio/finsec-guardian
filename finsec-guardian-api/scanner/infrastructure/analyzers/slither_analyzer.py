from __future__ import annotations

import asyncio
from collections.abc import Sequence

from scanner.domain.entities import Finding
from scanner.domain.ports.analyzer import AnalyzerPort
from scanner.domain.value_objects.analysis_request import AnalysisRequest
from scanner.services.analyzers.slither import (
    SlitherAnalyzer as LegacySlitherAnalyzer,
)

from .slither_finding_mapper import SlitherFindingMapper


class SlitherAnalyzer(AnalyzerPort):
    """V2 adapter around the existing Slither infrastructure."""

    @property
    def name(self) -> str:
        return "slither"

    async def analyze(
        self,
        request: AnalysisRequest,
    ) -> Sequence[Finding]:
        if not isinstance(request, AnalysisRequest):
            raise TypeError(
                "request must be an AnalysisRequest."
            )

        result = await asyncio.to_thread(
            self._run_legacy_analyzer,
            request,
        )

        detectors = result.raw_output.get("detectors", [])

        return SlitherFindingMapper.map_all(
            detectors=detectors,
            request=request,
        )

    @staticmethod
    def _run_legacy_analyzer(
        request: AnalysisRequest,
    ):
        analyzer = LegacySlitherAnalyzer()

        return analyzer.analyze(
            source_code=request.source_code,
            contract_name=request.contract_name,
        )