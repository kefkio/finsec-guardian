"""
WebIntel API Views

RESTful endpoints for web intelligence scanning, threat intelligence, and reporting.
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import WebScan, WebFinding, WebThreat, WebIntelligenceReport
from .serializers import (
    WebScanSerializer, WebScanCreateSerializer, WebFindingSerializer,
    WebThreatSerializer, WebIntelligenceReportSerializer
)
from .services.orchestrator import WebIntelOrchestrator
from .services.persistence import WebIntelPersistence

logger = logging.getLogger(__name__)


class WebScanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for WebScan operations.
    
    Endpoints:
    - POST /api/webintel/scans/ - Start new scan
    - GET /api/webintel/scans/ - List user's scans
    - GET /api/webintel/scans/{id}/ - Get scan details
    - POST /api/webintel/scans/{id}/quick_scan/ - Quick scan endpoint
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = WebScanSerializer
    
    def get_queryset(self):
        """Return scans for authenticated user."""
        return WebScan.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_serializer_class(self):
        """Use appropriate serializer based on action."""
        if self.action == 'create':
            return WebScanCreateSerializer
        return WebScanSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create and start a new web intelligence scan.
        
        POST /api/webintel/scans/
        {
            "target": "https://example.com",
            "target_type": "url",
            "title": "Suspicious Site",
            "run_phishing_detection": true,
            "run_scam_detection": true,
            ...
        }
        """
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create scan record
        scan = WebIntelPersistence.create_scan(
            user=request.user,
            **serializer.validated_data
        )
        
        # Start analysis pipeline
        self._execute_scan_async(scan)
        
        # Return created scan
        output_serializer = WebScanSerializer(scan)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    def _execute_scan_async(self, scan: WebScan):
        """
        Execute scan pipeline (stub - would be celery task).
        
        In production: @app.task, run async with Celery.
        """
        
        try:
            WebIntelPersistence.update_scan_status(scan, 'running')
            
            # Initialize orchestrator
            orchestrator = WebIntelOrchestrator()
            
            # Determine which analyzers to run
            run_analyzers = []
            if scan.run_url_analysis:
                run_analyzers.append('url')
            if scan.run_phishing_detection:
                run_analyzers.append('phishing')
            if scan.run_scam_detection:
                run_analyzers.append('scam')
            if scan.run_social_engineering:
                run_analyzers.append('soceng')
            if scan.run_monetization_analysis:
                run_analyzers.append('monetization')
            
            # Execute scan
            result = orchestrator.execute_scan(
                target=scan.target,
                target_type=scan.target_type,
                run_analyzers=run_analyzers,
            )
            
            if result.get('success'):
                # Persist findings
                WebIntelPersistence.persist_findings(
                    scan,
                    result.get('findings', []),
                    result.get('analyzer_results', {})
                )
                
                # Update risk score
                WebIntelPersistence.update_scan_score(
                    scan,
                    risk_score=result.get('risk_score', 0),
                    finding_count=len(result.get('findings', []))
                )
            else:
                WebIntelPersistence.update_scan_status(scan, 'failed')
                logger.error(f"Scan {scan.id} failed: {result.get('error')}")
        
        except Exception as e:
            logger.error(f"Scan execution error: {e}")
            WebIntelPersistence.update_scan_status(scan, 'failed')
    
    @action(detail=False, methods=['post'])
    def quick_scan(self, request):
        """
        Quick scan endpoint - synchronous analysis.
        
        POST /api/webintel/scans/quick_scan/
        {
            "target": "https://example.com"
        }
        
        Returns immediate results.
        """
        
        target = request.data.get('target')
        target_type = request.data.get('target_type', 'url')
        
        if not target:
            return Response(
                {'error': 'target is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Run orchestrator directly
        orchestrator = WebIntelOrchestrator()
        result = orchestrator.execute_scan(target, target_type)
        
        return Response(result, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def risk_explanation(self, request, pk=None):
        """
        Get detailed explanation of risk score.
        
        GET /api/webintel/scans/{id}/risk_explanation/
        """
        
        scan = self.get_object()
        findings = scan.findings.all().values(
            'severity', 'category', 'analyzer', 'confidence_score'
        )
        
        from .services.risk_scorer import WebRiskScorer
        scorer = WebRiskScorer()
        explanation = scorer.explain_score(list(findings))
        
        return Response(explanation)


class WebFindingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for WebFinding (read-only).
    
    Endpoints:
    - GET /api/webintel/findings/ - List findings
    - GET /api/webintel/findings/{id}/ - Get finding details
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = WebFindingSerializer
    
    def get_queryset(self):
        """Return findings from user's scans."""
        return WebFinding.objects.filter(
            scan__user=self.request.user
        ).order_by('-created_at')


class WebThreatViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for WebThreat intelligence records (read-only).
    
    Endpoints:
    - GET /api/webintel/threats/ - List threats
    - GET /api/webintel/threats/{id}/ - Get threat details
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = WebThreatSerializer
    
    def get_queryset(self):
        """Return all threats (intelligence is shared)."""
        return WebThreat.objects.all().order_by('-last_seen')
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recently active threats."""
        threats = self.get_queryset()[:10]
        serializer = self.get_serializer(threats, many=True)
        return Response(serializer.data)


class WebIntelligenceReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for generating and managing intelligence reports.
    
    Endpoints:
    - POST /api/webintel/reports/ - Create new report
    - GET /api/webintel/reports/ - List user's reports
    - GET /api/webintel/reports/{id}/ - Get report
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = WebIntelligenceReportSerializer
    
    def get_queryset(self):
        """Return reports generated by user."""
        return WebIntelligenceReport.objects.filter(
            generated_by=self.request.user
        ).order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """
        Create aggregated intelligence report.
        
        POST /api/webintel/reports/
        {
            "title": "Q1 Web Threats Report",
            "scan_ids": ["scan-id-1", "scan-id-2"]
        }
        """
        
        title = request.data.get('title', 'Web Intelligence Report')
        scan_ids = request.data.getlist('scan_ids', [])
        
        # Get scans
        scans = WebScan.objects.filter(
            id__in=scan_ids,
            user=request.user
        )
        
        if not scans.exists():
            return Response(
                {'error': 'No valid scans specified'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate report content
        content = self._generate_report_content(list(scans))
        
        # Create report
        report = WebIntelPersistence.create_report(
            user=request.user,
            title=title,
            scans=list(scans),
            content=content
        )
        
        serializer = self.get_serializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @staticmethod
    def _generate_report_content(scans: list) -> dict:
        """Generate report content from scans."""
        
        total_findings = 0
        total_threats = 0
        avg_risk = 0
        
        for scan in scans:
            total_findings += scan.finding_count
            total_threats += scan.threat_count
            avg_risk += scan.risk_score
        
        if scans:
            avg_risk = avg_risk // len(scans)
        
        return {
            'summary': {
                'total_scans': len(scans),
                'total_findings': total_findings,
                'total_threats': total_threats,
                'average_risk_score': avg_risk,
            },
            'scan_details': [
                {
                    'target': scan.target,
                    'risk_score': scan.risk_score,
                    'findings_count': scan.finding_count,
                }
                for scan in scans
            ]
        }
