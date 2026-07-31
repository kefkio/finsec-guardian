from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Callable, ClassVar

from scanner.domain.entities import Entity
from scanner.domain.entities.finding import Finding
from scanner.domain.entities.smart_contract import SmartContract
from scanner.domain.enums import RiskLevel, ScanStatus, Severity
from scanner.domain.exceptions import DomainValidationError


def _utc_now() -> datetime:
    """
    Default clock for Scan -- the current UTC time.

    Kept as a module-level function (not a lambda) so it has a stable,
    importable identity. Tests that need deterministic timestamps can
    inject a replacement via `Scan(..., clock=lambda: fixed_time)`.
    """
    return datetime.now(UTC)


@dataclass(slots=True)
class Scan(Entity):
    """
    Aggregate root representing a security scan performed on a smart contract.

    A Scan owns its Findings and is solely responsible for enforcing all
    aggregate invariants:

    - The Scan must be associated with a valid SmartContract.
    - Findings must belong to this Scan (see note on `scan_id` below).
    - Finding fingerprints must be unique within the Scan.
    - Findings cannot be added, removed, or otherwise modified once the
      Scan has reached a terminal state (COMPLETED, FAILED, or CANCELLED),
      except via `retry()`.
    - Status transitions must follow the Scan's lifecycle rules; invalid
      transitions raise DomainValidationError.

    No collaborator (repository, service, etc.) should mutate a Scan's
    findings or status directly -- all mutation happens through the
    methods defined here so these invariants can never be bypassed.

    This module has no framework dependency: timestamps come from an
    injectable `clock` rather than `django.utils.timezone`, so the domain
    layer stays framework-agnostic and independently testable.
    """

    smart_contract: SmartContract
    status: ScanStatus = ScanStatus.PENDING

    _findings: list[Finding] = field(default_factory=list, repr=False)

    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Injected time source. Defaults to the system clock; tests or other
    # callers can pass a fixed/fake clock for deterministic timestamps.
    # Excluded from repr/equality since it's infrastructure, not state.
    clock: Callable[[], datetime] = field(
        default=_utc_now, repr=False, compare=False
    )

    # Ordered from highest to lowest severity; used by `overall_risk`.
    # A ClassVar because this ordering is a fact about the Severity/
    # RiskLevel enums, not per-instance state -- every Scan shares it.
    _SEVERITY_RISK_ORDER: ClassVar[tuple[tuple[Severity, RiskLevel], ...]] = (
        (Severity.CRITICAL, RiskLevel.CRITICAL),
        (Severity.HIGH, RiskLevel.HIGH),
        (Severity.MEDIUM, RiskLevel.MEDIUM),
        (Severity.LOW, RiskLevel.LOW),
    )

    # Relative ordering of severities, used by `findings_at_least`.
    _SEVERITY_RANK: ClassVar[dict[Severity, int]] = {
        Severity.LOW: 0,
        Severity.MEDIUM: 1,
        Severity.HIGH: 2,
        Severity.CRITICAL: 3,
    }

    def __post_init__(self) -> None:
        """
        Validate invariants that must hold immediately after construction.

        Raises:
            DomainValidationError: If `smart_contract` is not a valid
                SmartContract, or if any supplied finding violates an
                aggregate invariant (e.g. duplicate fingerprints, or
                ownership by a different scan).
        """
        if not isinstance(self.smart_contract, SmartContract):
            raise DomainValidationError(
                "Scan must be associated with a valid SmartContract."
            )

        fingerprints: set[str] = set()
        for finding in self._findings:
            self._validate_finding(finding, fingerprints)

    # ==========================================================
    # Lifecycle
    # ==========================================================

    def queue(self) -> None:
        """
        Transition the scan from PENDING to QUEUED.

        Raises:
            DomainValidationError: If the scan is not currently PENDING.
        """
        if self.status is not ScanStatus.PENDING:
            raise DomainValidationError(
                "Scan can only be queued from the PENDING state."
            )
        self._set_status(ScanStatus.QUEUED)

    def start(self) -> None:
        """
        Transition the scan to RUNNING and record its start time.

        Raises:
            DomainValidationError: If the scan cannot be started from its
                current state (only PENDING and QUEUED allow starting).
        """
        if not self.status.can_start:
            raise DomainValidationError(
                "Scan can only be started from PENDING or QUEUED states."
            )
        self._set_status(ScanStatus.RUNNING, started=True)

    def complete(self) -> None:
        """
        Transition the scan to COMPLETED and record its completion time.

        Raises:
            DomainValidationError: If the scan is not currently RUNNING,
                or if it has no `started_at` (which would indicate it was
                never legitimately started -- this should be unreachable
                via `start()`, but guards against a corrupted aggregate,
                e.g. one rehydrated incorrectly from storage).
        """
        if self.status is not ScanStatus.RUNNING:
            raise DomainValidationError(
                "Scan can only be completed from the RUNNING state."
            )
        if self.started_at is None:
            raise DomainValidationError(
                "Scan cannot be completed without a recorded start time."
            )
        self._set_status(ScanStatus.COMPLETED, completed=True)

    def fail(self) -> None:
        """
        Transition the scan to FAILED and record its completion time.

        Raises:
            DomainValidationError: If the scan is not currently RUNNING.
        """
        if self.status is not ScanStatus.RUNNING:
            raise DomainValidationError("Only a running scan may fail.")
        self._set_status(ScanStatus.FAILED, completed=True)

    def cancel(self) -> None:
        """
        Transition the scan to CANCELLED and record its completion time.

        Raises:
            DomainValidationError: If the scan is not currently PENDING,
                QUEUED, or RUNNING.
        """
        if self.status not in (
            ScanStatus.PENDING,
            ScanStatus.QUEUED,
            ScanStatus.RUNNING,
        ):
            raise DomainValidationError(
                "Scan can only be cancelled from PENDING, QUEUED, or "
                "RUNNING states."
            )
        self._set_status(ScanStatus.CANCELLED, completed=True)

    def retry(self) -> None:
        """
        Reset a terminal, retryable scan back to PENDING for another run.

        Only FAILED or CANCELLED scans may be retried. COMPLETED scans are
        deliberately excluded -- a completed scan's findings are a valid
        historical result, not something to discard; start a new Scan
        against the same SmartContract instead of retrying one in place.

        Retrying clears prior findings and timestamps, since they belong
        to the run that failed or was cancelled, not the one about to
        happen.

        Raises:
            DomainValidationError: If the scan is not FAILED or CANCELLED.
        """
        if self.status not in (ScanStatus.FAILED, ScanStatus.CANCELLED):
            raise DomainValidationError(
                "Only a FAILED or CANCELLED scan can be retried."
            )
        self.status = ScanStatus.PENDING
        self.started_at = None
        self.completed_at = None
        self._findings.clear()

    def _set_status(
        self,
        status: ScanStatus,
        *,
        started: bool = False,
        completed: bool = False,
    ) -> None:
        """
        Apply a validated status transition and its associated timestamps.

        This is a pure bookkeeping helper -- callers are responsible for
        verifying the transition is legal *before* calling this method.
        """
        self.status = status
        if started:
            self.started_at = self.clock()
        if completed:
            self.completed_at = self.clock()

    # ==========================================================
    # Aggregate Invariants
    # ==========================================================

    def _ensure_findings_mutable(self) -> None:
        """
        Guard against mutating findings once the scan is terminal.

        Raises:
            DomainValidationError: If the scan has reached a terminal
                state (COMPLETED, FAILED, or CANCELLED).
        """
        if self.status.is_terminal:
            raise DomainValidationError(
                "Findings cannot be modified once the scan reaches a "
                "terminal state."
            )

    def _validate_finding(self, finding: Finding, fingerprints: set[str]) -> None:
        """
        Validate a single finding against aggregate invariants.

        On success, `finding.fingerprint` is added to `fingerprints` in
        place, so the same set can be threaded through multiple calls to
        accumulate and detect duplicates across a batch.

        NOTE: ownership enforcement below assumes `Finding` may carry an
        optional `scan_id` attribute pointing back at its owning Scan's
        `id` (from `Entity`). If `Finding` doesn't have that attribute
        yet, this check is a no-op; if it's named differently, update the
        `getattr` call accordingly. Without some such field, nothing stops
        a Finding created for one Scan from being attached to another.

        Args:
            finding: The finding to validate.
            fingerprints: Fingerprints already known to the aggregate
                (or batch); mutated in place on success.

        Raises:
            DomainValidationError: If `finding` is not a Finding instance,
                belongs to a different scan, or its fingerprint duplicates
                one already in `fingerprints`.
        """
        if not isinstance(finding, Finding):
            raise DomainValidationError("Only instances of Finding are allowed.")

        owning_scan_id = getattr(finding, "scan_id", None)
        if owning_scan_id is not None and owning_scan_id != self.id:
            raise DomainValidationError(
                f"Finding {finding.fingerprint!r} belongs to a different scan."
            )

        if finding.fingerprint in fingerprints:
            raise DomainValidationError(
                f"Duplicate fingerprint detected: {finding.fingerprint}"
            )

        fingerprints.add(finding.fingerprint)

    def _validate_batch(
        self, findings: list[Finding], fingerprints: set[str]
    ) -> list[Finding]:
        """
        Validate a batch of findings against `fingerprints` and each other.

        Nothing is mutated on `self` -- this only validates and returns the
        findings, so callers can guarantee all-or-nothing application.

        Raises:
            DomainValidationError: If any finding in the batch is invalid.
        """
        validated: list[Finding] = []
        for finding in findings:
            self._validate_finding(finding, fingerprints)
            validated.append(finding)
        return validated

    def _existing_fingerprints(self) -> set[str]:
        """Return the set of fingerprints currently held by this scan."""
        return {finding.fingerprint for finding in self._findings}

    # ==========================================================
    # State Properties
    # ==========================================================

    @property
    def is_pending(self) -> bool:
        return self.status is ScanStatus.PENDING

    @property
    def is_queued(self) -> bool:
        return self.status is ScanStatus.QUEUED

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
    def is_cancelled(self) -> bool:
        return self.status is ScanStatus.CANCELLED

    @property
    def is_terminal(self) -> bool:
        return self.status.is_terminal

    # ==========================================================
    # Findings -- Mutation
    # ==========================================================

    @property
    def findings(self) -> tuple[Finding, ...]:
        """Expose findings as an immutable collection."""
        return tuple(self._findings)

    def get_finding(self, fingerprint: str) -> Finding | None:
        """Return the finding with the given fingerprint, or None."""
        return next(
            (f for f in self._findings if f.fingerprint == fingerprint), None
        )

    def has_finding(self, fingerprint: str) -> bool:
        """Return True if a finding with the given fingerprint exists."""
        return self.get_finding(fingerprint) is not None

    def add_finding(self, finding: Finding) -> None:
        """
        Add a single finding.

        Raises:
            DomainValidationError: If the scan is terminal, `finding` is
                not a Finding instance, or its fingerprint already exists.
        """
        self._ensure_findings_mutable()
        self._validate_finding(finding, self._existing_fingerprints())
        self._findings.append(finding)

    def remove_finding(self, fingerprint: str) -> None:
        """
        Remove a finding by fingerprint.

        Raises:
            DomainValidationError: If the scan is terminal or no finding
                with the given fingerprint exists.
        """
        self._ensure_findings_mutable()

        finding = self.get_finding(fingerprint)
        if finding is None:
            raise DomainValidationError(f"Finding not found: {fingerprint}")

        self._findings.remove(finding)

    def replace_findings(self, findings: list[Finding]) -> None:
        """
        Atomically replace all findings.

        Every incoming finding is validated (including uniqueness against
        the rest of the batch) before the scan is mutated, so the
        aggregate is never left in a partially-updated state.

        Raises:
            DomainValidationError: If the scan is terminal or any finding
                in `findings` is invalid.
        """
        self._ensure_findings_mutable()
        self._findings = self._validate_batch(findings, set())

    def merge_findings(self, findings: list[Finding]) -> None:
        """
        Atomically merge findings into the existing set.

        Validation (against both existing findings and the rest of the
        batch) is completed before any state mutation occurs.

        Raises:
            DomainValidationError: If the scan is terminal or any finding
                in `findings` is invalid.
        """
        self._ensure_findings_mutable()
        validated = self._validate_batch(findings, self._existing_fingerprints())
        self._findings.extend(validated)

    def clear_findings(self) -> None:
        """
        Remove all findings.

        Raises:
            DomainValidationError: If the scan is terminal.
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
    def finding_count(self) -> int:
        """Return the total number of findings."""
        return len(self._findings)

    # ==========================================================
    # Findings -- Queries
    # ==========================================================

    def findings_by_severity(self, severity: Severity) -> tuple[Finding, ...]:
        """Return findings that exactly match the given severity."""
        return tuple(f for f in self._findings if f.severity is severity)

    def findings_at_least(self, severity: Severity) -> tuple[Finding, ...]:
        """
        Return findings at or above the given severity.

        e.g. `findings_at_least(Severity.HIGH)` returns HIGH and CRITICAL.
        """
        threshold = self._SEVERITY_RANK[severity]
        return tuple(
            f for f in self._findings
            if self._SEVERITY_RANK[f.severity] >= threshold
        )

    def findings_for_rule(self, rule_id: object) -> tuple[Finding, ...]:
        """
        Return findings produced by a given rule.

        ASSUMPTION: `Finding` exposes a `rule_id` attribute. Adjust the
        attribute name below if it's actually called something else
        (e.g. `rule` or `rule_code`).
        """
        return tuple(f for f in self._findings if f.rule_id == rule_id)

    def findings_for_file(self, file_path: object) -> tuple[Finding, ...]:
        """
        Return findings located in a given file.

        ASSUMPTION: `Finding` exposes a `file_path` attribute. Adjust the
        attribute name below if it's actually called something else
        (e.g. `location.file` or `path`).
        """
        return tuple(f for f in self._findings if f.file_path == file_path)

    # ==========================================================
    # Scan Statistics
    # ==========================================================

    def _count_by_severity(self, severity: Severity) -> int:
        """Count findings matching the given severity."""
        return sum(finding.severity is severity for finding in self._findings)

    @property
    def critical_findings(self) -> int:
        return self._count_by_severity(Severity.CRITICAL)

    @property
    def high_findings(self) -> int:
        return self._count_by_severity(Severity.HIGH)

    @property
    def medium_findings(self) -> int:
        return self._count_by_severity(Severity.MEDIUM)

    @property
    def low_findings(self) -> int:
        return self._count_by_severity(Severity.LOW)

    @property
    def has_critical_findings(self) -> bool:
        return self.critical_findings > 0

    @property
    def has_blocking_findings(self) -> bool:
        """Return True if any finding is HIGH or CRITICAL severity."""
        return any(
            finding.severity in (Severity.CRITICAL, Severity.HIGH)
            for finding in self._findings
        )

    # ==========================================================
    # Risk Computation
    # ==========================================================

    @property
    def overall_risk(self) -> RiskLevel:
        """
        Return the overall risk level of the scan based on its findings.

        The overall risk is the RiskLevel corresponding to the highest
        severity present among the scan's findings. If there are no
        findings, the overall risk is LOW.
        """
        for severity, risk in self._SEVERITY_RISK_ORDER:
            if self._count_by_severity(severity):
                return risk
        return RiskLevel.LOW

    @property
    def is_high_risk(self) -> bool:
        """Return True if the overall risk is HIGH or CRITICAL."""
        return self.overall_risk in (RiskLevel.HIGH, RiskLevel.CRITICAL)

    @property
    def can_deploy(self) -> bool:
        """
        Return True if this scan clears the bar for deployment.

        A scan supports deployment only once it has actually finished
        (COMPLETED) and has no blocking (HIGH/CRITICAL) findings. This is
        a deliberately conservative default -- teams that want to allow
        deployment with HIGH findings (but not CRITICAL) should treat
        this as a starting point, not a fixed policy, and override or
        parameterize it as their risk tolerance dictates.
        """
        return self.status is ScanStatus.COMPLETED and not self.has_blocking_findings

    # ==========================================================
    # Duration
    # ==========================================================

    @property
    def duration(self) -> float | None:
        """
        Return the duration of the scan in seconds, or None if it hasn't
        started.

        If the scan has completed, this is the time between `started_at`
        and `completed_at`. If it is still running, this is the elapsed
        time so far (measured against the current time via `clock`).

        This is a query, so it returns None rather than raising when the
        answer is simply "not applicable yet" -- callers that need a hard
        failure for an unstarted scan should check `started_at is None`
        (or `is_pending`) explicitly before calling this.
        """
        if self.started_at is None:
            return None

        end = self.completed_at or self.clock()
        return (end - self.started_at).total_seconds()