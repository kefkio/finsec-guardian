"""
WebIntel Orchestrator

Coordinates execution of all analysis engines and normalizes findings.
Pipeline: Input Validation → Analyzer Execution → Finding Normalization → Risk Scoring → Persistence
"""

import time
import logging
from typing import List, Dict, Any
from dataclasses import asdict
from datetime import datetime

from .normalizer import FindingNormalizer
from .risk_scorer import WebRiskScorer
from .analyzers.base import AnalyzerResult
from .analyzers.url import URLDomainAnalyzer
from .analyzers.phishing import PhishingDetector
from .analyzers.scam import ScamDetector
from .analyzers.soceng import SocialEngineeringAnalyzer
from .analyzers.monetization import MonetizationAnalyzer

logger = logging.getLogger(__name__)


class WebIntelOrchestrator:
    """
    Orchestrates the complete WebIntel pipeline.
    
    Pipeline stages:
    1. Input Validation: Normalize and validate target
    2. Analyzer Execution: Run all available analyzers in parallel
    3. Finding Normalization: Unify findings from all engines
    4. Finding Deduplication: Remove duplicate findings
    5. Risk Scoring: Calculate composite risk score
    6. Metadata Assembly: Package results for persistence
    """
    
    def __init__(self):
        """Initialize orchestrator with all analyzers."""
        self.analyzers = {
            'url': URLDomainAnalyzer(),
            'phishing': PhishingDetector(),
            'scam': ScamDetector(),
            'soceng': SocialEngineeringAnalyzer(),
            'monetization': MonetizationAnalyzer(),
        }
        
        self.normalizer = FindingNormalizer()
        self.risk_scorer = WebRiskScorer()
    
    def execute_scan(
        self,
        target: str,
        target_type: str = 'url',
        content: str = None,
        run_analyzers: List[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute complete web intelligence scan pipeline.
        
        Args:
            target: URL, domain, or IP to analyze
            target_type: Type of target ('url', 'domain', 'ip')
            content: Optional pre-fetched HTML content
            run_analyzers: List of analyzer names to run (None = all)
            **kwargs: Additional parameters for analyzers
        
        Returns:
            Dictionary with scan results including findings and risk score
        """
        
        start_time = time.time()
        
        # Stage 1: Input validation
        validation_error = self._validate_input(target, target_type)
        if validation_error:
            return {
                'success': False,
                'error': validation_error,
                'execution_time': time.time() - start_time,
            }
        
        # Determine which analyzers to run
        if run_analyzers is None:
            run_analyzers = list(self.analyzers.keys())
        
        # Stage 2: Execute analyzers
        analyzer_results = self._run_analyzers(
            target, target_type, content, run_analyzers, **kwargs
        )
        
        # Extract raw findings from all analyzers
        raw_findings = []
        for analyzer_name, result in analyzer_results.items():
            raw_findings.extend(result.findings)
        
        # Stage 3: Normalize findings
        normalized_findings = self.normalizer.normalize(raw_findings)
        
        # Stage 4: Deduplicate findings
        deduped_findings = self._deduplicate_findings(normalized_findings)
        
        # Stage 5: Calculate risk score
        risk_score = self.risk_scorer.calculate_score(deduped_findings)
        
        # Stage 6: Assemble metadata
        result = {
            'success': True,
            'target': target,
            'target_type': target_type,
            'scan_timestamp': datetime.now().isoformat(),
            'execution_time': time.time() - start_time,
            'findings': deduped_findings,
            'findings_count': len(deduped_findings),
            'risk_score': risk_score,
            'analyzer_results': {
                name: {
                    'available': res.available,
                    'error': res.error,
                    'findings_count': len(res.findings),
                    'execution_time': res.execution_time,
                } for name, res in analyzer_results.items()
            },
        }
        
        logger.info(
            f"WebIntel scan completed: {target} | "
            f"Risk: {risk_score} | Findings: {len(deduped_findings)} | "
            f"Time: {result['execution_time']:.2f}s"
        )
        
        return result
    
    def _validate_input(self, target: str, target_type: str) -> str:
        """
        Validate input parameters.
        
        Returns:
            Error message if invalid, empty string if valid
        """
        
        if not target or len(target) > 2048:
            return "Target must be between 1 and 2048 characters"
        
        if target_type not in ('url', 'domain', 'ip'):
            return f"Invalid target type: {target_type}. Must be 'url', 'domain', or 'ip'"
        
        return ""
    
    def _run_analyzers(
        self,
        target: str,
        target_type: str,
        content: str,
        run_analyzers: List[str],
        **kwargs
    ) -> Dict[str, AnalyzerResult]:
        """
        Execute all specified analyzers.
        
        In production, these would run in parallel (asyncio, threading, or distributed).
        Currently runs sequentially.
        """
        
        results = {}
        
        for analyzer_name in run_analyzers:
            if analyzer_name not in self.analyzers:
                logger.warning(f"Unknown analyzer: {analyzer_name}")
                continue
            
            analyzer = self.analyzers[analyzer_name]
            
            try:
                start = time.time()
                
                # Check availability
                if not analyzer.is_available():
                    results[analyzer_name] = AnalyzerResult(
                        available=False,
                        error=f"{analyzer_name} analyzer not available"
                    )
                    continue
                
                # Execute analyzer
                result = analyzer.analyze(
                    target,
                    target_type,
                    content=content,
                    **kwargs
                )
                
                result.execution_time = time.time() - start
                results[analyzer_name] = result
                
                logger.debug(
                    f"{analyzer_name} analyzer: "
                    f"{len(result.findings)} findings | "
                    f"{result.execution_time:.2f}s"
                )
                
            except Exception as e:
                logger.error(f"Analyzer {analyzer_name} failed: {e}")
                results[analyzer_name] = AnalyzerResult(
                    available=False,
                    error=str(e)
                )
        
        return results
    
    def _deduplicate_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate findings using fingerprint matching.
        
        Keeps highest severity version of each unique finding.
        """
        
        if not findings:
            return []
        
        # Group by fingerprint
        fingerprinted = {}
        for finding in findings:
            fp = finding.get('fingerprint')
            
            if not fp:
                # No fingerprint, keep as-is
                finding['fingerprint'] = self._generate_fingerprint(finding)
                fp = finding['fingerprint']
            
            if fp not in fingerprinted:
                fingerprinted[fp] = finding
            else:
                # Keep higher severity
                existing_severity = self._severity_rank(fingerprinted[fp]['severity'])
                new_severity = self._severity_rank(finding['severity'])
                
                if new_severity > existing_severity:
                    fingerprinted[fp] = finding
        
        return list(fingerprinted.values())
    
    @staticmethod
    def _generate_fingerprint(finding: Dict[str, Any]) -> str:
        """Generate normalized fingerprint for finding."""
        title = finding.get('title', '').lower().strip()
        category = finding.get('category', '').lower().strip()
        
        # Simple fingerprint: category + first 20 chars of title
        return f"{category}:{title[:20]}".replace(' ', '_')
    
    @staticmethod
    def _severity_rank(severity: str) -> int:
        """Convert severity to numeric rank for comparison."""
        ranks = {
            'critical': 5,
            'high': 4,
            'medium': 3,
            'low': 2,
            'info': 1,
        }
        return ranks.get(severity, 0)
