from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scanner.domain.entities import Finding
from scanner.domain.value_objects.analysis_request import AnalysisRequest
from scanner.infrastructure.analyzers.slither_analyzer import SlitherAnalyzer
from scanner.services.analyzers.base import AnalyzerResult
from scanner.services.analyzers.slither import SlitherError


@pytest.fixture
def analysis_request() -> AnalysisRequest:
    return AnalysisRequest(
        source_code="contract VulnerableBank {}",
        contract_name="VulnerableBank",
        source_filename="VulnerableBank.sol",
        solidity_version="0.8.20",
    )


@pytest.fixture
def detector() -> dict[str, object]:
    return {
        "check": "reentrancy-eth",
        "confidence": "High",
        "description": "Potential reentrancy vulnerability.",
        "impact": "High",
        "swc-id": "SWC-107",
        "id": "a" * 64,
        "markdown": "Apply the checks-effects-interactions pattern.",
        "elements": [
            {
                "name": "withdraw",
                "type": "function",
                "source_mapping": {
                    "filename_absolute": "/tmp/VulnerableBank.sol",
                    "filename_relative": "VulnerableBank.sol",
                    "filename_short": "VulnerableBank.sol",
                    "lines": [10],
                    "starting_column": 5,
                    "ending_column": 20,
                    "start": 100,
                    "length": 16,
                    "is_dependency": False,
                },
            }
        ],
    }


class TestSlitherAnalyzer:

    def test_name_returns_stable_identifier(self) -> None:
        analyzer = SlitherAnalyzer()

        assert analyzer.name == "slither"

    def test_implements_analyzer_port(self) -> None:
        from scanner.domain.ports.analyzer import AnalyzerPort

        analyzer = SlitherAnalyzer()

        assert isinstance(analyzer, AnalyzerPort)

    @pytest.mark.asyncio
    async def test_analyze_returns_mapped_findings(
        self,
        analysis_request: AnalysisRequest,
        detector: dict[str, object],
    ) -> None:
        result = AnalyzerResult(
            success=True,
            raw_output={
                "detectors": [detector],
            },
            stderr="",
            tool="slither",
        )

        with patch(
            "scanner.infrastructure.analyzers.slither_analyzer.LegacySlitherAnalyzer"
        ) as legacy_cls:
            legacy_instance = legacy_cls.return_value
            legacy_instance.analyze.return_value = result

            analyzer = SlitherAnalyzer()

            findings = await analyzer.analyze(
                analysis_request
            )

        assert isinstance(findings, tuple)
        assert len(findings) == 1
        assert isinstance(findings[0], Finding)

        assert findings[0].title == "reentrancy-eth"
        assert findings[0].swc_id == "SWC-107"

    @pytest.mark.asyncio
    async def test_analyze_passes_request_to_legacy_analyzer(
        self,
        analysis_request: AnalysisRequest,
    ) -> None:
        result = AnalyzerResult(
            success=True,
            raw_output={
                "detectors": [],
            },
            tool="slither",
        )

        with patch(
            "scanner.infrastructure.analyzers.slither_analyzer.LegacySlitherAnalyzer"
        ) as legacy_cls:
            legacy_instance = legacy_cls.return_value
            legacy_instance.analyze.return_value = result

            analyzer = SlitherAnalyzer()

            findings = await analyzer.analyze(
                analysis_request
            )

        legacy_instance.analyze.assert_called_once_with(
            source_code=analysis_request.source_code,
            contract_name=analysis_request.contract_name,
        )

        assert findings == ()

    @pytest.mark.asyncio
    async def test_analyze_returns_empty_tuple_when_no_detectors(
        self,
        analysis_request: AnalysisRequest,
    ) -> None:
        result = AnalyzerResult(
            success=True,
            raw_output={
                "detectors": [],
            },
            tool="slither",
        )

        with patch(
            "scanner.infrastructure.analyzers.slither_analyzer.LegacySlitherAnalyzer"
        ) as legacy_cls:
            legacy_instance = legacy_cls.return_value
            legacy_instance.analyze.return_value = result

            analyzer = SlitherAnalyzer()

            findings = await analyzer.analyze(
                analysis_request
            )

        assert findings == ()

    @pytest.mark.asyncio
    async def test_analyze_propagates_slither_error(
        self,
        analysis_request: AnalysisRequest,
    ) -> None:
        with patch(
            "scanner.infrastructure.analyzers.slither_analyzer.LegacySlitherAnalyzer"
        ) as legacy_cls:
            legacy_instance = legacy_cls.return_value
            legacy_instance.analyze.side_effect = SlitherError(
                "Slither analysis timed out."
            )

            analyzer = SlitherAnalyzer()

            with pytest.raises(
                SlitherError,
                match="Slither analysis timed out",
            ):
                await analyzer.analyze(
                    analysis_request
                )

    @pytest.mark.asyncio
    async def test_analyze_does_not_call_legacy_analyzer_directly_on_event_loop(
        self,
        analysis_request: AnalysisRequest,
    ) -> None:
        result = AnalyzerResult(
            success=True,
            raw_output={
                "detectors": [],
            },
            tool="slither",
        )

        with patch(
            "scanner.infrastructure.analyzers.slither_analyzer.asyncio.to_thread",
            new_callable=AsyncMock,
        ) as to_thread:
            to_thread.return_value = result

            analyzer = SlitherAnalyzer()

            findings = await analyzer.analyze(
                analysis_request
            )

        to_thread.assert_awaited_once()

        assert findings == ()

    @pytest.mark.asyncio
    async def test_analyze_handles_missing_detectors(
        self,
        analysis_request: AnalysisRequest,
    ) -> None:
        result = AnalyzerResult(
            success=True,
            raw_output={},
            tool="slither",
        )

        with patch(
            "scanner.infrastructure.analyzers.slither_analyzer.LegacySlitherAnalyzer"
        ) as legacy_cls:
            legacy_instance = legacy_cls.return_value
            legacy_instance.analyze.return_value = result

            analyzer = SlitherAnalyzer()

            findings = await analyzer.analyze(
                analysis_request
            )

        assert findings == ()


class TestSlitherAnalyzerFailureHandling:

    @pytest.mark.asyncio
    async def test_analyze_rejects_invalid_analysis_request(
        self,
    ) -> None:
        analyzer = SlitherAnalyzer()

        with pytest.raises(
            TypeError,
        ):
            await analyzer.analyze(
                None,  # type: ignore[arg-type]
            )