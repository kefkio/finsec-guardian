from rest_framework import viewsets
from .models import ThreatRecord
from .serializers import ThreatRecordSerializer


class ThreatRecordViewSet(viewsets.ModelViewSet):
    queryset = ThreatRecord.objects.all()
    serializer_class = ThreatRecordSerializer
