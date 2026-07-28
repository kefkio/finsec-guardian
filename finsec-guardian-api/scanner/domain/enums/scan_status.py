from scanner.domain.enums.base import DomainEnum


class ScanStatus(DomainEnum):
    """
    Represents the lifecycle state of a scan job.

    A scan progresses through a well-defined sequence of states,
    from creation to completion or termination.
    """

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        """
        Returns True if the scan has reached a final state.
        """
        return self in (
            ScanStatus.COMPLETED,
            ScanStatus.FAILED,
            ScanStatus.CANCELLED,
        )

    @property
    def is_active(self) -> bool:
        """
        Returns True if the scan is actively being processed.
        """
        return self in (
            ScanStatus.QUEUED,
            ScanStatus.RUNNING,
        )

    @property
    def can_start(self) -> bool:
        """
        Returns True if the scan can begin execution.
        """
        return self in (
            ScanStatus.PENDING,
            ScanStatus.QUEUED,
        )

    @property
    def completed_successfully(self) -> bool:
        """
        Returns True if the scan completed successfully.
        """
        return self is ScanStatus.COMPLETED

    @property
    def completed_unsuccessfully(self) -> bool:
        """
        Returns True if the scan ended unsuccessfully.
        """
        return self in (
            ScanStatus.FAILED,
            ScanStatus.CANCELLED,
        )