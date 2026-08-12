from __future__ import annotations

import pytest

from scanner.domain.entities import Finding
from scanner.domain.enums import (
    AnalyzerType,
    Confidence,
    RiskLevel,
    Severity,
)
from scanner.domain.exceptions import DomainValidationError
from scanner.domain.value_objects.analysis_request import AnalysisRequest
from scanner.infrastructure.analyzers.slither_finding_mapper import (
    SlitherFindingMapper,
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
def detector() -> dict[str, object]:
    return {
        "check": "solc-version",
        "confidence": "High",
        "description": (
            "Version constraint ^0.8.20 contains known severe issues."
        ),
        "impact": "Informational",
        "swc-id": "",
        "id": (
            "157d811179572a90ab419ac76caa7cfdf5f45e6d5b44f6e680cca0c56a75b47b"
        ),
        "markdown": (
            "Version constraint ^0.8.20 contains known severe issues."
        ),
        "first_markdown_element": "VulnerableBank.sol#L1",
        "reference": (
            "https://github.com/crytic/slither/wiki/"
            "Detector-Documentation#incorrect-versions-of-solidity"
        ),
        "elements": [
            {
                "name": "^0.8.20",
                "type": "pragma",
                "source_mapping": {
                    "ending_column": 25,
                    "filename_absolute": "/tmp/VulnerableBank.sol",
                    "filename_relative": "VulnerableBank.sol",
                    "filename_short": "VulnerableBank.sol",
                    "is_dependency": False,
                    "length": 24,
                    "lines": [1],
                    "start": 0,
                    "starting_column": 1,
                },
            }
        ],
    }


class TestSlitherFindingMapper:

    def test_maps_detector_to_finding(
        self,
        detector: dict[str, object],
        analysis_request: AnalysisRequest,
    ) -> None:
        finding = SlitherFindingMapper.map_detector(
            detector=detector,
            request=analysis_request,
        )

        assert isinstance(finding, Finding)
        assert finding.title == "solc-version"
        assert finding.description.startswith(
            "Version constraint ^0.8.20"
        )
        assert finding.recommendation.startswith(
            "Version constraint ^0.8.20"
        )
        assert finding.analyzer is AnalyzerType.SLITHER

    @pytest.mark.parametrize(
        ("impact", "expected"),
        [
            ("Critical", Severity.CRITICAL),
            ("High", Severity.HIGH),
            ("Medium", Severity.MEDIUM),
            ("Low", Severity.LOW),
            ("Informational", Severity.INFORMATIONAL),
            ("info", Severity.INFORMATIONAL),
        ],
    )
    def test_maps_impact_to_severity(
        self,
        detector: dict[str, object],
        analysis_request: AnalysisRequest,
        impact: str,
        expected: Severity,
    ) -> None:
        detector["impact"] = impact

        finding = SlitherFindingMapper.map_detector(
            detector=detector,
            request=analysis_request,
        )

        assert finding.severity is expected

    @pytest.mark.parametrize(
        ("impact", "expected"),
        [
            ("Critical", RiskLevel.CRITICAL),
            ("High", RiskLevel.HIGH),
            ("Medium", RiskLevel.MEDIUM),
            ("Low", RiskLevel.LOW),
            ("Informational", RiskLevel.VERY_LOW),
        ],
    )
    def test_derives_risk_level_from_severity(
        self,
        detector: dict[str, object],
        analysis_request: AnalysisRequest,
        impact: str,
        expected: RiskLevel,
    ) -> None:
        detector["impact"] = impact

        finding = SlitherFindingMapper.map_detector(
            detector=detector,
            request=analysis_request,
        )

        assert finding.risk_level is expected

    @pytest.mark.parametrize(
        ("confidence", "expected"),
        [
            ("High", Confidence.HIGH),
            ("Medium", Confidence.MEDIUM),
            ("Low", Confidence.LOW),
        ],
    )
    def test_maps_confidence(
        self,
        detector: dict[str, object],
        analysis_request: AnalysisRequest,
        confidence: str,
        expected: Confidence,
    ) -> None:
        detector["confidence"] = confidence

        finding = SlitherFindingMapper.map_detector(
            detector=detector,
            request=analysis_request,
        )

        assert finding.confidence is expected

    def test_missing_confidence_uses_conservative_default(
        self,
        detector: dict[str, object],
        analysis_request: AnalysisRequest,
    ) -> None:
        detector.pop("confidence")

        finding = SlitherFindingMapper.map_detector(
            detector=detector,
            request=analysis_request,
        )

        assert finding.confidence is Confidence.LOW

    def test_blank_confidence_uses_conservative_default(
        self,
        detector: dict[str, object],
        analysis_request: AnalysisRequest,
    ) -> None:
        detector["confidence"] = "   "

        finding = SlitherFindingMapper.map_detector(
            detector=detector,
            request=analysis_request,
        )

        assert finding.confidence is Confidence.LOW

    def test_maps_swc_id(
        self,
        detector: dict[str, object],
        analysis_request: AnalysisRequest,
    ) -> None:
        detector["swc-id"] = "SWC-107"

        finding = SlitherFindingMapper.map_detector(
            detector=detector,
            request=analysis_request,
        )

        assert finding.swc_id == "SWC-107"

    def test_empty_swc_id_becomes_none(
        self,
        detector: dict[str, object],
        analysis_request: AnalysisRequest,
    ) -> None:
        detector["swc-id"] = "   "

        finding = SlitherFindingMapper.map_detector(
            detector=detector,
            request=analysis_request,
        )

        assert finding.swc_id is None

    def test_uses_markdown_as_recommendation(
        self,
        detector: dict[str, object],
        analysis_request: AnalysisRequest,
    ) -> None:
        detector["markdown"] = (
            "  Apply a supported compiler version.  "
        )

        finding = SlitherFindingMapper.map_detector(
            detector=detector,
            request=analysis_request,
        )

        assert finding.recommendation == (
            "Apply a supported compiler version."
        )

    def test_recommendation_falls_back_when_markdown_missing(
        self,
        detector: dict[str, object],
        analysis_request: AnalysisRequest,
    ) -> None:
        detector.pop("markdown")

        finding = SlitherFindingMapper.map_detector(
            detector=detector,
            request=analysis_request,
        )

        assert finding.recommendation == (
            "Review and remediate the identified issue: solc-version."
        )

    def test_maps_source_location(
        self,
        detector: dict[str, object],
        analysis_request: AnalysisRequest,
    ) -> None:
        finding = SlitherFindingMapper.map_detector(
            detector=detector,
            request=analysis_request,
        )

        assert finding.location.filename == "VulnerableBank.sol"
        assert finding.location.line == 1
        assert finding.location.column == 1
        assert finding.location.end_column == 25

    def test_source_filename_falls_back_to_request(
        self,
        detector: dict[str, object],
        analysis_request: AnalysisRequest,
    ) -> None:
        source_mapping = detector["elements"][0]["source_mapping"]

        assert isinstance(source_mapping, dict)

        source_mapping["filename_relative"] = ""
        source_mapping["filename_short"] = ""
        source_mapping["filename_absolute"] = ""

        finding = SlitherFindingMapper.map_detector(
            detector=detector,
            request=analysis_request,
        )

        assert finding.location.filename == "VulnerableBank.sol"

    def test_source_filename_falls_back_to_default(
        self,
        detector: dict[str, object],
    ) -> None:
        analysis_request = AnalysisRequest(
            source_code="contract Test {}",
        )

        source_mapping = detector["elements"][0]["source_mapping"]

        assert isinstance(source_mapping, dict)

        source_mapping["filename_relative"] = ""
        source_mapping["filename_short"] = ""
        source_mapping["filename_absolute"] = ""

        finding = SlitherFindingMapper.map_detector(
            detector=detector,
            request=analysis_request,
        )

        assert finding.location.filename == "contract.sol"

    def test_generates_vulnerability_signature(
        self,
        detector: dict[str, object],
        analysis_request: AnalysisRequest,
    ) -> None:
        finding = SlitherFindingMapper.map_detector(
            detector=detector,
            request=analysis_request,
        )

        assert finding.signature is not None
        assert finding.signature.is_sha256
        assert len(finding.signature.value) == 64

    def test_fingerprint_is_deterministic(
        self,
        detector: dict[str, object],
        analysis_request: AnalysisRequest,
    ) -> None:
        first = SlitherFindingMapper.map_detector(
            detector=detector,
            request=analysis_request,
        )
        second = SlitherFindingMapper.map_detector(
            detector=detector,
            request=analysis_request,
        )

        assert first.signature == second.signature
        assert first.fingerprint == second.fingerprint

    def test_invalid_detector_type_is_rejected(
        self,
        analysis_request: AnalysisRequest,
    ) -> None:
        with pytest.raises(
            DomainValidationError,
            match="Slither detector must be a mapping",
        ):
            SlitherFindingMapper.map_detector(
                detector=[],  # type: ignore[arg-type]
                request=analysis_request,
            )

    def test_invalid_request_type_is_rejected(
        self,
        detector: dict[str, object],
    ) -> None:
        with pytest.raises(
            DomainValidationError,
            match="request must be an AnalysisRequest",
        ):
            SlitherFindingMapper.map_detector(
                detector=detector,
                request=None,  # type: ignore[arg-type]
            )

    def test_invalid_impact_is_rejected(
        self,
        detector: dict[str, object],
        analysis_request: AnalysisRequest,
    ) -> None:
        detector["impact"] = "unknown"

        with pytest.raises(
            DomainValidationError,
            match="Unsupported Slither impact",
        ):
            SlitherFindingMapper.map_detector(
                detector=detector,
                request=analysis_request,
            )

    def test_invalid_confidence_is_rejected(
        self,
        detector: dict[str, object],
        analysis_request: AnalysisRequest,
    ) -> None:
        detector["confidence"] = "unknown"

        with pytest.raises(
            DomainValidationError,
            match="Unsupported Slither confidence",
        ):
            SlitherFindingMapper.map_detector(
                detector=detector,
                request=analysis_request,
            )

    def test_missing_source_mapping_is_rejected(
        self,
        detector: dict[str, object],
        analysis_request: AnalysisRequest,
    ) -> None:
        detector.pop("elements")

        with pytest.raises(
            DomainValidationError,
            match="valid source_mapping",
        ):
            SlitherFindingMapper.map_detector(
                detector=detector,
                request=analysis_request,
            )

    def test_map_all_returns_tuple(
        self,
        detector: dict[str, object],
        analysis_request: AnalysisRequest,
    ) -> None:
        second = dict(detector)
        second["check"] = "another-detector"

        findings = SlitherFindingMapper.map_all(
            detectors=[detector, second],
            request=analysis_request,
        )

        assert isinstance(findings, tuple)
        assert len(findings) == 2
        assert all(
            isinstance(finding, Finding)
            for finding in findings
        )

    def test_map_all_preserves_detector_order(
        self,
        detector: dict[str, object],
        analysis_request: AnalysisRequest,
    ) -> None:
        second = dict(detector)
        second["check"] = "second-detector"

        findings = SlitherFindingMapper.map_all(
            detectors=[detector, second],
            request=analysis_request,
        )

        assert findings[0].title == "solc-version"
        assert findings[1].title == "second-detector"