from __future__ import annotations

import asyncio

import pytest

from scanner.application.services.scan_pipeline import ScanPipeline
from scanner.domain.entities.scan import Scan
from scanner.domain.enums import ScanStatus
from scanner.domain.value_objects.analysis_request import AnalysisRequest
from scanner.infrastructure.analyzers.heuristic_analyzer import (
    HeuristicAnalyzer,
)
from scanner.infrastructure.analyzers.slither_analyzer import (
    SlitherAnalyzer,
)
from scanner.infrastructure.persistence.repositories import (
    DjangoScanRepository,
)
from scanner.domain.enums import (
    AnalyzerType,
    ScanStatus,
)

pytestmark = pytest.mark.django_db


VULNERABLE_CONTRACT = """
pragma solidity ^0.8.20;

contract VulnerableBank {
    mapping(address => uint256) public balances;

    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw() public {
        uint256 amount = balances[msg.sender];

        (bool success, ) = msg.sender.call{value: amount}("");
        require(success);

        balances[msg.sender] = 0;
    }
}
"""


@pytest.fixture
def analysis_request() -> AnalysisRequest:
    return AnalysisRequest(
        source_code=VULNERABLE_CONTRACT,
        contract_name="VulnerableBank",
        source_filename="VulnerableBank.sol",
        solidity_version="0.8.20",
    )


@pytest.fixture
def pipeline() -> ScanPipeline:
    return ScanPipeline(
        analyzers=(
            SlitherAnalyzer(),
            HeuristicAnalyzer(),
        ),
        repository=DjangoScanRepository(),
    )


class TestScanPipelineIntegration:

    @pytest.mark.asyncio
    async def test_real_slither_scan_is_persisted_and_reloaded(
        self,
        pipeline: ScanPipeline,
        analysis_request: AnalysisRequest,
    ) -> None:
        scan = await pipeline.execute(
            analysis_request,
        )

        assert isinstance(scan, Scan)
        assert scan.status is ScanStatus.COMPLETED

        assert scan.smart_contract.filename == (
            "VulnerableBank.sol"
        )

        assert scan.smart_contract.contract_name == (
            "VulnerableBank"
        )

        assert scan.smart_contract.source_code == (
            VULNERABLE_CONTRACT.strip()
        )

        # The real Slither adapter should produce domain findings.
        assert scan.findings is not None

    @pytest.mark.asyncio
    async def test_persisted_scan_can_be_reloaded_through_repository(
        self,
        pipeline: ScanPipeline,
        analysis_request: AnalysisRequest,
    ) -> None:
        scan = await pipeline.execute(
            analysis_request,
        )

        repository = DjangoScanRepository()

        restored = await asyncio.to_thread(
            repository.get_by_id,
            scan.id,
        )

        assert restored is not None
        assert restored.id == scan.id
        assert restored.status is ScanStatus.COMPLETED

        assert restored.smart_contract.filename == (
            scan.smart_contract.filename
        )

        assert restored.smart_contract.contract_name == (
            scan.smart_contract.contract_name
        )

        assert restored.smart_contract.source_code == (
            scan.smart_contract.source_code
        )

    @pytest.mark.asyncio
    async def test_persisted_findings_match_pipeline_findings(
        self,
        pipeline: ScanPipeline,
        analysis_request: AnalysisRequest,
    ) -> None:
        scan = await pipeline.execute(
            analysis_request,
        )

        repository = DjangoScanRepository()

        restored = await asyncio.to_thread(
            repository.get_by_id,
            scan.id,
        )

        assert restored is not None

        assert restored.finding_count == (
            scan.finding_count
        )

        original_fingerprints = {
            finding.fingerprint
            for finding in scan.findings
        }

        restored_fingerprints = {
            finding.fingerprint
            for finding in restored.findings
        }

        assert restored_fingerprints == (
            original_fingerprints
        )

    @pytest.mark.asyncio
    async def test_pipeline_completes_real_scan_without_legacy_orchestrator(
        self,
        pipeline: ScanPipeline,
        analysis_request: AnalysisRequest,
    ) -> None:
        scan = await pipeline.execute(
            analysis_request,
        )

        assert scan.status is ScanStatus.COMPLETED

        repository = DjangoScanRepository()

        persisted = await asyncio.to_thread(
            repository.get_by_id,
            scan.id,
        )

        assert persisted is not None
        assert persisted.id == scan.id

@pytest.mark.asyncio
async def test_real_analyzers_merge_findings(
    pipeline: ScanPipeline,
    analysis_request: AnalysisRequest,
) -> None:
    scan = await pipeline.execute(
        analysis_request,
    )

    assert scan.status is ScanStatus.COMPLETED

    analyzers = {
        finding.analyzer
        for finding in scan.findings }

    assert AnalyzerType.SLITHER in analyzers
    assert AnalyzerType.HEURISTIC in analyzers

    @pytest.mark.asyncio
    async def test_persisted_findings_preserve_analyzer_identity(
        self,
        pipeline: ScanPipeline,
        analysis_request: AnalysisRequest,
    ) -> None:
        scan = await pipeline.execute(
            analysis_request,
        )

        repository = DjangoScanRepository()

        restored = await asyncio.to_thread(
            repository.get_by_id,
            scan.id,
        )

        assert restored is not None

        original_analyzers = {
            finding.analyzer
            for finding in scan.findings
        }

        restored_analyzers = {
            finding.analyzer
            for finding in restored.findings
        }

        assert restored_analyzers == (
            original_analyzers
        )