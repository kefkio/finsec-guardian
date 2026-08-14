from __future__ import annotations

import pytest

from scanner.domain.enums import (
    AnalyzerType,
    Confidence,
    RiskLevel,
    Severity,
)
from scanner.domain.value_objects.analysis_request import AnalysisRequest
from scanner.infrastructure.analyzers.mythril_finding_mapper import (
    MythrilFindingMapper,
)


def make_request(
    source_code: str = "pragma solidity ^0.8.20;\ncontract Test {}",
    filename: str = "Test.sol",
) -> AnalysisRequest:
    return AnalysisRequest(
        source_code=source_code,
        contract_name="Test",
        source_filename=filename,
        solidity_version="0.8.20",
    )


class TestMythrilFindingMapper:

    def test_map_one_creates_domain_finding(self) -> None:
        issue = {
            "swc_id": "SWC-107",
            "title": "External Call To User-Supplied Address",
            "severity": "High",
            "description_long": "Potential reentrancy vulnerability.",
            "description_short": "External call may be reentrant.",
            "lineno": 12,
            "code": "msg.sender.call.value(amount)();",
            "function": "withdraw",
            "address": 123,
        }

        finding = MythrilFindingMapper.map_one(
            issue=issue,
            request=make_request(),
        )

        assert finding is not None
        assert finding.title == (
            "External Call To User-Supplied Address"
        )
        assert finding.description == (
            "Potential reentrancy vulnerability."
        )
        assert finding.severity is Severity.HIGH
        assert finding.confidence is Confidence.HIGH
        assert finding.risk_level is RiskLevel.HIGH
        assert finding.analyzer is AnalyzerType.MYTHRIL
        assert finding.swc_id == "SWC-107"
        assert finding.location.filename == "Test.sol"
        assert finding.location.line == 12
        assert finding.location.column is None
        assert finding.location.end_line == 12
        assert finding.location.end_column is None

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("Critical", Severity.CRITICAL),
            ("High", Severity.HIGH),
            ("Medium", Severity.MEDIUM),
            ("Low", Severity.LOW),
            ("Informational", Severity.INFORMATIONAL),
            ("Info", Severity.INFORMATIONAL),
            ("unknown", Severity.MEDIUM),
            (None, Severity.MEDIUM),
        ],
    )
    def test_severity_mapping(
        self,
        raw: str | None,
        expected: Severity,
    ) -> None:
        assert (
            MythrilFindingMapper._map_severity(raw)
            is expected
        )

    def test_critical_finding_has_critical_risk(
        self,
    ) -> None:
        issue = {
            "title": "Critical issue",
            "severity": "Critical",
            "description_short": "Critical issue.",
            "lineno": 5,
        }

        finding = MythrilFindingMapper.map_one(
            issue=issue,
            request=make_request(),
        )

        assert finding is not None
        assert finding.severity is Severity.CRITICAL
        assert finding.risk_level is RiskLevel.CRITICAL
        assert finding.confidence is Confidence.HIGH

    def test_high_finding_has_high_risk(
        self,
    ) -> None:
        issue = {
            "title": "High issue",
            "severity": "High",
            "description_short": "High issue.",
            "lineno": 5,
        }

        finding = MythrilFindingMapper.map_one(
            issue=issue,
            request=make_request(),
        )

        assert finding is not None
        assert finding.severity is Severity.HIGH
        assert finding.risk_level is RiskLevel.HIGH
        assert finding.confidence is Confidence.HIGH

    def test_medium_finding_has_medium_risk(
        self,
    ) -> None:
        issue = {
            "title": "Medium issue",
            "severity": "Medium",
            "description_short": "Medium issue.",
            "lineno": 5,
        }

        finding = MythrilFindingMapper.map_one(
            issue=issue,
            request=make_request(),
        )

        assert finding is not None
        assert finding.severity is Severity.MEDIUM
        assert finding.risk_level is RiskLevel.MEDIUM
        assert finding.confidence is Confidence.HIGH

    def test_low_finding_has_medium_confidence(
        self,
    ) -> None:
        issue = {
            "title": "Low issue",
            "severity": "Low",
            "description_short": "Low issue.",
            "lineno": 5,
        }

        finding = MythrilFindingMapper.map_one(
            issue=issue,
            request=make_request(),
        )

        assert finding is not None
        assert finding.severity is Severity.LOW
        assert finding.risk_level is RiskLevel.LOW
        assert finding.confidence is Confidence.MEDIUM

    def test_informational_finding_maps_to_very_low_risk(
        self,
    ) -> None:
        issue = {
            "title": "Compiler information",
            "severity": "Informational",
            "description_short": "Informational finding.",
            "lineno": 1,
        }

        finding = MythrilFindingMapper.map_one(
            issue=issue,
            request=make_request(),
        )

        assert finding is not None
        assert finding.severity is Severity.INFORMATIONAL
        assert finding.risk_level is RiskLevel.VERY_LOW
        assert finding.confidence is Confidence.MEDIUM

    def test_long_description_takes_precedence(
        self,
    ) -> None:
        issue = {
            "title": "Issue",
            "severity": "Medium",
            "description_long": "Long description.",
            "description_short": "Short description.",
            "lineno": 10,
        }

        finding = MythrilFindingMapper.map_one(
            issue=issue,
            request=make_request(),
        )

        assert finding is not None
        assert finding.description == "Long description."

    def test_short_description_is_used_when_long_is_missing(
        self,
    ) -> None:
        issue = {
            "title": "Issue",
            "severity": "Medium",
            "description_short": "Short description.",
            "lineno": 10,
        }

        finding = MythrilFindingMapper.map_one(
            issue=issue,
            request=make_request(),
        )

        assert finding is not None
        assert finding.description == "Short description."

    def test_fallback_description_is_generated(
        self,
    ) -> None:
        issue = {
            "title": "Fallback issue",
            "severity": "Medium",
            "lineno": 10,
        }

        finding = MythrilFindingMapper.map_one(
            issue=issue,
            request=make_request(),
        )

        assert finding is not None
        assert finding.description == (
            "Mythril identified a potential vulnerability: "
            "Fallback issue."
        )

    def test_missing_title_is_rejected(
        self,
    ) -> None:
        issue = {
            "severity": "High",
            "description_short": "No title.",
            "lineno": 10,
        }

        finding = MythrilFindingMapper.map_one(
            issue=issue,
            request=make_request(),
        )

        assert finding is None

    def test_invalid_issue_is_rejected(
        self,
    ) -> None:
        finding = MythrilFindingMapper.map_one(
            issue={"title": ""},
            request=make_request(),
        )

        assert finding is None

    def test_missing_line_defaults_to_one(
        self,
    ) -> None:
        issue = {
            "title": "Missing line",
            "severity": "Medium",
        }

        finding = MythrilFindingMapper.map_one(
            issue=issue,
            request=make_request(),
        )

        assert finding is not None
        assert finding.location.line == 1

    def test_invalid_line_defaults_to_one(
        self,
    ) -> None:
        issue = {
            "title": "Invalid line",
            "severity": "Medium",
            "lineno": "not-a-number",
        }

        finding = MythrilFindingMapper.map_one(
            issue=issue,
            request=make_request(),
        )

        assert finding is not None
        assert finding.location.line == 1

    def test_filename_comes_from_request(
        self,
    ) -> None:
        issue = {
            "title": "Issue",
            "severity": "High",
            "lineno": 42,
        }

        finding = MythrilFindingMapper.map_one(
            issue=issue,
            request=make_request(
                filename="contracts/Vault.sol",
            ),
        )

        assert finding is not None
        assert finding.location.filename == (
            "contracts/Vault.sol"
        )

    def test_swc_id_is_preserved(
        self,
    ) -> None:
        issue = {
            "title": "Reentrancy",
            "severity": "High",
            "swc_id": "SWC-107",
            "lineno": 20,
        }

        finding = MythrilFindingMapper.map_one(
            issue=issue,
            request=make_request(),
        )

        assert finding is not None
        assert finding.swc_id == "SWC-107"

    def test_optional_swc_id_becomes_none(
        self,
    ) -> None:
        issue = {
            "title": "Issue",
            "severity": "Medium",
            "swc_id": "",
            "lineno": 20,
        }

        finding = MythrilFindingMapper.map_one(
            issue=issue,
            request=make_request(),
        )

        assert finding is not None
        assert finding.swc_id is None

    def test_recommendation_contains_issue_identity(
        self,
    ) -> None:
        issue = {
            "title": "Integer Arithmetic Bug",
            "severity": "Medium",
            "swc_id": "SWC-101",
            "lineno": 8,
        }

        finding = MythrilFindingMapper.map_one(
            issue=issue,
            request=make_request(),
        )

        assert finding is not None
        assert "Integer Arithmetic Bug" in (
            finding.recommendation
        )
        assert "SWC-101" in finding.recommendation

    def test_fingerprint_is_deterministic(
        self,
    ) -> None:
        issue = {
            "title": "Reentrancy",
            "severity": "High",
            "swc_id": "SWC-107",
            "lineno": 20,
            "function": "withdraw",
            "code": "msg.sender.call(...)",
        }

        request = make_request()

        first = MythrilFindingMapper.map_one(
            issue=issue,
            request=request,
        )

        second = MythrilFindingMapper.map_one(
            issue=issue,
            request=request,
        )

        assert first is not None
        assert second is not None
        assert first.fingerprint == second.fingerprint

    def test_different_issue_attributes_produce_different_fingerprints(
        self,
    ) -> None:
        base_issue = {
            "title": "Reentrancy",
            "severity": "High",
            "swc_id": "SWC-107",
            "lineno": 20,
            "function": "withdraw",
            "code": "msg.sender.call(...)",
        }

        changed_issue = {
            **base_issue,
            "lineno": 25,
        }

        request = make_request()

        first = MythrilFindingMapper.map_one(
            issue=base_issue,
            request=request,
        )

        second = MythrilFindingMapper.map_one(
            issue=changed_issue,
            request=request,
        )

        assert first is not None
        assert second is not None
        assert first.fingerprint != second.fingerprint

    def test_fingerprint_is_sha256_hex(
        self,
    ) -> None:
        issue = {
            "title": "Reentrancy",
            "severity": "High",
            "swc_id": "SWC-107",
            "lineno": 20,
        }

        finding = MythrilFindingMapper.map_one(
            issue=issue,
            request=make_request(),
        )

        assert finding is not None
        assert len(finding.fingerprint) == 64
        assert all(
            character in "0123456789abcdef"
            for character in finding.fingerprint
        )

    def test_map_all_returns_tuple(
        self,
    ) -> None:
        issues = [
            {
                "title": "Issue one",
                "severity": "High",
                "lineno": 10,
            },
            {
                "title": "Issue two",
                "severity": "Medium",
                "lineno": 20,
            },
        ]

        findings = MythrilFindingMapper.map_all(
            issues=issues,
            request=make_request(),
        )

        assert isinstance(findings, tuple)
        assert len(findings) == 2

    def test_map_all_skips_malformed_issues(
        self,
    ) -> None:
        issues = [
            {
                "title": "Valid issue",
                "severity": "High",
                "lineno": 10,
            },
            {
                "title": "",
                "severity": "High",
                "lineno": 20,
            },
            "invalid",
        ]

        findings = MythrilFindingMapper.map_all(
            issues=issues,
            request=make_request(),
        )

        assert len(findings) == 1
        assert findings[0].title == "Valid issue"

    def test_all_findings_are_mythril_findings(
        self,
    ) -> None:
        issues = [
            {
                "title": "Issue one",
                "severity": "High",
                "lineno": 10,
            },
            {
                "title": "Issue two",
                "severity": "Low",
                "lineno": 20,
            },
        ]

        findings = MythrilFindingMapper.map_all(
            issues=issues,
            request=make_request(),
        )

        assert all(
            finding.analyzer is AnalyzerType.MYTHRIL
            for finding in findings
        )