from __future__ import annotations

from uuid import uuid4

import pytest

from scanner.infrastructure.persistence.models_v2 import (
    FindingRecord,
    ScanRecord,
)


pytestmark = pytest.mark.django_db


class TestScanRecord:

    def test_creates_scan_record_with_uuid_identity(self) -> None:
        scan = ScanRecord.objects.create(
            filename="VulnerableBank.sol",
            contract_name="VulnerableBank",
            source_code="contract VulnerableBank {}",
            compiler_version="0.8.20",
        )

        assert scan.id is not None
        assert scan.pk == scan.id
        assert isinstance(scan.id, type(uuid4()))

    def test_default_status_is_pending(self) -> None:
        scan = ScanRecord.objects.create(
            filename="Test.sol",
            contract_name="Test",
            source_code="contract Test {}",
        )

        assert scan.status == ScanRecord.Status.PENDING

    def test_default_language_is_solidity(self) -> None:
        scan = ScanRecord.objects.create(
            filename="Test.sol",
            contract_name="Test",
            source_code="contract Test {}",
        )

        assert scan.language == "Solidity"

    def test_source_hash_is_nullable(self) -> None:
        scan = ScanRecord.objects.create(
            filename="Test.sol",
            contract_name="Test",
            source_code="contract Test {}",
        )

        assert scan.source_hash is None

    def test_source_hash_can_be_stored_and_looked_up(self) -> None:
        source_hash = "a" * 64

        scan = ScanRecord.objects.create(
            filename="Test.sol",
            contract_name="Test",
            source_code="contract Test {}",
            source_hash=source_hash,
        )

        found = ScanRecord.objects.get(source_hash=source_hash)

        assert found.pk == scan.pk

    def test_lifecycle_timestamps_are_nullable(self) -> None:
        scan = ScanRecord.objects.create(
            filename="Test.sol",
            contract_name="Test",
            source_code="contract Test {}",
        )

        assert scan.started_at is None
        assert scan.completed_at is None

    def test_status_choices_are_complete(self) -> None:
        values = {
            value
            for value, _ in ScanRecord.Status.choices
        }

        assert values == {
            "pending",
            "queued",
            "running",
            "completed",
            "failed",
            "cancelled",
        }


class TestFindingRecord:

    @pytest.fixture
    def scan(self) -> ScanRecord:
        return ScanRecord.objects.create(
            filename="VulnerableBank.sol",
            contract_name="VulnerableBank",
            source_code="contract VulnerableBank {}",
            compiler_version="0.8.20",
            source_hash="a" * 64,
        )

    def test_creates_finding_record_with_uuid_identity(
        self,
        scan: ScanRecord,
    ) -> None:
        finding = FindingRecord.objects.create(
            scan=scan,
            title="Reentrancy",
            description="Potential reentrancy vulnerability.",
            recommendation="Apply the checks-effects-interactions pattern.",
            severity=FindingRecord.Severity.HIGH,
            confidence=FindingRecord.Confidence.HIGH,
            risk_level=FindingRecord.RiskLevel.HIGH,
            analyzer=FindingRecord.Analyzer.SLITHER,
            fingerprint="b" * 64,
            filename="VulnerableBank.sol",
            line=10,
        )

        assert finding.id is not None
        assert finding.pk == finding.id
        assert isinstance(finding.id, type(uuid4()))

    def test_finding_defaults_to_new_status(
        self,
        scan: ScanRecord,
    ) -> None:
        finding = FindingRecord.objects.create(
            scan=scan,
            title="Reentrancy",
            description="Potential reentrancy vulnerability.",
            recommendation="Apply the checks-effects-interactions pattern.",
            severity=FindingRecord.Severity.HIGH,
            confidence=FindingRecord.Confidence.HIGH,
            risk_level=FindingRecord.RiskLevel.HIGH,
            analyzer=FindingRecord.Analyzer.SLITHER,
            fingerprint="c" * 64,
            filename="VulnerableBank.sol",
            line=10,
        )

        assert finding.status == FindingRecord.Status.NEW

    def test_finding_belongs_to_scan(
        self,
        scan: ScanRecord,
    ) -> None:
        finding = FindingRecord.objects.create(
            scan=scan,
            title="Access control",
            description="Missing access control.",
            recommendation="Restrict access.",
            severity=FindingRecord.Severity.MEDIUM,
            confidence=FindingRecord.Confidence.MEDIUM,
            risk_level=FindingRecord.RiskLevel.MEDIUM,
            analyzer=FindingRecord.Analyzer.SLITHER,
            fingerprint="d" * 64,
            filename="VulnerableBank.sol",
            line=20,
        )

        assert finding.scan_id == scan.id
        assert scan.findings.count() == 1
        assert scan.findings.first() == finding

    def test_full_source_location_is_persisted(
        self,
        scan: ScanRecord,
    ) -> None:
        finding = FindingRecord.objects.create(
            scan=scan,
            title="Problem",
            description="Problem description.",
            recommendation="Fix the problem.",
            severity=FindingRecord.Severity.LOW,
            confidence=FindingRecord.Confidence.LOW,
            risk_level=FindingRecord.RiskLevel.LOW,
            analyzer=FindingRecord.Analyzer.HEURISTIC,
            fingerprint="e" * 64,
            filename="VulnerableBank.sol",
            line=10,
            column=5,
            end_line=14,
            end_column=22,
        )

        finding.refresh_from_db()

        assert finding.filename == "VulnerableBank.sol"
        assert finding.line == 10
        assert finding.column == 5
        assert finding.end_line == 14
        assert finding.end_column == 22

    def test_optional_classification_fields_are_nullable(
        self,
        scan: ScanRecord,
    ) -> None:
        finding = FindingRecord.objects.create(
            scan=scan,
            title="Problem",
            description="Problem description.",
            recommendation="Fix the problem.",
            severity=FindingRecord.Severity.LOW,
            confidence=FindingRecord.Confidence.LOW,
            risk_level=FindingRecord.RiskLevel.LOW,
            analyzer=FindingRecord.Analyzer.SLITHER,
            fingerprint="f" * 64,
            filename="VulnerableBank.sol",
            line=10,
        )

        assert finding.cwe_id is None
        assert finding.swc_id is None
        assert finding.owasp_category is None
        assert finding.cvss_score is None

    def test_fingerprint_is_unique(
        self,
        scan: ScanRecord,
    ) -> None:
        fingerprint = "1" * 64

        FindingRecord.objects.create(
            scan=scan,
            title="First finding",
            description="First finding.",
            recommendation="Fix it.",
            severity=FindingRecord.Severity.LOW,
            confidence=FindingRecord.Confidence.LOW,
            risk_level=FindingRecord.RiskLevel.LOW,
            analyzer=FindingRecord.Analyzer.SLITHER,
            fingerprint=fingerprint,
            filename="VulnerableBank.sol",
            line=10,
        )

        with pytest.raises(Exception):
            FindingRecord.objects.create(
                scan=scan,
                title="Second finding",
                description="Second finding.",
                recommendation="Fix it.",
                severity=FindingRecord.Severity.LOW,
                confidence=FindingRecord.Confidence.LOW,
                risk_level=FindingRecord.RiskLevel.LOW,
                analyzer=FindingRecord.Analyzer.SLITHER,
                fingerprint=fingerprint,
                filename="VulnerableBank.sol",
                line=20,
            )

    def test_status_choices_are_complete(self) -> None:
        values = {
            value
            for value, _ in FindingRecord.Status.choices
        }

        assert values == {
            "new",
            "confirmed",
            "false_positive",
            "suppressed",
            "resolved",
        }

    def test_analyzer_choices_are_complete(self) -> None:
        values = {
            value
            for value, _ in FindingRecord.Analyzer.choices
        }

        assert values == {
            "slither",
            "mythril",
            "echidna",
            "heuristic",
            "manual",
        }

    def test_scan_deletion_cascades_to_findings(
        self,
        scan: ScanRecord,
    ) -> None:
        FindingRecord.objects.create(
            scan=scan,
            title="Problem",
            description="Problem description.",
            recommendation="Fix it.",
            severity=FindingRecord.Severity.MEDIUM,
            confidence=FindingRecord.Confidence.MEDIUM,
            risk_level=FindingRecord.RiskLevel.MEDIUM,
            analyzer=FindingRecord.Analyzer.SLITHER,
            fingerprint="2" * 64,
            filename="VulnerableBank.sol",
            line=10,
        )

        scan_id = scan.id

        scan.delete()

        assert not ScanRecord.objects.filter(
            pk=scan_id,
        ).exists()

        assert not FindingRecord.objects.filter(
            fingerprint="2" * 64,
        ).exists()