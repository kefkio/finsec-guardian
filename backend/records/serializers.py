from rest_framework import serializers
from .models import TamperProofRecord


class TamperProofRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = TamperProofRecord
        fields = [
            'id', 'title', 'content', 'content_hash',
            'previous_hash', 'chain_hash', 'created_at',
        ]
        read_only_fields = ['content_hash', 'previous_hash', 'chain_hash', 'created_at']


class TamperProofRecordCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TamperProofRecord
        fields = ['title', 'content']
