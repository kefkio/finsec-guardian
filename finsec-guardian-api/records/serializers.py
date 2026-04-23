from rest_framework import serializers
from .models import TamperRecord


class TamperRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = TamperRecord
        fields = ['id', 'content', 'content_hash', 'previous_hash', 'chain_valid', 'created_at']
        read_only_fields = ['content_hash', 'previous_hash', 'chain_valid', 'created_at']
