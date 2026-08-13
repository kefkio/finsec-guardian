from __future__ import annotations

import hashlib

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class SolidityVersion(models.Model):
    """Track supported Solidity compiler versions."""

    version = models.CharField(
        max_length=20,
        unique=True,
    )

    is_default = models.BooleanField(
        default=False,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ["-version"]

    def __str__(self) -> str:
        return f"Solidity {self.version}"


class ScanJob(models.Model):
    """
    Legacy V1 persistence model.

    These fields remain intact while the V2 persistence model is
    introduced alongside the legacy implementation.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("compiling", "Compiling"),
        ("analyzing", "Analyzing"),
        ("complete", "Complete"),
        ("failed", "Failed"),
    ]

    # ==========================================================
    # Core scanning data
    # ==========================================================

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    source_code = models.TextField()

    source_code_hash = models.CharField(
        max_length=64,
        db_index=True,
    )

    contract_name = models.CharField(
        max_length=255,
        blank=True,
    )

    contract_address = models.CharField(
        max_length=42,
        blank=True,
        db_index=True,
        help_text=(
            "Optional 0x-prefixed Ethereum address "
            "for on-chain intelligence"
        ),
    )

    # ==========================================================
    # Legacy source/file metadata
    # ==========================================================

    source_type = models.CharField(
        choices=[
            ("text", "Text Input"),
            ("upload", "Uploaded File"),
        ],
        default="text",
        max_length=20,
    )

    syntax_valid = models.BooleanField(
        default=False,
    )

    uploaded_file_size = models.PositiveIntegerField(
        default=0,
    )

    uploaded_filename = models.CharField(
        blank=True,
        max_length=255,
    )

    # ==========================================================
    # Compilation metadata
    # ==========================================================

    solidity_version = models.ForeignKey(
        SolidityVersion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    compiled_abi = models.JSONField(
        null=True,
        blank=True,
    )

    compiled_bytecode = models.TextField(
        blank=True,
    )

    compilation_error = models.TextField(
        blank=True,
    )

    # ==========================================================
    # Status tracking
    # ==========================================================

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    progress_percentage = models.IntegerField(
        default=0,
    )

    # ==========================================================
    # Timestamps
    # ==========================================================

    created_at = models.DateTimeField(
        auto_now_add=True,
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
    # Results metadata
    # ==========================================================

    total_findings = models.IntegerField(
        default=0,
    )

    critical_count = models.IntegerField(
        default=0,
    )

    high_count = models.IntegerField(
        default=0,
    )

    medium_count = models.IntegerField(
        default=0,
    )

    low_count = models.IntegerField(
        default=0,
    )

    info_count = models.IntegerField(
        default=0,
    )

    # ==========================================================
    # Legacy risk metadata
    # ==========================================================

    risk_assessment = models.JSONField(
        blank=True,
        default=dict,
        help_text="Full risk breakdown from RiskScorer",
    )

    risk_score = models.IntegerField(
        default=0,
        help_text="Aggregate risk score 0-100",
    )

    risk_verdict = models.CharField(
        blank=True,
        help_text="CRITICAL/HIGH/MEDIUM/LOW/MINIMAL RISK",
        max_length=30,
    )

    # ==========================================================
    # Audit trail
    # ==========================================================

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    user_agent = models.TextField(
        blank=True,
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["-created_at", "status"],
            ),
            models.Index(
                fields=["user", "-created_at"],
            ),
            models.Index(
                fields=["source_code_hash"],
            ),
        ]

    def __str__(self) -> str:
        return (
            f"ScanJob {self.id}: "
            f"{self.contract_name or 'Unnamed'} "
            f"({self.status})"
        )

    def save(self, *args, **kwargs):
        """Automatically compute the source code hash."""
        if self.source_code and not self.source_code_hash:
            self.source_code_hash = hashlib.sha256(
                self.source_code.encode("utf-8")
            ).hexdigest()

        super().save(*args, **kwargs)

    def update_finding_counts(self) -> None:
        """Update finding count summaries."""
        self.total_findings = self.findings.count()

        for severity in (
            "critical",
            "high",
            "medium",
            "low",
            "info",
        ):
            count = self.findings.filter(
                severity=severity,
            ).count()

            setattr(
                self,
                f"{severity}_count",
                count,
            )

        self.save(
            update_fields=[
                "total_findings",
                "critical_count",
                "high_count",
                "medium_count",
                "low_count",
                "info_count",
            ]
        )


class FindingCategory(models.Model):
    """Categorize findings by type."""

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    swc_id = models.CharField(
        max_length=20,
        blank=True,
    )

    description = models.TextField(
        blank=True,
    )

    class Meta:
        verbose_name_plural = "Finding Categories"

    def __str__(self) -> str:
        return f"{self.name} ({self.swc_id})"


class Finding(models.Model):
    """Legacy V1 finding persistence model."""

    SEVERITY_CHOICES = [
        ("critical", "Critical"),
        ("high", "High"),
        ("medium", "Medium"),
        ("low", "Low"),
        ("info", "Info"),
    ]

    STATUS_CHOICES = [
        ("new", "New"),
        ("acknowledged", "Acknowledged"),
        ("suppressed", "Suppressed"),
        ("resolved", "Resolved"),
    ]

    # ==========================================================
    # Core finding data
    # ==========================================================

    scan = models.ForeignKey(
        ScanJob,
        related_name="findings",
        on_delete=models.CASCADE,
    )

    category = models.ForeignKey(
        FindingCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # ==========================================================
    # Identification
    # ==========================================================

    swc_id = models.CharField(
        max_length=20,
        blank=True,
        db_index=True,
    )

    title = models.CharField(
        max_length=255,
    )

    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        db_index=True,
    )

    # ==========================================================
    # Description & Guidance
    # ==========================================================

    description = models.TextField()

    code_snippet = models.TextField(
        blank=True,
    )

    recommendation = models.TextField(
        blank=True,
    )

    reference_url = models.URLField(
        blank=True,
    )

    # ==========================================================
    # Location Information
    # ==========================================================

    line_number = models.IntegerField(
        null=True,
        blank=True,
    )

    line_start = models.IntegerField(
        null=True,
        blank=True,
    )

    line_end = models.IntegerField(
        null=True,
        blank=True,
    )

    column = models.IntegerField(
        null=True,
        blank=True,
    )

    # ==========================================================
    # Analysis metadata
    # ==========================================================

    confidence = models.IntegerField(
        default=100,
        help_text="Confidence 0-100",
    )

    impact_score = models.IntegerField(
        default=0,
        help_text="Impact 0-10",
    )

    # ==========================================================
    # Status & Tracking
    # ==========================================================

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="new",
    )

    is_false_positive = models.BooleanField(
        default=False,
    )

    suppression_reason = models.TextField(
        blank=True,
    )

    # ==========================================================
    # Timestamps
    # ==========================================================

    found_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    # ==========================================================
    # Additional metadata
    # ==========================================================

    tags = models.JSONField(
        default=list,
        blank=True,
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    class Meta:
        ordering = ["-severity", "-found_at"]

        indexes = [
            models.Index(
                fields=["scan", "-severity"],
            ),
            models.Index(
                fields=["swc_id"],
            ),
            models.Index(
                fields=["status"],
            ),
        ]

        unique_together = [
            "scan",
            "swc_id",
            "line_number",
            "title",
        ]

    def __str__(self) -> str:
        return (
            f"{self.severity.upper()}: "
            f"{self.title} "
            f"(Line {self.line_number})"
        )

    def get_risk_score(self) -> int:
        """Calculate the legacy composite risk score."""
        severity_weights = {
            "critical": 100,
            "high": 75,
            "medium": 50,
            "low": 25,
            "info": 5,
        }

        base_score = severity_weights.get(
            self.severity,
            0,
        )

        confidence_factor = self.confidence / 100

        return int(
            base_score * confidence_factor
        )


class SuppressionBaseline(models.Model):
    """Track suppressed findings to avoid reporting duplicates."""

    scan = models.ForeignKey(
        ScanJob,
        related_name="baselines",
        on_delete=models.CASCADE,
    )

    finding = models.ForeignKey(
        Finding,
        on_delete=models.CASCADE,
    )

    suppressed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    reason = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return (
            f"Baseline: {self.finding.title} "
            f"in ScanJob {self.scan.id}"
        )

    def is_expired(self) -> bool:
        return (
            self.expires_at is not None
            and timezone.now() > self.expires_at
        )


class ScanReport(models.Model):
    """Generate and store scan reports."""

    REPORT_TYPES = [
        ("summary", "Summary"),
        ("detailed", "Detailed"),
        ("executive", "Executive"),
    ]

    FORMAT_CHOICES = [
        ("json", "JSON"),
        ("pdf", "PDF"),
        ("html", "HTML"),
    ]

    scan = models.OneToOneField(
        ScanJob,
        on_delete=models.CASCADE,
        related_name="report",
    )

    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPES,
    )

    format = models.CharField(
        max_length=10,
        choices=FORMAT_CHOICES,
    )

    content = models.BinaryField()

    generated_at = models.DateTimeField(
        auto_now_add=True,
    )

    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-generated_at"]

    def __str__(self) -> str:
        return (
            f"Report: {self.scan.contract_name} "
            f"({self.report_type})"
        )
    