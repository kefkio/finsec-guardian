from __future__ import annotations

import asyncio
from collections.abc import Sequence

from scanner.domain.entities import Finding
from scanner.domain.exceptions import DomainValidationError
from scanner.domain.ports.analyzer import AnalyzerPort
from scanner.domain.value_objects.analysis_request import AnalysisRequest
from scanner.services.analyzers.mythril import (
    MythrilAnalyzer as LegacyMythrilAnalyzer,
)

from .mythril_finding_mapper import MythrilFindingMapper


class MythrilAnalyzer(AnalyzerPort):
    """
    V2 adapter around the existing Mythril infrastructure.

    Mythril execution remains isolated in the legacy infrastructure
    implementation. This adapter translates the resulting issue payload
    into V2 domain Finding entities.
    """

    @property
    def name(self) -> str:
        return "mythril"

    async def analyze(
        self,
        request: AnalysisRequest,
    ) -> Sequence[Finding]:
        if not isinstance(request, AnalysisRequest):
            raise DomainValidationError(
                "request must be an AnalysisRequest."
            )

        result = await asyncio.to_thread(
            self._run_legacy_analyzer,
            request,
        )

        if not result.success:
            raise RuntimeError(
                result.error or "Mythril analysis failed."
            )

        issues = result.raw_output.get(
            "issues",
            [],
        )

        return MythrilFindingMapper.map_all(
            issues=issues,
            request=request,
        )

    @staticmethod
    def _run_legacy_analyzer(
        request: AnalysisRequest,
    ):
        analyzer = LegacyMythrilAnalyzer()

        return analyzer.analyze(
            source_code=request.source_code,
            contract_name=request.contract_name,
        )