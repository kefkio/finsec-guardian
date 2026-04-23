import hashlib
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import TamperRecord
from .serializers import TamperRecordSerializer


class TamperRecordViewSet(viewsets.ModelViewSet):
    queryset = TamperRecord.objects.all()
    serializer_class = TamperRecordSerializer
    http_method_names = ['get', 'post', 'head', 'options']  # records are append-only

    def perform_create(self, serializer):
        content = serializer.validated_data['content']
        last = TamperRecord.objects.order_by('-created_at').first()
        previous_hash = last.content_hash if last else '0' * 64
        content_hash = hashlib.sha256((previous_hash + content).encode()).hexdigest()
        serializer.save(content_hash=content_hash, previous_hash=previous_hash)

    @action(detail=False, methods=['get'])
    def verify(self, request):
        records = TamperRecord.objects.order_by('created_at')
        valid = True
        previous_hash = '0' * 64
        for record in records:
            expected = hashlib.sha256((previous_hash + record.content).encode()).hexdigest()
            if record.content_hash != expected:
                valid = False
                record.chain_valid = False
                record.save(update_fields=['chain_valid'])
            previous_hash = record.content_hash
        return Response({'chain_valid': valid, 'record_count': records.count()})
