from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from django.utils import timezone

from scanner.domain.entities import Entity
from scanner.domain.entities.finding import Finding
from scanner.domain.entities.smart_contract import SmartContract
from scanner.domain.enums import ScanStatus, Severity, RiskLevel
from scanner.domain.exceptions import DomainValidationError




@dataclass(slots=True)
class Scan(Entity):
    """
    Aggregate root representing a security scan performed on a smart contract.

    A Scan owns its Findings and is responsible for enforcing all aggregate
    invariants, including:

    - Findings belong to this Scan.
    - Finding fingerprints are unique.
    - Findings cannot be modified once the Scan reaches a terminal state.
    """

    smart_contract: SmartContract
    status: ScanStatus = ScanStatus.PENDING

    _findings: list[Finding] = field(default_factory=list, repr=False)

    started_at: datetime | None = None
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.smart_contract, SmartContract):
            raise DomainValidationError(
                "Scan must be associated with a valid SmartContract."
            )

        self._ensure_findings_validity()

    # ==========================================================
    # Lifecycle
    # ==========================================================

    def queue(self) ->None:
        if self.status is not ScanStatus.PENDING:
            raise DomainValidationError(
                "Scan can only be queued from the PENDING state."
            )

        self.status = ScanStatus.QUEUED

    def start(self) -> None:
        if not self.status.can_start:
            raise DomainValidationError(
                "Scan can only be started from PENDING or QUEUED states."
            )

        self.status = ScanStatus.RUNNING
        self.started_at = timezone.now()

    def complete(self) -> None:
        if self.status is not ScanStatus.RUNNING:
            raise DomainValidationError(
                "Scan can only be completed from the RUNNING state."
            )

        self.status = ScanStatus.COMPLETED
        self.completed_at = timezone.now()

    def fail(self) -> None:
        """
        Marks the scan as failed.
        """
        if self.status is not ScanStatus.RUNNING:
            raise DomainValidationError(
            "Only a running scan may fail."
        )

        self.status = ScanStatus.FAILED
        self.completed_at = timezone.now()

    def cancel(self) -> None:
        if self.status not in (
            ScanStatus.PENDING,
            ScanStatus.QUEUED,
            ScanStatus.RUNNING,
        ):
            raise DomainValidationError(
                "Scan can only be cancelled from PENDING, QUEUED, or RUNNING states."
            )

        self.status = ScanStatus.CANCELLED
        self.completed_at = timezone.now()



    # ==========================================================
    # Aggregate Invariants
    # ==========================================================

    def _ensure_findings_mutable(self) -> None:
        """
        Findings cannot change after the scan reaches a terminal state.
        """
        if self.status.is_terminal:
            raise DomainValidationError(
                "Findings cannot be modified once the scan reaches a terminal state."
            )

    def _ensure_findings_validity(self) -> None:
        """
        Validate findings supplied during construction.
        """
        fingerprints: set[str] = set()

        for finding in self._findings:
            self._validate_finding(finding, fingerprints)

    def _validate_finding(
        self,
        finding: Finding,
        fingerprints: set[str],
    ) -> None:
        """
        Validate a finding against aggregate invariants.

        The supplied fingerprint set is updated upon successful validation,
        allowing duplicate detection across both existing and incoming findings.
        """
        if not isinstance(finding, Finding):
            raise DomainValidationError(
                "Only instances of Finding are allowed."
            )


        if finding.fingerprint in fingerprints:
            raise DomainValidationError(
                f"Duplicate fingerprint detected: {finding.fingerprint}"
            )

        fingerprints.add(finding.fingerprint)

        # ==========================================================
    # State Properties
    # ==========================================================

    @property
    def is_running(self) -> bool:
        return self.status is ScanStatus.RUNNING

    @property
    def is_completed(self) -> bool:
        return self.status is ScanStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        return self.status is ScanStatus.FAILED

    @property
    def is_terminal(self) -> bool:
        return self.status.is_terminal

    # ==========================================================
    # Findings
    # ==========================================================

    @property
    def findings(self) -> tuple[Finding, ...]:
        """
        Expose findings as an immutable collection.
        """
        return tuple(self._findings)

    def add_finding(self, finding: Finding) -> None:
        """
        Add a single finding.
        """
        self._ensure_findings_mutable()

        fingerprints = {
            existing.fingerprint
            for existing in self._findings
        }

        self._validate_finding(finding, fingerprints)

        self._findings.append(finding)

    def remove_finding(self, fingerprint: str) -> None:
        """
        Remove a finding by fingerprint.
        """
        self._ensure_findings_mutable()

        for finding in self._findings:
            if finding.fingerprint == fingerprint:
                self._findings.remove(finding)
                return

        raise DomainValidationError("Finding not found.")

    def replace_findings(self, findings: list[Finding]) -> None:
        """
        Atomically replace all findings.

        The scan is only mutated after every incoming finding has been
        successfully validated.
        """
        self._ensure_findings_mutable()

        fingerprints: set[str] = set()
        validated: list[Finding] = []

        for finding in findings:
            self._validate_finding(finding, fingerprints)
            validated.append(finding)

        self._findings = validated

    def merge_findings(self, findings: list[Finding]) -> None:
        """
        Atomically merge findings into the aggregate.

        Validation is completed before any state mutation occurs,
        ensuring the aggregate is never left partially updated.
        """
        self._ensure_findings_mutable()

        fingerprints = {
            existing.fingerprint
            for existing in self._findings
        }

        validated: list[Finding] = []

        for finding in findings:
            self._validate_finding(finding, fingerprints)
            validated.append(finding)

        self._findings.extend(validated)

    def clear_findings(self) -> None:
        """
        Remove all findings.
        """
        self._ensure_findings_mutable()
        self._findings.clear()

    @property
    def has_findings(self) -> bool:
        return bool(self._findings)

    @property
    def has_no_findings(self) -> bool:
        return not self._findings

    @property
    def duration(self) -> float | None:
        """
        Returns the duration of the scan in seconds, or None if the scan
        has not completed.
        """
        if self.started_at is None:
            raise DomainValidationError(
                "Scan has not started."
            )
        end = self.completed_at or timezone.now()
        return (end - self.started_at).total_seconds()

    @property
    def critical_findings(self) -> int:
        return sum(
        finding.severity is Severity.CRITICAL
        for finding in self._findings
    )

    @property
    def high_findings(self) -> int:
        return sum(
            finding.severity is Severity.HIGH
            for finding in self._findings
        )

    @property
    def medium_findings(self) -> int:
        return sum(
            finding.severity is Severity.MEDIUM
            for finding in self._findings
        )

    @property
    def low_findings(self) -> int:
        return sum(
            finding.severity is Severity.LOW
            for finding in self._findings
        )

    @property
    def overall_risk(self) -> RiskLevel:
        """
        Returns the highest risk level identified during the scan.

        If the scan contains no findings, the overall risk defaults
        to VERY_LOW.
        """
        if not self._findings:
            return RiskLevel.VERY_LOW

        return max(
            (
                finding.risk_level
                for finding in self._findings
            ),
            key=lambda risk: risk.priority,
        )

    # ==========================================================
    # Derived Properties
    # ==========================================================

    @property
    def finding_count(self) -> int:
        """Return the total number of findings."""
        return len(self._findings)