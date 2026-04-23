"""
WebIntel Admin Configuration

Django admin interface for web intelligence data.
"""

from django.contrib import admin
from .models import WebScan, WebFinding, WebThreat, WebIntelligenceReport, WebSuppressionBaseline


@admin.register(WebScan)
class WebScanAdmin(admin.ModelAdmin):
    list_display = ['target', 'target_type', 'status', 'risk_score', 'finding_count', 'created_at']
    list_filter = ['status', 'target_type', 'created_at']
    search_fields = ['target', 'title']
    readonly_fields = ['id', 'created_at', 'started_at', 'completed_at', 'finding_count', 'threat_count', 'risk_score']
    
    fieldsets = (
        ('Scan Info', {
            'fields': ('id', 'user', 'target', 'target_type', 'title', 'description')
        }),
        ('Status', {
            'fields': ('status', 'created_at', 'started_at', 'completed_at')
        }),
        ('Analysis Scope', {
            'fields': (
                'run_url_analysis', 'run_phishing_detection',
                'run_scam_detection', 'run_social_engineering', 'run_monetization_analysis'
            )
        }),
        ('Results', {
            'fields': ('risk_score', 'finding_count', 'threat_count')
        }),
        ('Engine Availability', {
            'fields': (
                'url_analyzer_available', 'phishing_detector_available',
                'scam_detector_available', 'soceng_analyzer_available',
                'monetization_analyzer_available'
            ),
            'classes': ('collapse',)
        }),
    )


@admin.register(WebFinding)
class WebFindingAdmin(admin.ModelAdmin):
    list_display = ['title', 'severity', 'analyzer', 'category', 'confidence_score', 'created_at']
    list_filter = ['severity', 'analyzer', 'category', 'created_at']
    search_fields = ['title', 'description', 'fingerprint']
    readonly_fields = ['id', 'fingerprint', 'created_at']
    
    fieldsets = (
        ('Finding Details', {
            'fields': ('id', 'scan', 'title', 'description')
        }),
        ('Classification', {
            'fields': ('severity', 'analyzer', 'category', 'fingerprint')
        }),
        ('Analysis', {
            'fields': ('confidence_score', 'risk_contribution', 'evidence')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )


@admin.register(WebThreat)
class WebThreatAdmin(admin.ModelAdmin):
    list_display = ['name', 'threat_type', 'severity_level', 'occurrence_count', 'last_seen']
    list_filter = ['threat_type', 'severity_level', 'last_seen']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'first_seen', 'last_seen']
    
    fieldsets = (
        ('Threat Identity', {
            'fields': ('id', 'name', 'threat_type', 'description')
        }),
        ('Severity', {
            'fields': ('severity_level', 'occurrence_count')
        }),
        ('Timeline', {
            'fields': ('first_seen', 'last_seen')
        }),
        ('Attribution', {
            'fields': ('indicators_of_compromise', 'known_attributes')
        }),
        ('Intelligence', {
            'fields': ('financial_impact', 'targeted_vertical', 'geographic_focus')
        }),
    )


@admin.register(WebIntelligenceReport)
class WebIntelligenceReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'generated_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['id', 'created_at']


@admin.register(WebSuppressionBaseline)
class WebSuppressionBaselineAdmin(admin.ModelAdmin):
    list_display = ['user', 'updated_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
