from __future__ import annotations

from uuid import UUID

from django.db import transaction

from scanner.domain.entities.scan import Scan
from scanner.domain.enums import ScanStatus
from scanner.domain.ports.scan_repository import ScanRepository
from scanner.infrastructure.persistence.mappers import PersistenceMapper
from scanner.infrastructure.persistence.models_v2 import (
    FindingRecord,
    ScanRecord,
)


class DjangoScanRepository(ScanRepository):
    """
    Django ORM implementation of the V2 ScanRepository port.

    The repository persists and reconstructs the Scan aggregate through
    ScanRecord and FindingRecord. Domain objects never escape through
    the infrastructure boundary.
    """

    # ==========================================================
    # Save
    # ==========================================================

    def save(self, scan: Scan) -> Scan:
        """
        Persist the complete Scan aggregate atomically.

        The scan record and all associated findings are persisted in
        a single transaction.
        """
        self._validate_scan(scan)

        with transaction.atomic():
            scan_record = PersistenceMapper.scan_to_record(scan)
            scan_record.save()

            self._replace_findings(
                scan_record=scan_record,
                scan=scan,
            )

        return scan

    # ==========================================================
    # Get
    # ==========================================================

    def get_by_id(self, scan_id: UUID) -> Scan | None:
        """
        Retrieve a Scan aggregate by its domain identifier.
        """
        record = (
            ScanRecord.objects
            .prefetch_related("findings")
            .filter(pk=scan_id)
            .first()
        )

        if record is None:
            return None

        return PersistenceMapper.record_to_scan(record)

    def get_by_hash(
        self,
        source_hash: str,
    ) -> Scan | None:
        """
        Retrieve the most recently persisted Scan for a source hash.
        """
        record = (
            ScanRecord.objects
            .prefetch_related("findings")
            .filter(source_hash=source_hash)
            .order_by("-created_at", "-id")
            .first()
        )

        if record is None:
            return None

        return PersistenceMapper.record_to_scan(record)

    def get_by_status(
        self,
        status: ScanStatus,
    ) -> tuple[Scan, ...]:
        """
        Retrieve all scans with the supplied lifecycle status.
        """
        self._validate_status(status)

        records = (
            ScanRecord.objects
            .prefetch_related("findings")
            .filter(status=status.value)
            .order_by("-created_at", "-id")
        )

        return tuple(
            PersistenceMapper.record_to_scan(record)
            for record in records
        )

    # ==========================================================
    # Update
    # ==========================================================

    def update(self, scan: Scan) -> Scan:
        """
        Persist the current state of an existing Scan aggregate.

        The aggregate's persisted findings are replaced atomically
        with its current findings.
        """
        self._validate_scan(scan)

        with transaction.atomic():
            try:
                scan_record = ScanRecord.objects.get(
                    pk=scan.id,
                )
            except ScanRecord.DoesNotExist as exc:
                raise ValueError(
                    f"Scan {scan.id} does not exist."
                ) from exc

            mapped_record = PersistenceMapper.scan_to_record(
                scan,
            )

            # Preserve the existing persistence timestamp while
            # allowing Django to update updated_at.
            scan_record.filename = mapped_record.filename
            scan_record.contract_name = mapped_record.contract_name
            scan_record.source_code = mapped_record.source_code
            scan_record.compiler_version = (
                mapped_record.compiler_version
            )
            scan_record.language = mapped_record.language
            scan_record.source_hash = mapped_record.source_hash
            scan_record.status = mapped_record.status
            scan_record.started_at = mapped_record.started_at
            scan_record.completed_at = mapped_record.completed_at

            scan_record.save()

            self._replace_findings(
                scan_record=scan_record,
                scan=scan,
            )

        return scan

    # ==========================================================
    # Delete
    # ==========================================================

    def delete(self, scan_id: UUID) -> None:
        """
        Delete a Scan aggregate.

        FindingRecord rows are removed through the CASCADE
        relationship defined on FindingRecord.scan.
        """
        ScanRecord.objects.filter(
            pk=scan_id,
        ).delete()

    # ==========================================================
    # Recent
    # ==========================================================

    def list_recent(
        self,
        limit: int = 10,
    ) -> tuple[Scan, ...]:
        """
        Return the most recently persisted scans.
        """
        if limit < 1:
            return ()

        records = (
            ScanRecord.objects
            .prefetch_related("findings")
            .order_by("-created_at", "-id")[:limit]
        )

        return tuple(
            PersistenceMapper.record_to_scan(record)
            for record in records
        )

    # ==========================================================
    # Internal persistence helpers
    # ==========================================================

    @staticmethod
    def _replace_findings(
        *,
        scan_record: ScanRecord,
        scan: Scan,
    ) -> None:
        """
        Replace all persisted findings for a Scan.

        This operates directly on persistence state. It does not mutate
        the domain aggregate and therefore remains valid for terminal
        Scan instances during persistence/repository updates.
        """
        scan_record.findings.all().delete()

        records = [
            PersistenceMapper.finding_to_record(
                finding=finding,
                scan_record=scan_record,
            )
            for finding in scan.findings
        ]

        if records:
            FindingRecord.objects.bulk_create(
                records,
            )

    # ==========================================================
    # Validation
    # ==========================================================

    @staticmethod
    def _validate_scan(scan: Scan) -> None:
        if not isinstance(scan, Scan):
            raise TypeError(
                "scan must be a Scan."
            )

    @staticmethod
    def _validate_status(status: ScanStatus) -> None:
        if not isinstance(status, ScanStatus):
            raise TypeError(
                "status must be a ScanStatus."
            )