from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from scanner.domain.entities.scan import Scan
from scanner.domain.enums import ScanStatus


class ScanRepository(ABC):
    """
    Port for persisting and retrieving Scan aggregates.

    Infrastructure implementations may use Django ORM, SQL, or another
    persistence mechanism. The domain and application layers depend only
    on this abstraction.
    """

    @abstractmethod
    def save(self, scan: Scan) -> Scan:
        """
        Persist a Scan aggregate and return the persisted aggregate.
        """
        ...

    @abstractmethod
    def get_by_id(self, scan_id: UUID) -> Scan | None:
        """
        Retrieve a Scan by its domain identifier.
        """
        ...

    @abstractmethod
    def get_by_hash(self, source_hash: str) -> Scan | None:
        """
        Retrieve a Scan by the source hash of its SmartContract.
        """
        ...

    @abstractmethod
    def get_by_status(
        self,
        status: ScanStatus,
    ) -> tuple[Scan, ...]:
        """
        Retrieve scans matching the supplied lifecycle status.
        """
        ...

    @abstractmethod
    def update(self, scan: Scan) -> Scan:
        """
        Persist changes to an existing Scan aggregate.
        """
        ...

    @abstractmethod
    def delete(self, scan_id: UUID) -> None:
        """
        Delete a Scan by its domain identifier.
        """
        ...

    @abstractmethod
    def list_recent(
        self,
        limit: int = 10,
    ) -> tuple[Scan, ...]:
        """
        Return the most recently persisted scans.
        """
        ...