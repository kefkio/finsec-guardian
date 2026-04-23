from rest_framework import serializers
from .models import ScanJob, Finding


class FindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Finding
        fields = ['id', 'swc_id', 'title', 'severity', 'description', 'recommendation', 'line_number']


class ScanJobSerializer(serializers.ModelSerializer):
    findings = FindingSerializer(many=True, read_only=True)
    finding_count = serializers.SerializerMethodField()

    class Meta:
        model = ScanJob
        fields = ['id', 'contract_name', 'source_code', 'status', 'created_at', 'completed_at', 'findings', 'finding_count']
        read_only_fields = ['status', 'created_at', 'completed_at']

    def get_finding_count(self, obj):
        return obj.findings.count()


class ScanJobListSerializer(serializers.ModelSerializer):
    finding_count = serializers.SerializerMethodField()

    class Meta:
        model = ScanJob
        fields = ['id', 'contract_name', 'status', 'created_at', 'completed_at', 'finding_count']

    def get_finding_count(self, obj):
        return obj.findings.count()
