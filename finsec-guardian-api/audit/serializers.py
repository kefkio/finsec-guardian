from rest_framework import serializers
from .models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = ['id', 'event_type', 'severity', 'actor', 'resource', 'ip_address', 'message', 'metadata', 'timestamp']
        read_only_fields = ['timestamp']
