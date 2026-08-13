from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from scanner.application.services.scan_pipeline import ScanPipeline
from scanner.domain.entities.finding import Finding
from scanner.domain.enums import (
    AnalyzerType,
    Confidence,
    RiskLevel,
    ScanStatus,
    Severity,
)
from scanner.domain.ports.analyzer import AnalyzerPort
from scanner.domain.ports.scan_repository import ScanRepository
from scanner.domain.value_objects.analysis_request import AnalysisRequest
from scanner.domain.value_objects.source_location import SourceLocation
from scanner.domain.value_objects.vulnerability_signature import (
    VulnerabilitySignature,
)


@pytest.fixture
def analysis_request() -> AnalysisRequest:
    return AnalysisRequest(
        source_code="contract VulnerableBank {}",
        contract_name="VulnerableBank",
        source_filename="VulnerableBank.sol",
        solidity_version="0.8.20",
    )


@pytest.fixture
def finding() -> Finding:
    return Finding(
        title="Reentrancy",
        description="Potential reentrancy vulnerability.",
        recommendation="Apply checks-effects-interactions.",
        severity=Severity.HIGH,
        confidence=Confidence.HIGH,
        risk_level=RiskLevel.HIGH,
        analyzer=AnalyzerType.SLITHER,
        location=SourceLocation(
            filename="VulnerableBank.sol",
            line=10,
            column=5,
            end_line=14,
            end_column=22,
        ),
        signature=VulnerabilitySignature("b" * 64),
        swc_id="SWC-107",
    )


@pytest.fixture
def analyzer() -> AsyncMock:
    return AsyncMock(spec=AnalyzerPort)


@pytest.fixture
def repository() -> MagicMock:
    return MagicMock(spec=ScanRepository)


@pytest.fixture
def pipeline(
    analyzer: AsyncMock,
    repository: MagicMock,
) -> ScanPipeline:
    return ScanPipeline(
        analyzer=analyzer,
        repository=repository,
    )


class TestScanPipeline:

    @pytest.mark.asyncio
    async def test_execute_returns_completed_scan(
        self,
        pipeline: ScanPipeline,
        analyzer: AsyncMock,
        repository: MagicMock,
        analysis_request: AnalysisRequest,
    ) -> None:
        analyzer.analyze.return_value = ()

        scan = await pipeline.execute(
            analysis_request,
        )

        assert scan.status is ScanStatus.COMPLETED
        assert scan.smart_contract.filename == "VulnerableBank.sol"
        assert scan.smart_contract.contract_name == "VulnerableBank"
        assert scan.smart_contract.source_code == (
            "contract VulnerableBank {}"
        )

        analyzer.analyze.assert_awaited_once_with(
            analysis_request,
        )

        assert repository.save.call_count == 1
        assert repository.update.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_merges_analyzer_findings(
        self,
        pipeline: ScanPipeline,
        analyzer: AsyncMock,
        analysis_request: AnalysisRequest,
        finding: Finding,
    ) -> None:
        analyzer.analyze.return_value = (finding,)

        scan = await pipeline.execute(
            analysis_request,
        )

        assert scan.status is ScanStatus.COMPLETED
        assert scan.finding_count == 1
        assert scan.findings[0] is finding

    @pytest.mark.asyncio
    async def test_execute_persists_lifecycle_transitions(
        self,
        pipeline: ScanPipeline,
        analyzer: AsyncMock,
        repository: MagicMock,
        analysis_request: AnalysisRequest,
    ) -> None:
        analyzer.analyze.return_value = ()

        persisted_statuses: list[ScanStatus] = []

        def capture_update(scan) -> None:
            persisted_statuses.append(scan.status)

        repository.update.side_effect = capture_update

        await pipeline.execute(
            analysis_request,
        )

        assert repository.save.call_count == 1
        assert repository.update.call_count == 2

        assert persisted_statuses == [
            ScanStatus.RUNNING,
            ScanStatus.COMPLETED,
        ]

    @pytest.mark.asyncio
    async def test_execute_marks_scan_failed_when_analyzer_fails(
        self,
        pipeline: ScanPipeline,
        analyzer: AsyncMock,
        repository: MagicMock,
        analysis_request: AnalysisRequest,
    ) -> None:
        analyzer.analyze.side_effect = RuntimeError(
            "Analyzer failed."
        )

        persisted_statuses: list[ScanStatus] = []

        def capture_update(scan) -> None:
            persisted_statuses.append(scan.status)

        repository.update.side_effect = capture_update

        with pytest.raises(
            RuntimeError,
            match="Analyzer failed",
        ):
            await pipeline.execute(
                analysis_request,
            )

        assert repository.save.call_count == 1
        assert repository.update.call_count == 2

        assert persisted_statuses == [
            ScanStatus.RUNNING,
            ScanStatus.FAILED,
        ]

    @pytest.mark.asyncio
    async def test_execute_rejects_invalid_request(
        self,
        pipeline: ScanPipeline,
    ) -> None:
        with pytest.raises(
            TypeError,
            match="request must be an AnalysisRequest",
        ):
            await pipeline.execute(
                None,  # type: ignore[arg-type]
            )

    @pytest.mark.asyncio
    async def test_execute_does_not_call_analyzer_before_persistence(
        self,
        pipeline: ScanPipeline,
        analyzer: AsyncMock,
        repository: MagicMock,
        analysis_request: AnalysisRequest,
    ) -> None:
        events: list[str] = []

        def save(scan) -> None:
            events.append(
                f"save:{scan.status.value}"
            )

        def update(scan) -> None:
            events.append(
                f"update:{scan.status.value}"
            )

        async def analyze(request) -> tuple:
            events.append("analyze")
            return ()

        repository.save.side_effect = save
        repository.update.side_effect = update
        analyzer.analyze.side_effect = analyze

        await pipeline.execute(
            analysis_request,
        )

        assert events == [
            "save:queued",
            "update:running",
            "analyze",
            "update:completed",
        ]

    @pytest.mark.asyncio
    async def test_execute_passes_exact_analysis_request_to_analyzer(
        self,
        pipeline: ScanPipeline,
        analyzer: AsyncMock,
        analysis_request: AnalysisRequest,
    ) -> None:
        analyzer.analyze.return_value = ()

        await pipeline.execute(
            analysis_request,
        )

        analyzer.analyze.assert_awaited_once_with(
            analysis_request,
        )