from __future__ import annotations

from collections.abc import Sequence

import pytest

from scanner.domain.entities import Finding
from scanner.domain.ports.analyzer import AnalyzerPort
from scanner.domain.value_objects.analysis_request import AnalysisRequest


def test_cannot_instantiate_abstract_analyzer_port() -> None:
    with pytest.raises(TypeError):
        AnalyzerPort()  # type: ignore[abstract]


def test_subclass_missing_name_property_cannot_be_instantiated() -> None:
    class IncompleteAnalyzer(AnalyzerPort):
        async def analyze(
            self,
            request: AnalysisRequest,
        ) -> Sequence[Finding]:
            return []

    with pytest.raises(TypeError):
        IncompleteAnalyzer()  # type: ignore[abstract]


def test_subclass_missing_analyze_method_cannot_be_instantiated() -> None:
    class IncompleteAnalyzer(AnalyzerPort):
        @property
        def name(self) -> str:
            return "incomplete"

    with pytest.raises(TypeError):
        IncompleteAnalyzer()  # type: ignore[abstract]


@pytest.mark.asyncio
async def test_valid_concrete_analyzer_fulfills_port_contract() -> None:
    class DummyAnalyzer(AnalyzerPort):
        @property
        def name(self) -> str:
            return "dummy"

        async def analyze(
            self,
            request: AnalysisRequest,
        ) -> Sequence[Finding]:
            return []

    analyzer = DummyAnalyzer()
    request = AnalysisRequest(
        source_code="contract Test {}",
        contract_name="Test",
    )

    assert analyzer.name == "dummy"

    findings = await analyzer.analyze(request)

    assert findings == []