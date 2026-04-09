from rest_framework import serializers
from .models import Scan, Finding


class FindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Finding
        fields = ['id', 'swc_id', 'title', 'description', 'severity', 'line_number', 'recommendation']


class ScanSerializer(serializers.ModelSerializer):
    findings = FindingSerializer(many=True, read_only=True)
    findings_count = serializers.SerializerMethodField()

    class Meta:
        model = Scan
        fields = [
            'id', 'contract_name', 'status', 'error_message',
            'created_at', 'updated_at', 'findings', 'findings_count',
        ]
        read_only_fields = ['status', 'error_message', 'created_at', 'updated_at', 'findings']

    def get_findings_count(self, obj):
        return obj.findings.count()


class ScanCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scan
        fields = ['contract_name', 'source_code']
