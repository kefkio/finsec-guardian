"""
WebIntel Serializers

DRF serializers for WebScan, WebFinding, WebThreat, and reports.
"""

from rest_framework import serializers
from .models import (
    WebScan, WebFinding, WebThreat, WebIntelligenceReport,
    WebSuppressionBaseline
)


class WebFindingSerializer(serializers.ModelSerializer):
    """Serializer for WebFinding."""
    
    class Meta:
        model = WebFinding
        fields = [
            'id', 'title', 'description', 'severity', 'analyzer',
            'category', 'confidence_score', 'fingerprint', 'evidence', 'created_at'
        ]
        read_only_fields = ['id', 'fingerprint', 'created_at']


class WebScanSerializer(serializers.ModelSerializer):
    """Serializer for WebScan."""
    
    findings = WebFindingSerializer(many=True, read_only=True)
    
    class Meta:
        model = WebScan
        fields = [
            'id', 'target', 'target_type', 'status', 'risk_score',
            'finding_count', 'threat_count', 'created_at', 'started_at',
            'completed_at', 'run_url_analysis', 'run_phishing_detection',
            'run_scam_detection', 'run_social_engineering', 'run_monetization_analysis',
            'findings', 'title', 'description',
        ]
        read_only_fields = [
            'id', 'status', 'risk_score', 'finding_count', 'threat_count',
            'created_at', 'started_at', 'completed_at', 'findings'
        ]


class WebScanCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new WebScans."""
    
    class Meta:
        model = WebScan
        fields = [
            'target', 'target_type', 'title', 'description',
            'run_url_analysis', 'run_phishing_detection', 'run_scam_detection',
            'run_social_engineering', 'run_monetization_analysis',
        ]


class WebThreatSerializer(serializers.ModelSerializer):
    """Serializer for WebThreat."""
    
    findings_count = serializers.SerializerMethodField()
    
    class Meta:
        model = WebThreat
        fields = [
            'id', 'threat_type', 'name', 'description', 'severity_level',
            'first_seen', 'last_seen', 'occurrence_count', 'indicators_of_compromise',
            'known_attributes', 'financial_impact', 'targeted_vertical',
            'geographic_focus', 'findings_count'
        ]
        read_only_fields = ['id', 'first_seen', 'last_seen']
    
    def get_findings_count(self, obj):
        return obj.findings.count()


class WebIntelligenceReportSerializer(serializers.ModelSerializer):
    """Serializer for WebIntelligenceReport."""
    
    scans_count = serializers.SerializerMethodField()
    
    class Meta:
        model = WebIntelligenceReport
        fields = [
            'id', 'title', 'description', 'created_at', 'scans_count', 'content_json'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_scans_count(self, obj):
        return obj.scans.count()


class WebSuppressionBaselineSerializer(serializers.ModelSerializer):
    """Serializer for suppression rules."""
    
    class Meta:
        model = WebSuppressionBaseline
        fields = [
            'id', 'whitelisted_domains', 'whitelisted_patterns',
            'ignored_threat_types', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
