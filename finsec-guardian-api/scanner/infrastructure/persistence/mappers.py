from __future__ import annotations

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
from scanner.infrastructure.persistence.models_v2 import (
    FindingRecord,
    ScanRecord,
)


class PersistenceMapper:
    """
    Maps between V2 domain entities and Django persistence records.

    This mapper contains no business rules and performs no database
    operations. Its responsibility is structural translation only.
    """

    # ==========================================================
    # Scan
    # ==========================================================

    @staticmethod
    def scan_to_record(scan: Scan) -> ScanRecord:
        """
        Convert a domain Scan aggregate into an unsaved ScanRecord.
        """
        return ScanRecord(
            id=scan.id,
            filename=scan.smart_contract.filename,
            contract_name=scan.smart_contract.contract_name,
            source_code=scan.smart_contract.source_code,
            compiler_version=scan.smart_contract.compiler_version,
            language=scan.smart_contract.language,
            source_hash=scan.smart_contract.source_hash,
            status=scan.status.value,
            started_at=scan.started_at,
            completed_at=scan.completed_at,
        )

    @staticmethod
    def record_to_scan(record: ScanRecord) -> Scan:
        """
        Reconstruct a Scan aggregate from a persisted ScanRecord.

        Findings are supplied during aggregate construction rather than
        through a lifecycle mutation method. This is necessary because
        terminal scans correctly prohibit post-construction finding
        mutations.
        """
        contract = SmartContract(
            filename=record.filename,
            contract_name=record.contract_name,
            source_code=record.source_code,
            compiler_version=record.compiler_version,
            language=record.language,
            source_hash=record.source_hash,
        )

        findings = [
            PersistenceMapper.record_to_finding(
                finding_record,
            )
            for finding_record in record.findings.all()
        ]

        scan = Scan(
            smart_contract=contract,
            status=ScanStatus(record.status),
            _findings=findings,
            started_at=record.started_at,
            completed_at=record.completed_at,
        )

        # Preserve domain identity.
        scan.id = record.id

        return scan

    # ==========================================================
    # Finding
    # ==========================================================

    @staticmethod
    def finding_to_record(
        finding: Finding,
        scan_record: ScanRecord,
    ) -> FindingRecord:
        """
        Convert a domain Finding into an unsaved FindingRecord.
        """
        return FindingRecord(
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

    @staticmethod
    def record_to_finding(
        record: FindingRecord,
    ) -> Finding:
        """
        Reconstruct a domain Finding from a persisted FindingRecord.
        """
        location = SourceLocation(
            filename=record.filename,
            line=record.line,
            column=record.column,
            end_line=record.end_line,
            end_column=record.end_column,
        )

        signature = VulnerabilitySignature(
            record.fingerprint,
        )

        finding = Finding(
            title=record.title,
            description=record.description,
            recommendation=record.recommendation,
            severity=Severity(record.severity),
            confidence=Confidence(record.confidence),
            risk_level=RiskLevel(record.risk_level),
            analyzer=AnalyzerType(record.analyzer),
            location=location,
            signature=signature,
            cwe_id=record.cwe_id,
            swc_id=record.swc_id,
            owasp_category=record.owasp_category,
            cvss_score=record.cvss_score,
            status=FindingStatus(record.status),
            assigned_to=record.assigned_to,
            verified_by=record.verified_by,
            resolved_by=record.resolved_by,
            closed_at=record.closed_at,
        )

        # Preserve domain identity.
        finding.id = record.id

        return finding