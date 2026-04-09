from rest_framework import serializers
from .models import Threat


class ThreatSerializer(serializers.ModelSerializer):
    risk_score = serializers.ReadOnlyField()

    class Meta:
        model = Threat
        fields = [
            'id', 'title', 'description', 'category', 'likelihood',
            'impact', 'risk_score', 'status', 'mitigation',
            'created_at', 'updated_at',
        ]
