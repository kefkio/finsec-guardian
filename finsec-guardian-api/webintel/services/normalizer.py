"""
WebIntel Finding Normalizer

Transforms heterogeneous analyzer outputs into a unified finding schema.
Similar to scanner/services/normalizer.py but adapted for web intelligence.
"""

import logging
from typing import List, Dict, Any
from dataclasses import asdict

from .analyzers.base import WebFindingData

logger = logging.getLogger(__name__)


class FindingNormalizer:
    """
    Normalizes findings from all WebIntel analyzers into a canonical schema.
    
    Canonical schema:
    {
        'title': str,
        'description': str,
        'severity': str (critical|high|medium|low|info),
        'category': str,
        'analyzer': str,
        'confidence_score': int (0-100),
        'fingerprint': str,
        'evidence': dict,
        'timestamp': str,
    }
    """
    
    SEVERITY_HIERARCHY = {
        'critical': 5,
        'high': 4,
        'medium': 3,
        'low': 2,
        'info': 1,
    }
    
    def normalize(self, findings: List[WebFindingData]) -> List[Dict[str, Any]]:
        """
        Normalize heterogeneous findings into canonical schema.
        
        Args:
            findings: List of WebFindingData objects
        
        Returns:
            List of normalized finding dictionaries
        """
        
        normalized = []
        
        for finding in findings:
            try:
                normalized_finding = self._normalize_finding(finding)
                normalized.append(normalized_finding)
                
            except Exception as e:
                logger.warning(f"Failed to normalize finding: {e}")
                continue
        
        return normalized
    
    def _normalize_finding(self, finding: WebFindingData) -> Dict[str, Any]:
        """Normalize single finding."""
        
        # Convert dataclass to dict
        if isinstance(finding, WebFindingData):
            finding_dict = asdict(finding)
        else:
            finding_dict = finding
        
        # Normalize severity
        severity = finding_dict.get('severity', 'info')
        if isinstance(severity, str):
            severity = severity.lower()
        
        if severity not in self.SEVERITY_HIERARCHY:
            severity = 'info'
        
        # Generate fingerprint if missing
        fingerprint = finding_dict.get('fingerprint')
        if not fingerprint:
            fingerprint = self._generate_fingerprint(finding_dict)
        
        # Ensure confidence score is in valid range
        confidence = finding_dict.get('confidence_score', 0)
        confidence = max(0, min(100, int(confidence)))
        
        # Canonical output
        return {
            'title': finding_dict.get('title', 'Untitled Finding'),
            'description': finding_dict.get('description', ''),
            'severity': severity,
            'category': finding_dict.get('category', 'uncategorized'),
            'analyzer': finding_dict.get('analyzer_name', 'unknown'),
            'confidence_score': confidence,
            'fingerprint': fingerprint,
            'evidence': finding_dict.get('evidence', {}),
        }
    
    @staticmethod
    def _generate_fingerprint(finding: Dict[str, Any]) -> str:
        """
        Generate unique fingerprint for finding deduplication.
        
        Based on: category + normalized title
        """
        
        category = finding.get('category', 'unknown').lower().strip()
        title = finding.get('title', 'untitled').lower().strip()
        
        # Normalize title: remove punctuation, extra spaces
        import re
        title = re.sub(r'[^a-z0-9\s]', '', title)
        title = re.sub(r'\s+', '_', title)[:30]
        
        fingerprint = f"{category}:{title}"
        
        return fingerprint
    
    def deduplicate_by_evidence(
        self,
        findings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Additional deduplication based on evidence content.
        
        Finds findings with similar evidence and merges them.
        """
        
        if not findings:
            return []
        
        # Group by evidence hash
        evidence_groups = {}
        
        for finding in findings:
            evidence = finding.get('evidence', {})
            
            # Create hash of evidence content
            evidence_hash = self._hash_evidence(evidence)
            
            if evidence_hash not in evidence_groups:
                evidence_groups[evidence_hash] = []
            
            evidence_groups[evidence_hash].append(finding)
        
        # Deduplicate within groups
        deduped = []
        
        for group in evidence_groups.values():
            if len(group) == 1:
                deduped.append(group[0])
            else:
                # Keep highest severity
                best = max(
                    group,
                    key=lambda f: self._severity_rank(f['severity'])
                )
                deduped.append(best)
        
        return deduped
    
    @staticmethod
    def _hash_evidence(evidence: Dict[str, Any]) -> str:
        """Generate hash of evidence dictionary."""
        # Simple approach: stringify and hash
        import json
        evidence_str = json.dumps(evidence, sort_keys=True, default=str)
        
        # Use simple hash (in production, use hashlib)
        return str(hash(evidence_str))
    
    @staticmethod
    def _severity_rank(severity: str) -> int:
        """Convert severity to numeric rank."""
        ranks = {
            'critical': 5,
            'high': 4,
            'medium': 3,
            'low': 2,
            'info': 1,
        }
        return ranks.get(severity, 0)
