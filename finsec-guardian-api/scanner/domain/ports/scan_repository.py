from abc import ABC, abstractmethod


class ScanRepository(ABC):
    """
    Contract for persisting and retrieving ScanJobs.
    """

    @abstractmethod
    def save(self, scan):
        """Persist a ScanJob."""
        pass

    @abstractmethod
    def get_by_id(self, scan_id):
        """Retrieve a ScanJob by its ID."""
        pass

    @abstractmethod
    def get_by_hash(self, source_code_hash):
        """Retrieve a ScanJob by its source code hash."""
        pass

    @abstractmethod
    def get_by_status(self, status):
        """Retrieve ScanJobs by their status."""
        pass

    @abstractmethod
    def get_by_user(self, user_id):
        """Retrieve ScanJobs by the user who initiated them."""
        pass

    @abstractmethod
    def update(self, scan):
        """Update an existing ScanJob."""
        pass

        
    @abstractmethod
    def delete(self, scan_id):
        """Delete a ScanJob."""
        pass

    @abstractmethod
    def list_recent(self, limit=10):
        """Return the most recent ScanJobs."""
        pass