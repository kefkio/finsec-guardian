from __future__ import annotations

import uuid

from django.db import models


class ScanRecord(models.Model):
    """
    Persistence representation of the V2 Scan aggregate.

    This model intentionally mirrors the V2 domain model rather than
    the legacy ScanJob model.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # ==========================================================
    # SmartContract
    # ==========================================================

    filename = models.CharField(
        max_length=500,
    )

    contract_name = models.CharField(
        max_length=255,
    )

    source_code = models.TextField()

    compiler_version = models.CharField(
        max_length=50,
        null=True,
        blank=True,
    )

    language = models.CharField(
        max_length=50,
        default="Solidity",
    )

    source_hash = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_index=True,
    )

    # ==========================================================
    # Scan lifecycle
    # ==========================================================

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    # ==========================================================
    # Persistence timestamps
    # ==========================================================

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "scanner_v2_scan"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["status", "-created_at"],
                name="scan_v2_status_created_idx",
            ),
            models.Index(
                fields=["source_hash", "-created_at"],
                name="scan_v2_source_hash_idx",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"ScanRecord {self.id}: "
            f"{self.contract_name} ({self.status})"
        )


class FindingRecord(models.Model):
    """
    Persistence representation of a V2 Finding entity.
    """

    class Severity(models.TextChoices):
        CRITICAL = "critical", "Critical"
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"
        INFORMATIONAL = "informational", "Informational"

    class Confidence(models.TextChoices):
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"

    class RiskLevel(models.TextChoices):
        CRITICAL = "critical", "Critical"
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"
        VERY_LOW = "very_low", "Very Low"

    class Analyzer(models.TextChoices):
        SLITHER = "slither", "Slither"
        MYTHRIL = "mythril", "Mythril"
        ECHIDNA = "echidna", "Echidna"
        HEURISTIC = "heuristic", "Heuristic"
        MANUAL = "manual", "Manual"

    class Status(models.TextChoices):
        NEW = "new", "New"
        CONFIRMED = "confirmed", "Confirmed"
        FALSE_POSITIVE = "false_positive", "False Positive"
        SUPPRESSED = "suppressed", "Suppressed"
        RESOLVED = "resolved", "Resolved"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    scan = models.ForeignKey(
        ScanRecord,
        related_name="findings",
        on_delete=models.CASCADE,
    )

    # ==========================================================
    # Vulnerability Metadata
    # ==========================================================

    title = models.CharField(
        max_length=200,
    )

    description = models.TextField()

    recommendation = models.TextField()

    # ==========================================================
    # Classification
    # ==========================================================

    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        db_index=True,
    )

    confidence = models.CharField(
        max_length=20,
        choices=Confidence.choices,
    )

    risk_level = models.CharField(
        max_length=20,
        choices=RiskLevel.choices,
        db_index=True,
    )

    analyzer = models.CharField(
        max_length=30,
        choices=Analyzer.choices,
        db_index=True,
    )

    # ==========================================================
    # Canonical Identity
    # ==========================================================

    fingerprint = models.CharField(
        max_length=128,
        db_index=True,
    )

    # ==========================================================
    # Source Location
    # ==========================================================

    filename = models.CharField(
        max_length=500,
    )

    line = models.PositiveIntegerField()

    column = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    end_line = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    end_column = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    # ==========================================================
    # Classification Standards
    # ==========================================================

    cwe_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
    )

    swc_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_index=True,
    )

    owasp_category = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    cvss_score = models.FloatField(
        null=True,
        blank=True,
    )

    # ==========================================================
    # Workflow
    # ==========================================================

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True,
    )

    assigned_to = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    verified_by = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    resolved_by = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    # ==========================================================
    # Audit Metadata
    # ==========================================================

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    closed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "scanner_v2_finding"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["scan", "-severity"],
                name="finding_v2_scan_severity_idx",
            ),
            models.Index(
                fields=["scan", "-created_at"],
                name="finding_v2_scan_created_idx",
            ),
            models.Index(
                fields=["analyzer", "-created_at"],
                name="fndg_v2_analyzer_created_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["scan", "fingerprint"],
                name="finding_v2_scan_fp_unique",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.severity.upper()}: "
            f"{self.title} "
            f"(Line {self.line})"
        )