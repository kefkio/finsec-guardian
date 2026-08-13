from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from scanner.domain.entities.scan import Scan
from scanner.domain.entities.smart_contract import SmartContract
from scanner.domain.enums import ScanStatus
from scanner.domain.ports.scan_repository import ScanRepository


@pytest.fixture
def smart_contract() -> SmartContract:
    return SmartContract(
        filename="VulnerableBank.sol",
        contract_name="VulnerableBank",
        source_code="contract VulnerableBank {}",
        compiler_version="0.8.20",
    )


@pytest.fixture
def scan(smart_contract: SmartContract) -> Scan:
    return Scan(
        smart_contract=smart_contract,
    )


class TestScanRepository:

    def test_cannot_instantiate_abstract_scan_repository(self) -> None:
        with pytest.raises(TypeError):
            ScanRepository()  # type: ignore[abstract]

    def test_subclass_missing_save_cannot_be_instantiated(self) -> None:
        class IncompleteRepository(ScanRepository):
            def get_by_id(self, scan_id: UUID) -> Scan | None:
                return None

            def get_by_hash(self, source_hash: str) -> Scan | None:
                return None

            def get_by_status(
                self,
                status: ScanStatus,
            ) -> tuple[Scan, ...]:
                return ()

            def update(self, scan: Scan) -> Scan:
                return scan

            def delete(self, scan_id: UUID) -> None:
                pass

            def list_recent(
                self,
                limit: int = 10,
            ) -> tuple[Scan, ...]:
                return ()

        with pytest.raises(TypeError):
            IncompleteRepository()  # type: ignore[abstract]

    def test_subclass_missing_query_method_cannot_be_instantiated(
        self,
    ) -> None:
        class IncompleteRepository(ScanRepository):
            def save(self, scan: Scan) -> Scan:
                return scan

            def update(self, scan: Scan) -> Scan:
                return scan

            def delete(self, scan_id: UUID) -> None:
                pass

            def list_recent(
                self,
                limit: int = 10,
            ) -> tuple[Scan, ...]:
                return ()

        with pytest.raises(TypeError):
            IncompleteRepository()  # type: ignore[abstract]

    def test_valid_concrete_repository_fulfills_contract(
        self,
        scan: Scan,
    ) -> None:
        class InMemoryScanRepository(ScanRepository):
            def __init__(self) -> None:
                self._scans: dict[UUID, Scan] = {}

            def save(self, scan: Scan) -> Scan:
                self._scans[scan.id] = scan
                return scan

            def get_by_id(self, scan_id: UUID) -> Scan | None:
                return self._scans.get(scan_id)

            def get_by_hash(
                self,
                source_hash: str,
            ) -> Scan | None:
                for stored_scan in self._scans.values():
                    if stored_scan.smart_contract.source_hash == source_hash:
                        return stored_scan

                return None

            def get_by_status(
                self,
                status: ScanStatus,
            ) -> tuple[Scan, ...]:
                return tuple(
                    stored_scan
                    for stored_scan in self._scans.values()
                    if stored_scan.status is status
                )

            def update(self, scan: Scan) -> Scan:
                self._scans[scan.id] = scan
                return scan

            def delete(self, scan_id: UUID) -> None:
                self._scans.pop(scan_id, None)

            def list_recent(
                self,
                limit: int = 10,
            ) -> tuple[Scan, ...]:
                return tuple(self._scans.values())[:limit]

        repository = InMemoryScanRepository()

        saved = repository.save(scan)

        assert saved is scan
        assert repository.get_by_id(scan.id) is scan
        assert isinstance(scan.id, UUID)

    def test_get_by_hash_uses_smart_contract_source_hash(
        self,
        scan: Scan,
    ) -> None:
        class InMemoryScanRepository(ScanRepository):
            def __init__(self) -> None:
                self._scans: dict[UUID, Scan] = {}

            def save(self, scan: Scan) -> Scan:
                self._scans[scan.id] = scan
                return scan

            def get_by_id(self, scan_id: UUID) -> Scan | None:
                return self._scans.get(scan_id)

            def get_by_hash(
                self,
                source_hash: str,
            ) -> Scan | None:
                for stored_scan in self._scans.values():
                    if stored_scan.smart_contract.source_hash == source_hash:
                        return stored_scan

                return None

            def get_by_status(
                self,
                status: ScanStatus,
            ) -> tuple[Scan, ...]:
                return tuple(
                    stored_scan
                    for stored_scan in self._scans.values()
                    if stored_scan.status is status
                )

            def update(self, scan: Scan) -> Scan:
                self._scans[scan.id] = scan
                return scan

            def delete(self, scan_id: UUID) -> None:
                self._scans.pop(scan_id, None)

            def list_recent(
                self,
                limit: int = 10,
            ) -> tuple[Scan, ...]:
                return tuple(self._scans.values())[:limit]

        source_hash = "a" * 64
        scan.smart_contract.update_hash(source_hash)

        repository = InMemoryScanRepository()
        repository.save(scan)

        assert repository.get_by_hash(source_hash) is scan
        assert repository.get_by_hash("b" * 64) is None