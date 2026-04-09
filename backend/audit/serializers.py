from rest_framework import serializers
from .models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = [
            'id', 'event_type', 'description', 'severity',
            'actor', 'resource', 'ip_address', 'metadata', 'created_at',
        ]
        read_only_fields = ['created_at']
