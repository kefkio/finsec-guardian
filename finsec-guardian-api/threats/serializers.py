from rest_framework import serializers
from .models import ThreatRecord


class ThreatRecordSerializer(serializers.ModelSerializer):
    risk_score = serializers.ReadOnlyField()

    class Meta:
        model = ThreatRecord
        fields = ['id', 'title', 'category', 'description', 'likelihood', 'impact', 'risk_score', 'mitigation', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
