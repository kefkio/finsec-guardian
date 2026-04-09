from rest_framework import viewsets
from rest_framework.response import Response
from .models import AuditEvent
from .serializers import AuditEventSerializer


class AuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditEventSerializer

    def get_queryset(self):
        qs = AuditEvent.objects.all()
        search = self.request.query_params.get('search', '')
        if search:
            qs = qs.filter(description__icontains=search) | qs.filter(event_type__icontains=search)
        return qs
