"""
FinSec WebIntel Data Models

WebIntel provides detection and scoring for financial deception risks in web-based systems.
Models track scans, findings, and threat intelligence about malicious domains/URLs.
"""

from django.db import models
from django.contrib.auth.models import User
import uuid


class WebScan(models.Model):
    """
    Represents a web intelligence scan job.
    
    Scans can target a URL, domain, or IP address and run multiple analyzers
    to detect scam websites, phishing pages, and social engineering patterns.
    """
    
    SCAN_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    TARGET_TYPE_CHOICES = [
        ('url', 'Full URL'),
        ('domain', 'Domain Name'),
        ('ip', 'IP Address'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='web_scans')
    
    # Target information
    target = models.CharField(max_length=2048, help_text="URL, domain, or IP to analyze")
    target_type = models.CharField(max_length=10, choices=TARGET_TYPE_CHOICES, default='url')
    
    # Scan metadata
    status = models.CharField(max_length=20, choices=SCAN_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Analysis scope
    run_url_analysis = models.BooleanField(default=True)
    run_phishing_detection = models.BooleanField(default=True)
    run_scam_detection = models.BooleanField(default=True)
    run_social_engineering = models.BooleanField(default=True)
    run_monetization_analysis = models.BooleanField(default=True)
    
    # Results
    risk_score = models.IntegerField(default=0, help_text="0-100 composite risk score")
    finding_count = models.IntegerField(default=0)
    threat_count = models.IntegerField(default=0)
    
    # Web-specific metadata
    title = models.CharField(max_length=512, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    # Engine availability flags
    url_analyzer_available = models.BooleanField(default=True)
    phishing_detector_available = models.BooleanField(default=True)
    scam_detector_available = models.BooleanField(default=True)
    soceng_analyzer_available = models.BooleanField(default=True)
    monetization_analyzer_available = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['target']),
        ]
    
    def __str__(self):
        return f"WebScan({self.target[:50]}@{self.created_at.strftime('%Y-%m-%d')})"


class WebFinding(models.Model):
    """
    Individual finding from web intelligence analysis.
    
    Represents a detected threat indicator (e.g., phishing form, scam signature, 
    social engineering tactic, monetization pipeline).
    """
    
    SEVERITY_CHOICES = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
        ('info', 'Informational'),
    ]
    
    ANALYZER_CHOICES = [
        ('url', 'URL/Domain Analyzer'),
        ('phishing', 'Phishing Detector'),
        ('scam', 'Scam Signature Matcher'),
        ('soceng', 'Social Engineering Analyzer'),
        ('monetization', 'Monetization Pipeline Analyzer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scan = models.ForeignKey(WebScan, on_delete=models.CASCADE, related_name='findings')
    
    # Finding classification
    title = models.CharField(max_length=256)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    analyzer = models.CharField(max_length=50, choices=ANALYZER_CHOICES)
    category = models.CharField(max_length=100, help_text="e.g., phishing_form, vsl_funnel, credential_harvester")
    
    # Evidence
    evidence = models.JSONField(default=dict, blank=True, help_text="Analyzer-specific evidence data")
    
    # Impact assessment
    confidence_score = models.IntegerField(default=0, help_text="0-100 confidence in finding")
    risk_contribution = models.FloatField(default=0.0, help_text="Contribution to overall risk score")
    
    # Deduplication
    fingerprint = models.CharField(max_length=256, db_index=True, help_text="Normalized finding signature")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-severity', '-created_at']
        indexes = [
            models.Index(fields=['scan', 'severity']),
            models.Index(fields=['analyzer']),
            models.Index(fields=['fingerprint']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.severity})"


class WebThreat(models.Model):
    """
    Aggregated threat intelligence record.
    
    Links multiple findings to a common threat actor, pattern, or infrastructure.
    Provides context for threat correlation and reputation scoring.
    """
    
    THREAT_TYPE_CHOICES = [
        ('phishing_campaign', 'Phishing Campaign'),
        ('investment_scam', 'Investment Scam'),
        ('vsl_funnel', 'VSL Sales Funnel'),
        ('credential_harvester', 'Credential Harvester'),
        ('botnet_c2', 'Botnet C&C'),
        ('ransomware', 'Ransomware Infrastructure'),
        ('money_laundering', 'Money Laundering Pipeline'),
        ('payment_fraud', 'Payment Fraud'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Threat identity
    threat_type = models.CharField(max_length=100, choices=THREAT_TYPE_CHOICES)
    name = models.CharField(max_length=256, help_text="Threat actor or campaign name")
    description = models.TextField(blank=True)
    
    # Attribution
    indicators_of_compromise = models.JSONField(default=list, blank=True, help_text="Associated domains, IPs, emails")
    known_attributes = models.JSONField(default=dict, blank=True, help_text="Observable patterns and signatures")
    
    # Threat scoring
    severity_level = models.CharField(max_length=20, choices=[('critical', 'Critical'), ('high', 'High'), ('medium', 'Medium'), ('low', 'Low')])
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    occurrence_count = models.IntegerField(default=1)
    
    # Intelligence enrichment
    financial_impact = models.CharField(max_length=100, blank=True, help_text="Estimated impact: e.g., '100K-1M USD'")
    targeted_vertical = models.CharField(max_length=100, blank=True, help_text="Industry: e.g., Cryptocurrency, Real Estate")
    geographic_focus = models.CharField(max_length=256, blank=True, help_text="Regions targeted: e.g., North America, EU")
    
    # Findings reference
    findings = models.ManyToManyField(WebFinding, related_name='threats', blank=True)
    
    class Meta:
        ordering = ['-last_seen']
        indexes = [
            models.Index(fields=['threat_type', '-last_seen']),
            models.Index(fields=['severity_level']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.threat_type})"


class WebIntelligenceReport(models.Model):
    """
    Generated intelligence report from one or more web scans.
    
    Can be exported as JSON, HTML, or PDF for consumption by other FinSec modules
    or external stakeholders.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scans = models.ManyToManyField(WebScan, related_name='reports')
    
    title = models.CharField(max_length=512)
    description = models.TextField(blank=True)
    
    # Report generation
    created_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Report contents
    content_json = models.JSONField(default=dict, blank=True)
    
    # Export formats
    html_rendered = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"WebIntelReport({self.title})"


class WebSuppressionBaseline(models.Model):
    """
    Baseline configuration for suppressing false positives.
    
    Allows whitelisting of legitimate websites/patterns to reduce noise.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='web_suppression_baseline')
    
    # Suppression rules
    whitelisted_domains = models.JSONField(default=list, blank=True)
    whitelisted_patterns = models.JSONField(default=list, blank=True)  # Regex patterns
    ignored_threat_types = models.JSONField(default=list, blank=True)
    ignored_findings = models.ManyToManyField(WebFinding, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Suppression baseline for {self.user.username}"
