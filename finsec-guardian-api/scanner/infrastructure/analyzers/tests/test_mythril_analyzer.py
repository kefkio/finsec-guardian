from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from scanner.domain.enums import AnalyzerType
from scanner.domain.exceptions import DomainValidationError
from scanner.domain.value_objects.analysis_request import AnalysisRequest
from scanner.infrastructure.analyzers.mythril_analyzer import (
    MythrilAnalyzer,
)


def make_request(
    source_code: str = (
        "pragma solidity ^0.8.20;\n"
        "contract Test {}"
    ),
    filename: str = "Test.sol",
) -> AnalysisRequest:
    return AnalysisRequest(
        source_code=source_code,
        contract_name="Test",
        source_filename=filename,
        solidity_version="0.8.20",
    )


@pytest.fixture
def analyzer() -> MythrilAnalyzer:
    return MythrilAnalyzer()


class TestMythrilAnalyzer:

    def test_name_is_mythril(
        self,
        analyzer: MythrilAnalyzer,
    ) -> None:
        assert analyzer.name == AnalyzerType.MYTHRIL.value
        assert analyzer.name == "mythril"

    @pytest.mark.asyncio
    async def test_invalid_request_is_rejected(
        self,
        analyzer: MythrilAnalyzer,
    ) -> None:
        with pytest.raises(
            DomainValidationError,
            match="request must be an AnalysisRequest",
        ):
            await analyzer.analyze(
                None,  # type: ignore[arg-type]
            )

    @pytest.mark.asyncio
    async def test_maps_mythril_issues_to_domain_findings(
        self,
        analyzer: MythrilAnalyzer,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        request = make_request()

        legacy_result = MagicMock()
        legacy_result.success = True
        legacy_result.error = None
        legacy_result.raw_output = {
            "issues": [
                {
                    "swc_id": "SWC-107",
                    "title": "Reentrancy",
                    "severity": "High",
                    "description_long": (
                        "Potential reentrancy vulnerability."
                    ),
                    "description_short": (
                        "External call may be reentrant."
                    ),
                    "lineno": 12,
                    "code": "msg.sender.call(...)",
                    "function": "withdraw",
                    "address": 100,
                }
            ]
        }

        def fake_legacy_runner(
            request: AnalysisRequest,
        ):
            assert request is request_arg
            return legacy_result

        request_arg = request

        monkeypatch.setattr(
            analyzer,
            "_run_legacy_analyzer",
            fake_legacy_runner,
        )

        findings = await analyzer.analyze(request)

        assert len(findings) == 1

        finding = findings[0]

        assert finding.analyzer is AnalyzerType.MYTHRIL
        assert finding.title == "Reentrancy"
        assert finding.swc_id == "SWC-107"
        assert finding.location.filename == "Test.sol"
        assert finding.location.line == 12

    @pytest.mark.asyncio
    async def test_passes_exact_request_to_legacy_analyzer(
        self,
        analyzer: MythrilAnalyzer,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        request = make_request()

        legacy_result = MagicMock()
        legacy_result.success = True
        legacy_result.error = None
        legacy_result.raw_output = {
            "issues": []
        }

        received: list[AnalysisRequest] = []

        def fake_legacy_runner(
            received_request: AnalysisRequest,
        ):
            received.append(received_request)
            return legacy_result

        monkeypatch.setattr(
            analyzer,
            "_run_legacy_analyzer",
            fake_legacy_runner,
        )

        await analyzer.analyze(request)

        assert received == [request]
        assert received[0] is request

    @pytest.mark.asyncio
    async def test_returns_empty_tuple_when_mythril_finds_no_issues(
        self,
        analyzer: MythrilAnalyzer,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        legacy_result = MagicMock()
        legacy_result.success = True
        legacy_result.error = None
        legacy_result.raw_output = {
            "issues": []
        }

        monkeypatch.setattr(
            analyzer,
            "_run_legacy_analyzer",
            lambda request: legacy_result,
        )

        findings = await analyzer.analyze(
            make_request(),
        )

        assert findings == ()
        assert isinstance(findings, tuple)

    @pytest.mark.asyncio
    async def test_handles_missing_issues_key(
        self,
        analyzer: MythrilAnalyzer,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        legacy_result = MagicMock()
        legacy_result.success = True
        legacy_result.error = None
        legacy_result.raw_output = {}

        monkeypatch.setattr(
            analyzer,
            "_run_legacy_analyzer",
            lambda request: legacy_result,
        )

        findings = await analyzer.analyze(
            make_request(),
        )

        assert findings == ()

    @pytest.mark.asyncio
    async def test_raises_when_legacy_mythril_fails(
        self,
        analyzer: MythrilAnalyzer,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        legacy_result = MagicMock()
        legacy_result.success = False
        legacy_result.error = "Mythril timed out"
        legacy_result.raw_output = {}

        monkeypatch.setattr(
            analyzer,
            "_run_legacy_analyzer",
            lambda request: legacy_result,
        )

        with pytest.raises(
            RuntimeError,
            match="Mythril timed out",
        ):
            await analyzer.analyze(
                make_request(),
            )

    @pytest.mark.asyncio
    async def test_raises_generic_error_when_legacy_error_is_missing(
        self,
        analyzer: MythrilAnalyzer,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        legacy_result = MagicMock()
        legacy_result.success = False
        legacy_result.error = None
        legacy_result.raw_output = {}

        monkeypatch.setattr(
            analyzer,
            "_run_legacy_analyzer",
            lambda request: legacy_result,
        )

        with pytest.raises(
            RuntimeError,
            match="Mythril analysis failed",
        ):
            await analyzer.analyze(
                make_request(),
            )

    @pytest.mark.asyncio
    async def test_maps_multiple_findings(
        self,
        analyzer: MythrilAnalyzer,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        legacy_result = MagicMock()
        legacy_result.success = True
        legacy_result.error = None
        legacy_result.raw_output = {
            "issues": [
                {
                    "swc_id": "SWC-107",
                    "title": "Reentrancy",
                    "severity": "High",
                    "description_long": "Reentrancy issue.",
                    "description_short": "Reentrancy.",
                    "lineno": 10,
                    "code": "call(...)",
                    "function": "withdraw",
                },
                {
                    "swc_id": "SWC-101",
                    "title": "Integer Arithmetic Bug",
                    "severity": "Medium",
                    "description_long": "Arithmetic issue.",
                    "description_short": "Arithmetic.",
                    "lineno": 20,
                    "code": "a + b",
                    "function": "calculate",
                },
            ]
        }

        monkeypatch.setattr(
            analyzer,
            "_run_legacy_analyzer",
            lambda request: legacy_result,
        )

        findings = await analyzer.analyze(
            make_request(),
        )

        assert len(findings) == 2
        assert {
            finding.title
            for finding in findings
        } == {
            "Reentrancy",
            "Integer Arithmetic Bug",
        }

        assert all(
            finding.analyzer is AnalyzerType.MYTHRIL
            for finding in findings
        )

    @pytest.mark.asyncio
    async def test_legacy_runner_exception_propagates(
        self,
        analyzer: MythrilAnalyzer,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def raise_error(
            request: AnalysisRequest,
        ):
            raise RuntimeError("runner exploded")

        monkeypatch.setattr(
            analyzer,
            "_run_legacy_analyzer",
            raise_error,
        )

        with pytest.raises(
            RuntimeError,
            match="runner exploded",
        ):
            await analyzer.analyze(
                make_request(),
            )

    def test_legacy_runner_delegates_to_legacy_mythril(
        self,
        analyzer: MythrilAnalyzer,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        request = make_request()

        legacy_instance = MagicMock()
        legacy_instance.analyze.return_value = "result"

        legacy_class = MagicMock(
            return_value=legacy_instance,
        )

        monkeypatch.setattr(
            "scanner.infrastructure.analyzers.mythril_analyzer.LegacyMythrilAnalyzer",
            legacy_class,
        )

        result = analyzer._run_legacy_analyzer(
            request,
        )

        assert result == "result"

        legacy_class.assert_called_once_with()

        legacy_instance.analyze.assert_called_once_with(
            source_code=request.source_code,
            contract_name=request.contract_name,
        )