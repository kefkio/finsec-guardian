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
from scanner.infrastructure.persistence.models_v2 import (
    FindingRecord,
    ScanRecord,
)
from scanner.infrastructure.persistence.repositories import (
    DjangoScanRepository,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def repository() -> DjangoScanRepository:
    return DjangoScanRepository()


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
    return Finding(
        title="Reentrancy",
        description="Potential reentrancy vulnerability.",
        recommendation=(
            "Apply the checks-effects-interactions pattern."
        ),
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
        cwe_id="CWE-841",
        swc_id="SWC-107",
        owasp_category="SC05",
        cvss_score=8.1,
        status=FindingStatus.CONFIRMED,
        assigned_to="security-team",
        verified_by="reviewer",
    )


@pytest.fixture
def scan(
    smart_contract: SmartContract,
    finding: Finding,
) -> Scan:
    return Scan(
        smart_contract=smart_contract,
        status=ScanStatus.RUNNING,
        started_at=datetime(
            2026,
            8,
            13,
            8,
            0,
            tzinfo=timezone.utc,
        ),
        _findings=[finding],
    )


class TestDjangoScanRepository:

    def test_save_persists_scan_and_findings(
        self,
        repository: DjangoScanRepository,
        scan: Scan,
    ) -> None:
        saved = repository.save(scan)

        assert saved.id == scan.id

        assert ScanRecord.objects.filter(
            pk=scan.id,
        ).exists()

        record = ScanRecord.objects.get(
            pk=scan.id,
        )

        assert record.filename == "VulnerableBank.sol"
        assert record.contract_name == "VulnerableBank"
        assert record.source_hash == "a" * 64
        assert record.findings.count() == 1

        finding = record.findings.get()

        assert finding.id == scan.findings[0].id
        assert finding.fingerprint == "b" * 64

    def test_get_by_id_returns_domain_scan(
        self,
        repository: DjangoScanRepository,
        scan: Scan,
    ) -> None:
        repository.save(scan)

        restored = repository.get_by_id(scan.id)

        assert restored is not None
        assert isinstance(restored, Scan)
        assert restored.id == scan.id
        assert restored.smart_contract.filename == (
            scan.smart_contract.filename
        )
        assert restored.smart_contract.source_hash == (
            scan.smart_contract.source_hash
        )
        assert restored.finding_count == 1
        assert restored.findings[0].fingerprint == (
            scan.findings[0].fingerprint
        )

    def test_get_by_id_returns_none_for_missing_scan(
        self,
        repository: DjangoScanRepository,
    ) -> None:
        restored = repository.get_by_id(
            scan_id=scan_id(),
        )

        assert restored is None

    def test_get_by_hash_returns_latest_matching_scan(
        self,
        repository: DjangoScanRepository,
    ) -> None:
        first = Scan(
            smart_contract=SmartContract(
                filename="First.sol",
                contract_name="First",
                source_code="contract First {}",
                source_hash="a" * 64,
            ),
        )

        second = Scan(
            smart_contract=SmartContract(
                filename="Second.sol",
                contract_name="Second",
                source_code="contract Second {}",
                source_hash="a" * 64,
            ),
        )

        repository.save(first)
        repository.save(second)

        restored = repository.get_by_hash("a" * 64)

        assert restored is not None
        assert restored.id == second.id

    def test_get_by_hash_returns_none_when_missing(
        self,
        repository: DjangoScanRepository,
    ) -> None:
        restored = repository.get_by_hash("f" * 64)

        assert restored is None

    def test_get_by_status_returns_matching_scans(
        self,
        repository: DjangoScanRepository,
        scan: Scan,
    ) -> None:
        repository.save(scan)

        another = Scan(
            smart_contract=SmartContract(
                filename="Other.sol",
                contract_name="Other",
                source_code="contract Other {}",
            ),
            status=ScanStatus.PENDING,
        )

        repository.save(another)

        running = repository.get_by_status(
            ScanStatus.RUNNING
        )

        assert len(running) == 1
        assert running[0].id == scan.id

    def test_get_by_status_returns_tuple(
        self,
        repository: DjangoScanRepository,
        scan: Scan,
    ) -> None:
        repository.save(scan)

        result = repository.get_by_status(
            ScanStatus.RUNNING
        )

        assert isinstance(result, tuple)

    def test_update_replaces_findings(
        self,
        repository: DjangoScanRepository,
        scan: Scan,
    ) -> None:
        repository.save(scan)

        scan.replace_findings([])

        updated = repository.update(scan)

        assert updated.id == scan.id

        record = ScanRecord.objects.get(
            pk=scan.id,
        )

        assert record.findings.count() == 0

    def test_update_persists_scan_changes(
        self,
        repository: DjangoScanRepository,
        scan: Scan,
    ) -> None:
        repository.save(scan)

        scan.smart_contract.rename(
            "RenamedBank"
        )

        updated = repository.update(scan)

        assert updated.smart_contract.contract_name == (
            "RenamedBank"
        )

        record = ScanRecord.objects.get(
            pk=scan.id,
        )

        assert record.contract_name == "RenamedBank"

    def test_delete_removes_scan(
        self,
        repository: DjangoScanRepository,
        scan: Scan,
    ) -> None:
        repository.save(scan)

        repository.delete(scan.id)

        assert not ScanRecord.objects.filter(
            pk=scan.id,
        ).exists()

        assert not FindingRecord.objects.filter(
            scan_id=scan.id,
        ).exists()

    def test_delete_is_idempotent_for_missing_scan(
        self,
        repository: DjangoScanRepository,
    ) -> None:
        repository.delete(scan_id())

    def test_list_recent_returns_latest_scans_first(
        self,
        repository: DjangoScanRepository,
    ) -> None:
        first = Scan(
            smart_contract=SmartContract(
                filename="First.sol",
                contract_name="First",
                source_code="contract First {}",
            ),
        )

        second = Scan(
            smart_contract=SmartContract(
                filename="Second.sol",
                contract_name="Second",
                source_code="contract Second {}",
            ),
        )

        repository.save(first)
        repository.save(second)

        recent = repository.list_recent(
            limit=2,
        )

        assert len(recent) == 2
        assert recent[0].id == second.id
        assert recent[1].id == first.id

    def test_list_recent_respects_limit(
        self,
        repository: DjangoScanRepository,
    ) -> None:
        for name in (
            "First",
            "Second",
            "Third",
        ):
            repository.save(
                Scan(
                    smart_contract=SmartContract(
                        filename=f"{name}.sol",
                        contract_name=name,
                        source_code=(
                            f"contract {name} {{}}"
                        ),
                    ),
                )
            )

        recent = repository.list_recent(
            limit=2,
        )

        assert len(recent) == 2


def scan_id():
    from uuid import uuid4

    return uuid4()
