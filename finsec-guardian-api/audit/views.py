from rest_framework import viewsets
from .models import AuditEvent
from .serializers import AuditEventSerializer


class AuditEventViewSet(viewsets.ModelViewSet):
    queryset = AuditEvent.objects.all()
    serializer_class = AuditEventSerializer
    http_method_names = ['get', 'post', 'head', 'options']  # no edit/delete on audit log
