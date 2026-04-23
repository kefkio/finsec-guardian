"""
WebIntel Persistence Service

Handles database operations for storing scans, findings, and threat intelligence.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..models import WebScan, WebFinding, WebThreat, WebIntelligenceReport

logger = logging.getLogger(__name__)


class WebIntelPersistence:
    """Persists WebIntel scan results to the database."""
    
    @staticmethod
    def create_scan(
        user,
        target: str,
        target_type: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        **scan_kwargs
    ) -> WebScan:
        """Create and save a WebScan record."""
        
        scan = WebScan(
            user=user,
            target=target,
            target_type=target_type,
            title=title or target[:100],
            description=description,
            status='pending',
            **scan_kwargs
        )
        scan.save()
        
        logger.info(f"Created WebScan: {scan.id} for {target}")
        return scan
    
    @staticmethod
    def update_scan_status(scan: WebScan, status: str):
        """Update scan status."""
        scan.status = status
        if status == 'running':
            scan.started_at = datetime.now()
        elif status == 'completed':
            scan.completed_at = datetime.now()
        
        scan.save()
    
    @staticmethod
    def persist_findings(
        scan: WebScan,
        findings: List[Dict[str, Any]],
        engine_results: Dict[str, Dict[str, Any]]
    ) -> List[WebFinding]:
        """
        Persist normalized findings to database.
        
        Args:
            scan: Parent WebScan record
            findings: List of normalized findings
            engine_results: Metadata about each analyzer
        
        Returns:
            List of created WebFinding records
        """
        
        created_findings = []
        
        for finding_data in findings:
            try:
                finding = WebFinding(
                    scan=scan,
                    title=finding_data.get('title'),
                    description=finding_data.get('description'),
                    severity=finding_data.get('severity'),
                    analyzer=finding_data.get('analyzer'),
                    category=finding_data.get('category'),
                    evidence=finding_data.get('evidence', {}),
                    confidence_score=finding_data.get('confidence_score'),
                    fingerprint=finding_data.get('fingerprint'),
                )
                finding.save()
                created_findings.append(finding)
                
            except Exception as e:
                logger.error(f"Failed to persist finding: {e}")
                continue
        
        # Update scan metadata
        scan.finding_count = len(created_findings)
        
        # Update engine availability flags
        for analyzer_name, result in engine_results.items():
            if result.get('available') is False:
                setattr(scan, f'{analyzer_name}_available', False)
        
        scan.save()
        
        logger.info(f"Persisted {len(created_findings)} findings for scan {scan.id}")
        
        return created_findings
    
    @staticmethod
    def update_scan_score(scan: WebScan, risk_score: int, finding_count: int):
        """Update scan with final risk score."""
        scan.risk_score = risk_score
        scan.finding_count = finding_count
        scan.status = 'completed'
        scan.completed_at = datetime.now()
        scan.save()
        
        logger.info(f"Updated scan {scan.id} with risk score: {risk_score}")
    
    @staticmethod
    def create_threat_record(
        threat_type: str,
        name: str,
        severity_level: str,
        findings: List[WebFinding],
        **threat_kwargs
    ) -> WebThreat:
        """Create and link threat intelligence record."""
        
        threat = WebThreat(
            threat_type=threat_type,
            name=name,
            severity_level=severity_level,
            **threat_kwargs
        )
        threat.save()
        
        # Add findings
        for finding in findings:
            threat.findings.add(finding)
        
        logger.info(f"Created WebThreat: {threat.id} ({name})")
        return threat
    
    @staticmethod
    def create_report(
        user,
        title: str,
        scans: List[WebScan],
        content: Optional[Dict[str, Any]] = None,
    ) -> WebIntelligenceReport:
        """Create aggregated intelligence report."""
        
        report = WebIntelligenceReport(
            title=title,
            generated_by=user,
            content_json=content or {},
        )
        report.save()
        
        # Add scans
        for scan in scans:
            report.scans.add(scan)
        
        logger.info(f"Created WebIntelligenceReport: {report.id}")
        return report
    
    @staticmethod
    def get_scan_with_findings(scan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve scan and all associated findings."""
        
        try:
            scan = WebScan.objects.get(id=scan_id)
            findings = scan.findings.all().values(
                'id', 'title', 'description', 'severity',
                'analyzer', 'category', 'confidence_score', 'evidence'
            )
            
            return {
                'scan': {
                    'id': str(scan.id),
                    'target': scan.target,
                    'target_type': scan.target_type,
                    'status': scan.status,
                    'risk_score': scan.risk_score,
                    'created_at': scan.created_at.isoformat(),
                    'completed_at': scan.completed_at.isoformat() if scan.completed_at else None,
                },
                'findings': list(findings),
                'finding_count': len(findings),
            }
        
        except WebScan.DoesNotExist:
            logger.warning(f"Scan not found: {scan_id}")
            return None
