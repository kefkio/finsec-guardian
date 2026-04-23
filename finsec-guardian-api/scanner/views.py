import hashlib
import logging
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError as DRFValidationError

from .models import ScanJob, Finding, FindingCategory
from .serializers import ScanJobSerializer, ScanJobListSerializer, FindingSerializer
from .slither_runner import run_slither_analysis
from audit.models import AuditEvent

logger = logging.getLogger(__name__)


def _audit(user, action, resource_type, resource_id, message, ip_address=None, metadata=None):
    """
    Bridge between call-sites that use (user, action, resource_type, resource_id)
    and AuditEvent's actual fields (event_type, actor, resource, metadata).
    """
    AuditEvent.objects.create(
        event_type=f'{action}_{resource_type}',
        actor=str(user) if user else 'anonymous',
        resource=f'{resource_type}:{resource_id}',
        severity='info',
        message=message,
        ip_address=ip_address,
        metadata=metadata or {},
    )



def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class ScanJobViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for managing Solidity contract scans
    
    Endpoints:
    - POST /api/scanner/scans/ - Create new scan
    - GET /api/scanner/scans/ - List all scans
    - GET /api/scanner/scans/{id}/ - Get scan details
    - GET /api/scanner/scans/{id}/findings/ - Get scan findings
    - POST /api/scanner/scans/{id}/suppress-finding/ - Suppress a finding
    - POST /api/scanner/scans/{id}/export-report/ - Export scan report
    """

    @action(detail=False, methods=['post'], url_path='trigger')
    def trigger_scan(self, request):
        """
        Trigger a Solidity scan via POST.
        Expects: { "source_code": "...", "contract_name": "..." }
        """
        from .slither_parser import parse_slither_output

        source_code = request.data.get('source_code')
        contract_name = request.data.get('contract_name', 'Contract')
        if not source_code:
            return Response({'error': 'source_code is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Run Slither analysis
        slither_output = run_slither_analysis(source_code)
        if 'error' in slither_output:
            return Response({'error': slither_output['error'], 'stderr': slither_output.get('stderr')}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        findings = parse_slither_output(slither_output)
        # Optionally: Save ScanJob and Finding objects here

        return Response({'contract_name': contract_name, 'findings': findings}, status=status.HTTP_200_OK)

    queryset = ScanJob.objects.all()
    serializer_class = ScanJobSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return ScanJobListSerializer
        return ScanJobSerializer
    
    def get_queryset(self):
        """Filter scans by authenticated user"""
        return ScanJob.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        """
        Create a new scan job with audit trail
        Async analysis via Celery task
        """
        source_code = serializer.validated_data.get('source_code', '')
        contract_name = serializer.validated_data.get('contract_name', 'Unnamed')
        
        # Validate source code
        if not source_code or len(source_code.strip()) == 0:
            raise DRFValidationError({'source_code': 'Source code cannot be empty'})
        
        if len(source_code) > 1000000:  # 1MB limit
            raise DRFValidationError({'source_code': 'Source code exceeds maximum size of 1MB'})
        
        # Compute source code hash
        source_hash = hashlib.sha256(source_code.encode('utf-8')).hexdigest()
        
        # Create scan job with user context
        job = serializer.save(
            user=self.request.user,
            status='pending',
            source_code_hash=source_hash,
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:500],
            metadata={
                'endpoint': '/api/scanner/scans/',
                'method': 'POST'
            }
        )
        
        # Log audit event
        _audit(
            user=self.request.user, action='CREATE', resource_type='ScanJob',
            resource_id=job.id,
            message=f'Created scan job for contract: {contract_name}',
            ip_address=get_client_ip(self.request),
            metadata={'contract_name': contract_name, 'source_hash': source_hash}
        )
        
        # Queue async analysis task
        run_slither_analysis.delay(job.id)
        
        logger.info(f"ScanJob {job.id} created for user {self.request.user.id}")
        return job

    def perform_update(self, serializer):
        """Track updates to scan jobs"""
        job = serializer.save()
        
        _audit(
            user=self.request.user, action='UPDATE', resource_type='ScanJob',
            resource_id=job.id,
            message=f'Updated scan job: {job.contract_name}',
            ip_address=get_client_ip(self.request)
        )

    def perform_destroy(self, instance):
        """Log scan deletion"""
        _audit(
            user=self.request.user, action='DELETE', resource_type='ScanJob',
            resource_id=instance.id,
            message=f'Deleted scan job: {instance.contract_name}',
            ip_address=get_client_ip(self.request)
        )
        instance.delete()

    @action(detail=True, methods=['get'])
    def findings(self, request, pk=None):
        """Get all findings for a specific scan"""
        scan = self.get_object()
        
        # Filter by severity if provided
        severity = request.query_params.get('severity')
        findings = scan.findings.all()
        
        if severity:
            findings = findings.filter(severity=severity)
        
        serializer = FindingSerializer(findings, many=True)
        
        return Response({
            'scan_id': scan.id,
            'contract_name': scan.contract_name,
            'total_findings': findings.count(),
            'findings': serializer.data
        })

    @action(detail=True, methods=['post'])
    def suppress_finding(self, request, pk=None):
        """Suppress a finding to avoid future reports"""
        scan = self.get_object()
        finding_id = request.data.get('finding_id')
        reason = request.data.get('reason', '')
        
        try:
            finding = Finding.objects.get(id=finding_id, scan=scan)
        except Finding.DoesNotExist:
            return Response(
                {'error': 'Finding not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Mark as suppressed
        finding.status = 'suppressed'
        finding.suppression_reason = reason
        finding.save(update_fields=['status', 'suppression_reason'])
        
        # Log audit event
        _audit(
            user=request.user, action='UPDATE', resource_type='Finding',
            resource_id=finding.id,
            message=f'Suppressed finding: {finding.title}',
            ip_address=get_client_ip(request),
            metadata={'reason': reason}
        )
        
        return Response({
            'status': 'Finding suppressed',
            'finding_id': finding.id,
            'reason': reason
        })

    @action(detail=True, methods=['post'])
    def acknowledge_finding(self, request, pk=None):
        """Acknowledge a finding as reviewed"""
        scan = self.get_object()
        finding_id = request.data.get('finding_id')
        
        try:
            finding = Finding.objects.get(id=finding_id, scan=scan)
        except Finding.DoesNotExist:
            return Response(
                {'error': 'Finding not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        finding.status = 'acknowledged'
        finding.save(update_fields=['status', 'updated_at'])
        
        _audit(
            user=request.user, action='UPDATE', resource_type='Finding',
            resource_id=finding.id,
            message=f'Acknowledged finding: {finding.title}',
            ip_address=get_client_ip(request)
        )
        
        return Response({
            'status': 'Finding acknowledged',
            'finding_id': finding.id
        })

    @action(detail=True, methods=['post'])
    def mark_resolved(self, request, pk=None):
        """Mark a finding as resolved"""
        scan = self.get_object()
        finding_id = request.data.get('finding_id')
        resolution_notes = request.data.get('notes', '')
        
        try:
            finding = Finding.objects.get(id=finding_id, scan=scan)
        except Finding.DoesNotExist:
            return Response(
                {'error': 'Finding not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        finding.status = 'resolved'
        finding.resolved_at = timezone.now()
        finding.metadata = finding.metadata or {}
        finding.metadata['resolution_notes'] = resolution_notes
        finding.save(update_fields=['status', 'resolved_at', 'metadata', 'updated_at'])
        
        _audit(
            user=request.user, action='UPDATE', resource_type='Finding',
            resource_id=finding.id,
            message=f'Marked as resolved: {finding.title}',
            ip_address=get_client_ip(request),
            metadata={'notes': resolution_notes}
        )
        
        return Response({
            'status': 'Finding marked as resolved',
            'finding_id': finding.id,
            'resolved_at': finding.resolved_at
        })

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get scan statistics and summary"""
        scan = self.get_object()
        
        return Response({
            'scan_id': scan.id,
            'contract_name': scan.contract_name,
            'status': scan.status,
            'created_at': scan.created_at,
            'completed_at': scan.completed_at,
            'findings_summary': {
                'total': scan.total_findings,
                'critical': scan.critical_count,
                'high': scan.high_count,
                'medium': scan.medium_count,
                'low': scan.low_count,
                'info': scan.info_count
            },
            'status_breakdown': {
                'new': scan.findings.filter(status='new').count(),
                'acknowledged': scan.findings.filter(status='acknowledged').count(),
                'suppressed': scan.findings.filter(status='suppressed').count(),
                'resolved': scan.findings.filter(status='resolved').count(),
            },
            'risk_metrics': {
                'average_risk_score': sum(
                    f.get_risk_score() for f in scan.findings.all()
                ) / max(scan.total_findings, 1) if scan.total_findings > 0 else 0,
                'high_risk_findings': scan.findings.filter(
                    severity__in=['critical', 'high']
                ).count(),
            }
        })

    @action(detail=True, methods=['post'])
    def export_report(self, request, pk=None):
        """
        Export scan report in specified format
        Formats: json, pdf, html
        """
        scan = self.get_object()
        report_format = request.data.get('format', 'json')
        report_type = request.data.get('type', 'summary')  # summary, detailed, executive
        
        if report_format not in ['json', 'pdf', 'html']:
            return Response(
                {'error': 'Invalid format. Choose from: json, pdf, html'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Queue report generation task
        from .tasks import generate_scan_report
        task = generate_scan_report.delay(scan.id, report_format, report_type)
        
        return Response({
            'status': 'Report generation queued',
            'task_id': task.id,
            'scan_id': scan.id,
            'format': report_format,
            'type': report_type
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def quick_scan(request):
    """
    Quick scan endpoint - simplified interface
    POST with: source_code, contract_name (optional)
    """
    source_code = request.data.get('source_code', '')
    contract_name = request.data.get('contract_name', 'QuickScan')
    
    if not source_code:
        return Response(
            {'error': 'source_code is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create and queue scan
    source_hash = hashlib.sha256(source_code.encode('utf-8')).hexdigest()
    
    scan = ScanJob.objects.create(
        user=request.user,
        source_code=source_code,
        contract_name=contract_name,
        status='pending',
        source_code_hash=source_hash,
        ip_address=get_client_ip(request)
    )
    
    # Log event
    _audit(
        user=request.user, action='CREATE', resource_type='ScanJob',
        resource_id=scan.id,
        message=f'Quick scan initiated for: {contract_name}',
        ip_address=get_client_ip(request)
    )
    
    # Queue analysis
    run_slither_analysis.delay(scan.id)
    
    return Response(
        ScanJobSerializer(scan).data,
        status=status.HTTP_201_CREATED
    )