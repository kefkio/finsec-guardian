from __future__ import annotations

from datetime import datetime
from typing import Optional

from scanner.domain.ports.scan_repository import ScanRepository
from scanner.infrastructure.persistence.models import ScanJob


class DjangoScanRepository(ScanRepository):
    """
    Django ORM implementation of the ScanRepository Port.

    This class encapsulates all persistence logic for ScanJob entities.
    The rest of the application should interact with ScanJobs only
    through this repository rather than directly using the Django ORM.
    """

    def get_by_id(self, scan_id: int) -> Optional[ScanJob]:
        """
        Retrieve a ScanJob by its primary key.
        """
        try:
            return ScanJob.objects.get(pk=scan_id)
        except ScanJob.DoesNotExist:
            return None

    def save(self, scan: ScanJob) -> ScanJob:
        """
        Create or update a ScanJob.

        Django automatically determines whether this is an INSERT
        or UPDATE based on whether the primary key already exists.
        """
        scan.save()
        return scan

    def delete(self, scan_id: int) -> bool:
        """
        Delete a ScanJob.

        Returns:
            True if a record was deleted.
            False otherwise.
        """
        deleted_count, _ = ScanJob.objects.filter(pk=scan_id).delete()
        return deleted_count > 0

    def list_all(self) -> list[ScanJob]:
        """
        Return all ScanJobs.
        """
        return list(
            ScanJob.objects.order_by("-created_at")
        )

    def list_recent(self, limit: int = 10) -> list[ScanJob]:
        """
        Return the most recent ScanJobs.
        """
        return list(
            ScanJob.objects.order_by("-created_at")[:limit]
        )

    def find_by_status(self, status: str) -> list[ScanJob]:
        """
        Find ScanJobs with the specified status.
        """
        return list(
            ScanJob.objects.filter(status=status)
        )

    def find_by_contract_name(self, contract_name: str) -> list[ScanJob]:
        """
        Find ScanJobs by contract name.
        """
        return list(
            ScanJob.objects.filter(contract_name=contract_name)
        )

    def find_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> list[ScanJob]:
        """
        Find ScanJobs created within a date range.
        """
        return list(
            ScanJob.objects.filter(
                created_at__range=(start_date, end_date)
            )
        )

    def find_by_hash(
        self,
        source_hash: str,
    ) -> Optional[ScanJob]:
        """
        Find a previously scanned contract using its SHA-256 hash.

        This enables duplicate detection and scan caching.
        """
        return (
            ScanJob.objects.filter(
                source_code_hash=source_hash
            )
            .order_by("-created_at")
            .first()
        )

    def exists(self, scan_id: int) -> bool:
        """
        Check whether a ScanJob exists.
        """
        return ScanJob.objects.filter(pk=scan_id).exists()

    def count(self) -> int:
        """
        Return the total number of ScanJobs.
        """
        return ScanJob.objects.count()