from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import hashlib


class SolidityVersion(models.Model):
    """Track supported Solidity compiler versions"""
    version = models.CharField(max_length=20, unique=True)  # e.g., '0.8.21'
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-version']
    
    def __str__(self):
        return f"Solidity {self.version}"


class ScanJob(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('compiling', 'Compiling'),
        ('analyzing', 'Analyzing'),
        ('complete', 'Complete'),
        ('failed', 'Failed'),
    ]

    # Core scanning data
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    source_code = models.TextField()
    source_code_hash = models.CharField(max_length=64, db_index=True)  # SHA-256 hash
    contract_name = models.CharField(max_length=255, blank=True)
    
    # Compilation metadata
    solidity_version = models.ForeignKey(SolidityVersion, on_delete=models.SET_NULL, null=True, blank=True)
    compiled_abi = models.JSONField(null=True, blank=True)
    compiled_bytecode = models.TextField(blank=True)
    compilation_error = models.TextField(blank=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress_percentage = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Results metadata
    total_findings = models.IntegerField(default=0)
    critical_count = models.IntegerField(default=0)
    high_count = models.IntegerField(default=0)
    medium_count = models.IntegerField(default=0)
    low_count = models.IntegerField(default=0)
    info_count = models.IntegerField(default=0)
    
    # Audit trail
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)  # Store extra data
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at', 'status']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['source_code_hash']),
        ]
    
    def __str__(self):
        return f"ScanJob {self.id}: {self.contract_name or 'Unnamed'} ({self.status})"
    
    def save(self, *args, **kwargs):
        """Automatically compute source code hash"""
        if self.source_code and not self.source_code_hash:
            self.source_code_hash = hashlib.sha256(
                self.source_code.encode('utf-8')
            ).hexdigest()
        super().save(*args, **kwargs)
    
    def update_finding_counts(self):
        """Update finding count summaries"""
        counts = self.findings.values('severity').distinct().count()
        self.total_findings = self.findings.count()
        
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            count = self.findings.filter(severity=severity).count()
            setattr(self, f'{severity}_count', count)
        
        self.save(update_fields=[
            'total_findings', 'critical_count', 'high_count',
            'medium_count', 'low_count', 'info_count'
        ])


class FindingCategory(models.Model):
    """Categorize findings by type (e.g., Reentrancy, Access Control)"""
    name = models.CharField(max_length=100, unique=True)
    swc_id = models.CharField(max_length=20, blank=True)  # e.g., 'SWC-107'
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Finding Categories"
    
    def __str__(self):
        return f"{self.name} ({self.swc_id})"


class Finding(models.Model):
    SEVERITY_CHOICES = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
        ('info', 'Info'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('acknowledged', 'Acknowledged'),
        ('suppressed', 'Suppressed'),
        ('resolved', 'Resolved'),
    ]

    # Core finding data
    scan = models.ForeignKey(ScanJob, related_name='findings', on_delete=models.CASCADE)
    category = models.ForeignKey(FindingCategory, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Identification
    swc_id = models.CharField(max_length=20, blank=True, db_index=True)
    title = models.CharField(max_length=255)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, db_index=True)
    
    # Description & Guidance
    description = models.TextField()
    code_snippet = models.TextField(blank=True)
    recommendation = models.TextField(blank=True)
    reference_url = models.URLField(blank=True)  # Link to SWC registry or docs
    
    # Location Information
    line_number = models.IntegerField(null=True, blank=True)
    line_start = models.IntegerField(null=True, blank=True)
    line_end = models.IntegerField(null=True, blank=True)
    column = models.IntegerField(null=True, blank=True)
    
    # Analysis metadata
    confidence = models.IntegerField(default=100, help_text="Confidence 0-100")  # 0-100%
    impact_score = models.IntegerField(default=0, help_text="Impact 0-10")  # 0-10
    
    # Status & Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    is_false_positive = models.BooleanField(default=False)
    suppression_reason = models.TextField(blank=True)
    
    # Timestamps
    found_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Additional metadata
    tags = models.JSONField(default=list, blank=True)  # e.g., ['gas-optimization', 'logic-error']
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-severity', '-found_at']
        indexes = [
            models.Index(fields=['scan', '-severity']),
            models.Index(fields=['swc_id']),
            models.Index(fields=['status']),
        ]
        unique_together = ['scan', 'swc_id', 'line_number', 'title']

    def __str__(self):
        return f"{self.severity.upper()}: {self.title} (Line {self.line_number})"
    
    def get_risk_score(self):
        """Calculate composite risk score (0-100)"""
        severity_weights = {
            'critical': 100,
            'high': 75,
            'medium': 50,
            'low': 25,
            'info': 5,
        }
        base_score = severity_weights.get(self.severity, 0)
        confidence_factor = self.confidence / 100
        return int(base_score * confidence_factor)


class SuppressionBaseline(models.Model):
    """Track suppressed findings to avoid reporting duplicates"""
    scan = models.ForeignKey(ScanJob, related_name='baselines', on_delete=models.CASCADE)
    finding = models.ForeignKey(Finding, on_delete=models.CASCADE)
    suppressed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Baseline: {self.finding.title} in ScanJob {self.scan.id}"
    
    def is_expired(self):
        """Check if suppression has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class ScanReport(models.Model):
    """Generate and store scan reports (PDF, JSON, etc.)"""
    REPORT_TYPES = [
        ('summary', 'Summary'),
        ('detailed', 'Detailed'),
        ('executive', 'Executive'),
    ]
    
    FORMAT_CHOICES = [
        ('json', 'JSON'),
        ('pdf', 'PDF'),
        ('html', 'HTML'),
    ]
    
    scan = models.OneToOneField(ScanJob, on_delete=models.CASCADE, related_name='report')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    
    content = models.BinaryField()  # Store file content
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"Report: {self.scan.contract_name} ({self.report_type})"