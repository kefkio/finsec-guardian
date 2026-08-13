from __future__ import annotations

from datetime import datetime, timezone

import pytest

from scanner.domain.entities.finding import Finding, FindingStatus
from scanner.domain.entities.scan import Scan
from scanner.domain.entities.smart_contract import SmartContract
from scanner.domain.enums import (
    AnalyzerType,
    Confidence,
    RiskLevel,
    ScanStatus,
    Severity,
)
from scanner.domain.value_objects.source_location import SourceLocation
from scanner.domain.value_objects.vulnerability_signature import (
    VulnerabilitySignature,
)
from scanner.infrastructure.persistence.mappers import PersistenceMapper
from scanner.infrastructure.persistence.models_v2 import (
    FindingRecord,
    ScanRecord,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def smart_contract() -> SmartContract:
    return SmartContract(
        filename="VulnerableBank.sol",
        contract_name="VulnerableBank",
        source_code="contract VulnerableBank {}",
        compiler_version="0.8.20",
        language="Solidity",
        source_hash="a" * 64,
    )


@pytest.fixture
def finding() -> Finding:
    location = SourceLocation(
        filename="VulnerableBank.sol",
        line=10,
        column=5,
        end_line=14,
        end_column=22,
    )

    return Finding(
        title="Reentrancy",
        description="Potential reentrancy vulnerability.",
        recommendation="Apply the checks-effects-interactions pattern.",
        severity=Severity.HIGH,
        confidence=Confidence.HIGH,
        risk_level=RiskLevel.HIGH,
        analyzer=AnalyzerType.SLITHER,
        location=location,
        signature=VulnerabilitySignature("b" * 64),
        cwe_id="CWE-841",
        swc_id="SWC-107",
        owasp_category="SC05",
        cvss_score=8.1,
        status=FindingStatus.CONFIRMED,
        assigned_to="security-team",
        verified_by="reviewer",
        resolved_by=None,
        closed_at=None,
    )


@pytest.fixture
def scan(
    smart_contract: SmartContract,
    finding: Finding,
) -> Scan:
    return Scan(
        smart_contract=smart_contract,
        status=ScanStatus.COMPLETED,
        started_at=datetime(
            2026,
            8,
            13,
            8,
            0,
            tzinfo=timezone.utc,
        ),
        completed_at=datetime(
            2026,
            8,
            13,
            8,
            5,
            tzinfo=timezone.utc,
        ),
        _findings=[finding],
    )


class TestPersistenceMapperScan:

    def test_scan_to_record_preserves_identity_and_contract_data(
        self,
        scan: Scan,
    ) -> None:
        record = PersistenceMapper.scan_to_record(scan)

        assert isinstance(record, ScanRecord)
        assert record.id == scan.id
        assert record.filename == "VulnerableBank.sol"
        assert record.contract_name == "VulnerableBank"
        assert record.source_code == "contract VulnerableBank {}"
        assert record.compiler_version == "0.8.20"
        assert record.language == "Solidity"
        assert record.source_hash == "a" * 64
        assert record.status == "completed"
        assert record.started_at == scan.started_at
        assert record.completed_at == scan.completed_at

    def test_record_to_scan_preserves_identity_and_contract_data(
        self,
        scan: Scan,
    ) -> None:
        record = PersistenceMapper.scan_to_record(scan)

        # Persist the record and its finding so the reverse mapper
        # can load the aggregate through the real Django relation.
        record.save()

        for finding in scan.findings:
            finding_record = PersistenceMapper.finding_to_record(
                finding,
                record,
            )
            finding_record.save()

        record.refresh_from_db()

        restored = PersistenceMapper.record_to_scan(record)

        assert isinstance(restored, Scan)
        assert restored.id == scan.id
        assert restored.status is ScanStatus.COMPLETED
        assert restored.started_at == scan.started_at
        assert restored.completed_at == scan.completed_at

        assert restored.smart_contract.filename == (
            scan.smart_contract.filename
        )
        assert restored.smart_contract.contract_name == (
            scan.smart_contract.contract_name
        )
        assert restored.smart_contract.source_code == (
            scan.smart_contract.source_code
        )
        assert restored.smart_contract.compiler_version == (
            scan.smart_contract.compiler_version
        )
        assert restored.smart_contract.language == (
            scan.smart_contract.language
        )
        assert restored.smart_contract.source_hash == (
            scan.smart_contract.source_hash
        )


class TestPersistenceMapperFinding:

    def test_finding_to_record_preserves_domain_fields(
        self,
        finding: Finding,
    ) -> None:
        scan_record = ScanRecord.objects.create(
            id=None,
            filename="VulnerableBank.sol",
            contract_name="VulnerableBank",
            source_code="contract VulnerableBank {}",
            compiler_version="0.8.20",
            language="Solidity",
            source_hash="a" * 64,
            status=ScanRecord.Status.COMPLETED,
        )

        record = PersistenceMapper.finding_to_record(
            finding,
            scan_record,
        )

        assert isinstance(record, FindingRecord)
        assert record.id == finding.id
        assert record.scan is scan_record

        assert record.title == finding.title
        assert record.description == finding.description
        assert record.recommendation == finding.recommendation

        assert record.severity == finding.severity.value
        assert record.confidence == finding.confidence.value
        assert record.risk_level == finding.risk_level.value
        assert record.analyzer == finding.analyzer.value

        assert record.fingerprint == finding.signature.value

        assert record.filename == finding.location.filename
        assert record.line == finding.location.line
        assert record.column == finding.location.column
        assert record.end_line == finding.location.end_line
        assert record.end_column == finding.location.end_column

        assert record.cwe_id == finding.cwe_id
        assert record.swc_id == finding.swc_id
        assert record.owasp_category == finding.owasp_category
        assert record.cvss_score == finding.cvss_score

        assert record.status == finding.status.value
        assert record.assigned_to == finding.assigned_to
        assert record.verified_by == finding.verified_by
        assert record.resolved_by == finding.resolved_by
        assert record.closed_at == finding.closed_at

    def test_record_to_finding_preserves_identity_and_domain_fields(
        self,
        finding: Finding,
    ) -> None:
        scan_record = ScanRecord.objects.create(
            filename="VulnerableBank.sol",
            contract_name="VulnerableBank",
            source_code="contract VulnerableBank {}",
            compiler_version="0.8.20",
            language="Solidity",
            source_hash="a" * 64,
            status=ScanRecord.Status.COMPLETED,
        )

        finding_record = FindingRecord.objects.create(
            id=finding.id,
            scan=scan_record,
            title=finding.title,
            description=finding.description,
            recommendation=finding.recommendation,
            severity=finding.severity.value,
            confidence=finding.confidence.value,
            risk_level=finding.risk_level.value,
            analyzer=finding.analyzer.value,
            fingerprint=finding.signature.value,
            filename=finding.location.filename,
            line=finding.location.line,
            column=finding.location.column,
            end_line=finding.location.end_line,
            end_column=finding.location.end_column,
            cwe_id=finding.cwe_id,
            swc_id=finding.swc_id,
            owasp_category=finding.owasp_category,
            cvss_score=finding.cvss_score,
            status=finding.status.value,
            assigned_to=finding.assigned_to,
            verified_by=finding.verified_by,
            resolved_by=finding.resolved_by,
            closed_at=finding.closed_at,
        )

        restored = PersistenceMapper.record_to_finding(
            finding_record,
        )

        assert isinstance(restored, Finding)
        assert restored.id == finding.id

        assert restored.title == finding.title
        assert restored.description == finding.description
        assert restored.recommendation == finding.recommendation

        assert restored.severity is finding.severity
        assert restored.confidence is finding.confidence
        assert restored.risk_level is finding.risk_level
        assert restored.analyzer is finding.analyzer
        assert restored.status is finding.status

        assert restored.signature == finding.signature

        assert restored.location == finding.location

        assert restored.cwe_id == finding.cwe_id
        assert restored.swc_id == finding.swc_id
        assert restored.owasp_category == finding.owasp_category
        assert restored.cvss_score == finding.cvss_score

        assert restored.assigned_to == finding.assigned_to
        assert restored.verified_by == finding.verified_by
        assert restored.resolved_by == finding.resolved_by
        assert restored.closed_at == finding.closed_at

    def test_finding_round_trip_preserves_fingerprint(
        self,
        finding: Finding,
    ) -> None:
        scan_record = ScanRecord.objects.create(
            filename="VulnerableBank.sol",
            contract_name="VulnerableBank",
            source_code="contract VulnerableBank {}",
            status=ScanRecord.Status.COMPLETED,
        )

        record = PersistenceMapper.finding_to_record(
            finding,
            scan_record,
        )
        record.save()

        restored = PersistenceMapper.record_to_finding(
            record,
        )

        assert restored.fingerprint == finding.fingerprint
        assert restored.signature.value == (
            finding.signature.value
        )


class TestPersistenceMapperAggregateRoundTrip:

    def test_scan_round_trip_preserves_findings(
        self,
        scan: Scan,
    ) -> None:
        scan_record = PersistenceMapper.scan_to_record(
            scan,
        )
        scan_record.save()

        for finding in scan.findings:
            finding_record = PersistenceMapper.finding_to_record(
                finding,
                scan_record,
            )
            finding_record.save()

        scan_record.refresh_from_db()

        restored = PersistenceMapper.record_to_scan(
            scan_record,
        )

        assert restored.id == scan.id
        assert restored.finding_count == scan.finding_count
        assert len(restored.findings) == len(scan.findings)

        original = scan.findings[0]
        rebuilt = restored.findings[0]

        assert rebuilt.id == original.id
        assert rebuilt.fingerprint == original.fingerprint
        assert rebuilt.title == original.title
        assert rebuilt.location == original.location
        assert rebuilt.severity is original.severity
        assert rebuilt.confidence is original.confidence
        assert rebuilt.risk_level is original.risk_level
        assert rebuilt.analyzer is original.analyzer