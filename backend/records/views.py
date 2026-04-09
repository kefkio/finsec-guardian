from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import TamperProofRecord
from .serializers import TamperProofRecordSerializer, TamperProofRecordCreateSerializer
from .hashing import compute_content_hash, compute_chain_hash


class TamperProofRecordViewSet(viewsets.ModelViewSet):
    queryset = TamperProofRecord.objects.all()
    serializer_class = TamperProofRecordSerializer
    http_method_names = ['get', 'post', 'head', 'options']

    def get_serializer_class(self):
        if self.action == 'create':
            return TamperProofRecordCreateSerializer
        return TamperProofRecordSerializer

    def create(self, request, *args, **kwargs):
        serializer = TamperProofRecordCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        title = serializer.validated_data['title']
        content = serializer.validated_data['content']

        last = TamperProofRecord.objects.last()
        previous_hash = last.chain_hash if last else '0' * 64

        content_hash = compute_content_hash(content)
        chain_hash = compute_chain_hash(content_hash, previous_hash)

        record = TamperProofRecord.objects.create(
            title=title,
            content=content,
            content_hash=content_hash,
            previous_hash=previous_hash,
            chain_hash=chain_hash,
        )

        out = TamperProofRecordSerializer(record)
        return Response(out.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='verify')
    def verify(self, request):
        records = TamperProofRecord.objects.all()
        valid = True
        broken_at = None

        prev_hash = '0' * 64
        for record in records:
            expected_content_hash = compute_content_hash(record.content)
            expected_chain_hash = compute_chain_hash(expected_content_hash, prev_hash)

            if (record.content_hash != expected_content_hash
                    or record.chain_hash != expected_chain_hash
                    or record.previous_hash != prev_hash):
                valid = False
                broken_at = record.pk
                break

            prev_hash = record.chain_hash

        return Response({'valid': valid, 'broken_at': broken_at, 'total': records.count()})
