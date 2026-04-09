import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Scan, Finding
from .serializers import ScanSerializer, ScanCreateSerializer, FindingSerializer
from .engine_dispatcher import dispatch

logger = logging.getLogger(__name__)


class ScanViewSet(viewsets.ModelViewSet):
    queryset = Scan.objects.prefetch_related('findings').all()
    serializer_class = ScanSerializer
    http_method_names = ['get', 'post', 'head', 'options']

    def get_serializer_class(self):
        if self.action == 'create':
            return ScanCreateSerializer
        return ScanSerializer

    def create(self, request, *args, **kwargs):
        serializer = ScanCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        scan = serializer.save(status='running')

        try:
            raw_findings = dispatch(scan.tool, scan.source_code)
            for f in raw_findings:
                Finding.objects.create(scan=scan, **f)
            scan.status = 'completed'
        except Exception as exc:
            logger.exception('Analysis run failed for scan %s (%s): %s', scan.pk, scan.tool, exc)
            scan.error_message = str(exc)
            scan.status = 'failed'
        finally:
            scan.save()

        out = ScanSerializer(scan)
        return Response(out.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='findings')
    def findings(self, request, pk=None):
        scan = self.get_object()
        serializer = FindingSerializer(scan.findings.all(), many=True)
        return Response(serializer.data)
