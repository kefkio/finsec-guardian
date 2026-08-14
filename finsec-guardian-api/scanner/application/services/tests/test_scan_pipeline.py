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
from scanner.domain.exceptions import DomainValidationError
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
def heuristic_finding() -> Finding:
    return Finding(
        title="Missing access control",
        description="State mutation is not access controlled.",
        recommendation="Add appropriate access control.",
        severity=Severity.HIGH,
        confidence=Confidence.HIGH,
        risk_level=RiskLevel.HIGH,
        analyzer=AnalyzerType.HEURISTIC,
        location=SourceLocation(
            filename="VulnerableBank.sol",
            line=20,
            column=1,
            end_line=20,
            end_column=None,
        ),
        signature=VulnerabilitySignature("c" * 64),
        swc_id="SWC-105",
    )


@pytest.fixture
def slither_analyzer() -> AsyncMock:
    analyzer = AsyncMock(spec=AnalyzerPort)
    analyzer.name = AnalyzerType.SLITHER.value
    return analyzer


@pytest.fixture
def heuristic_analyzer() -> AsyncMock:
    analyzer = AsyncMock(spec=AnalyzerPort)
    analyzer.name = AnalyzerType.HEURISTIC.value
    return analyzer


@pytest.fixture
def repository() -> MagicMock:
    return MagicMock(spec=ScanRepository)


@pytest.fixture
def pipeline(
    slither_analyzer: AsyncMock,
    repository: MagicMock,
) -> ScanPipeline:
    return ScanPipeline(
        analyzers=(slither_analyzer,),
        repository=repository,
    )


class TestScanPipeline:

    @pytest.mark.asyncio
    async def test_execute_returns_completed_scan(
        self,
        pipeline: ScanPipeline,
        slither_analyzer: AsyncMock,
        repository: MagicMock,
        analysis_request: AnalysisRequest,
    ) -> None:
        slither_analyzer.analyze.return_value = ()

        scan = await pipeline.execute(
            analysis_request,
        )

        assert scan.status is ScanStatus.COMPLETED
        assert scan.smart_contract.filename == (
            "VulnerableBank.sol"
        )
        assert scan.smart_contract.contract_name == (
            "VulnerableBank"
        )
        assert scan.smart_contract.source_code == (
            "contract VulnerableBank {}"
        )

        slither_analyzer.analyze.assert_awaited_once_with(
            analysis_request,
        )

        assert repository.save.call_count == 1
        assert repository.update.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_merges_analyzer_findings(
        self,
        pipeline: ScanPipeline,
        slither_analyzer: AsyncMock,
        analysis_request: AnalysisRequest,
        finding: Finding,
    ) -> None:
        slither_analyzer.analyze.return_value = (
            finding,
        )

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
        slither_analyzer: AsyncMock,
        repository: MagicMock,
        analysis_request: AnalysisRequest,
    ) -> None:
        slither_analyzer.analyze.return_value = ()

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
        slither_analyzer: AsyncMock,
        repository: MagicMock,
        analysis_request: AnalysisRequest,
    ) -> None:
        slither_analyzer.analyze.side_effect = RuntimeError(
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
        slither_analyzer: AsyncMock,
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
        slither_analyzer.analyze.side_effect = analyze

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
        slither_analyzer: AsyncMock,
        analysis_request: AnalysisRequest,
    ) -> None:
        slither_analyzer.analyze.return_value = ()

        await pipeline.execute(
            analysis_request,
        )

        slither_analyzer.analyze.assert_awaited_once_with(
            analysis_request,
        )

    # ==========================================================
    # Multi-analyzer behavior
    # ==========================================================

    def test_pipeline_requires_at_least_one_analyzer(
        self,
        repository: MagicMock,
    ) -> None:
        with pytest.raises(
            ValueError,
            match="At least one analyzer",
        ):
            ScanPipeline(
                analyzers=(),
                repository=repository,
            )

    def test_pipeline_rejects_invalid_analyzer(
        self,
        repository: MagicMock,
    ) -> None:
        with pytest.raises(
            TypeError,
            match="All analyzers must implement AnalyzerPort",
        ):
            ScanPipeline(
                analyzers=(object(),),
                repository=repository,
            )

    def test_pipeline_exposes_configured_analyzers(
        self,
        slither_analyzer: AsyncMock,
        heuristic_analyzer: AsyncMock,
        repository: MagicMock,
    ) -> None:
        pipeline = ScanPipeline(
            analyzers=(
                slither_analyzer,
                heuristic_analyzer,
            ),
            repository=repository,
        )

        assert pipeline.analyzers == (
            slither_analyzer,
            heuristic_analyzer,
        )

    @pytest.mark.asyncio
    async def test_execute_runs_all_analyzers(
        self,
        slither_analyzer: AsyncMock,
        heuristic_analyzer: AsyncMock,
        repository: MagicMock,
        analysis_request: AnalysisRequest,
    ) -> None:
        slither_analyzer.analyze.return_value = ()
        heuristic_analyzer.analyze.return_value = ()

        pipeline = ScanPipeline(
            analyzers=(
                slither_analyzer,
                heuristic_analyzer,
            ),
            repository=repository,
        )

        scan = await pipeline.execute(
            analysis_request,
        )

        assert scan.status is ScanStatus.COMPLETED

        slither_analyzer.analyze.assert_awaited_once_with(
            analysis_request,
        )

        heuristic_analyzer.analyze.assert_awaited_once_with(
            analysis_request,
        )

    @pytest.mark.asyncio
    async def test_execute_merges_findings_from_all_analyzers(
        self,
        slither_analyzer: AsyncMock,
        heuristic_analyzer: AsyncMock,
        repository: MagicMock,
        analysis_request: AnalysisRequest,
        finding: Finding,
        heuristic_finding: Finding,
    ) -> None:
        slither_analyzer.analyze.return_value = (
            finding,
        )

        heuristic_analyzer.analyze.return_value = (
            heuristic_finding,
        )

        pipeline = ScanPipeline(
            analyzers=(
                slither_analyzer,
                heuristic_analyzer,
            ),
            repository=repository,
        )

        scan = await pipeline.execute(
            analysis_request,
        )

        assert scan.status is ScanStatus.COMPLETED
        assert scan.finding_count == 2

        assert {
            item.analyzer
            for item in scan.findings
        } == {
            AnalyzerType.SLITHER,
            AnalyzerType.HEURISTIC,
        }

        assert {
            item.fingerprint
            for item in scan.findings
        } == {
            finding.fingerprint,
            heuristic_finding.fingerprint,
        }

    @pytest.mark.asyncio
    async def test_analyzers_execute_in_configured_order(
        self,
        slither_analyzer: AsyncMock,
        heuristic_analyzer: AsyncMock,
        repository: MagicMock,
        analysis_request: AnalysisRequest,
    ) -> None:
        events: list[str] = []

        async def run_slither(request) -> tuple:
            events.append("slither")
            return ()

        async def run_heuristic(request) -> tuple:
            events.append("heuristic")
            return ()

        slither_analyzer.analyze.side_effect = run_slither
        heuristic_analyzer.analyze.side_effect = run_heuristic

        pipeline = ScanPipeline(
            analyzers=(
                slither_analyzer,
                heuristic_analyzer,
            ),
            repository=repository,
        )

        await pipeline.execute(
            analysis_request,
        )

        assert events == [
            "slither",
            "heuristic",
        ]

    @pytest.mark.asyncio
    async def test_duplicate_fingerprint_from_second_analyzer_fails_scan(
        self,
        slither_analyzer: AsyncMock,
        heuristic_analyzer: AsyncMock,
        repository: MagicMock,
        analysis_request: AnalysisRequest,
        finding: Finding,
    ) -> None:
        duplicate = Finding(
            title="Same vulnerability",
            description="Duplicate fingerprint.",
            recommendation="Review the finding.",
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            risk_level=RiskLevel.HIGH,
            analyzer=AnalyzerType.HEURISTIC,
            location=SourceLocation(
                filename="VulnerableBank.sol",
                line=10,
                column=1,
                end_line=10,
                end_column=None,
            ),
            signature=VulnerabilitySignature(
                finding.fingerprint,
            ),
            swc_id="SWC-107",
        )

        slither_analyzer.analyze.return_value = (
            finding,
        )

        heuristic_analyzer.analyze.return_value = (
            duplicate,
        )

        persisted_statuses: list[ScanStatus] = []

        def capture_update(scan) -> None:
            persisted_statuses.append(scan.status)

        repository.update.side_effect = capture_update

        pipeline = ScanPipeline(
            analyzers=(
                slither_analyzer,
                heuristic_analyzer,
            ),
            repository=repository,
        )

        with pytest.raises(
            DomainValidationError,
            match="Duplicate fingerprint",
        ):
            await pipeline.execute(
                analysis_request,
            )

        assert persisted_statuses == [
            ScanStatus.RUNNING,
            ScanStatus.FAILED,
        ]

    @pytest.mark.asyncio
    async def test_second_analyzer_failure_marks_scan_failed(
        self,
        slither_analyzer: AsyncMock,
        heuristic_analyzer: AsyncMock,
        repository: MagicMock,
        analysis_request: AnalysisRequest,
    ) -> None:
        slither_analyzer.analyze.return_value = ()

        heuristic_analyzer.analyze.side_effect = RuntimeError(
            "Heuristic analyzer failed."
        )

        persisted_statuses: list[ScanStatus] = []

        def capture_update(scan) -> None:
            persisted_statuses.append(scan.status)

        repository.update.side_effect = capture_update

        pipeline = ScanPipeline(
            analyzers=(
                slither_analyzer,
                heuristic_analyzer,
            ),
            repository=repository,
        )

        with pytest.raises(
            RuntimeError,
            match="Heuristic analyzer failed",
        ):
            await pipeline.execute(
                analysis_request,
            )

        assert persisted_statuses == [
            ScanStatus.RUNNING,
            ScanStatus.FAILED,
        ]

    @pytest.mark.asyncio
    async def test_first_analyzer_failure_prevents_later_analyzers(
        self,
        slither_analyzer: AsyncMock,
        heuristic_analyzer: AsyncMock,
        repository: MagicMock,
        analysis_request: AnalysisRequest,
    ) -> None:
        slither_analyzer.analyze.side_effect = RuntimeError(
            "Slither failed."
        )

        pipeline = ScanPipeline(
            analyzers=(
                slither_analyzer,
                heuristic_analyzer,
            ),
            repository=repository,
        )

        with pytest.raises(
            RuntimeError,
            match="Slither failed",
        ):
            await pipeline.execute(
                analysis_request,
            )

        heuristic_analyzer.analyze.assert_not_awaited()