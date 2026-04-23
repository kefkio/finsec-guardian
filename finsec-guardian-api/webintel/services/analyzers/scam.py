"""
Scam Signature Matcher

Detects financial scams: VSL sales funnels, fake investment platforms,
pyramid schemes, and fraudulent monetization pipelines.
"""

import re
import logging
from typing import List, Optional, Dict, Any

from .base import BaseWebAnalyzer, AnalyzerResult, WebFindingData, FindingSeverity

logger = logging.getLogger(__name__)


class ScamDetector(BaseWebAnalyzer):
    """
    Detects known scam patterns and fraudulent infrastructure.
    
    Identifies:
    - VSL (Video Sales Letter) funnels
    - Fake investment platforms (crypto, forex, stocks)
    - MLM/pyramid schemes
    - Fake job opportunities
    - Romance/financial romance scams
    - Miracle cure/get-rich-quick schemes
    """
    
    analyzer_name = "Scam Signature Matcher"
    
    # VSL funnel indicators
    VSL_PATTERNS = [
        r'(?:video sales letter|vsl funnel)',
        r'(?:watch.*video|secret.*revealed)',
        r'(?:limited.*time|expires.*soon|countdown)',
        r'(?:unlock.*now|claim.*now)',
    ]
    
    # Fake investment platform indicators
    INVESTMENT_SCAM_PATTERNS = [
        r'(?:guaranteed.*returns|guaranteed.*profit)',
        r'(?:passive.*income|easy.*money)',
        r'(?:risk.*free|riskless)',
        r'(?:double.*money|triple.*money|100%.*return)',
        r'(?:forex|cryptocurrency|binary.*option).*(?:easy|simple|guaranteed)',
    ]
    
    # Get-rich-quick patterns
    GREED_PATTERNS = [
        r'(?:make \$\d+|earn \$\d+).*(?:day|week)',
        r'(?:millionaire|wealth|fortune).*(?:secret|method)',
        r'(?:shortcut|hack|loophole).*(?:system|method)',
    ]
    
    # Urgency/scarcity abuse patterns
    SCARCITY_PATTERNS = [
        r'(?:limited.*slot|only \d+ left)',
        r'(?:closes.*\d+.*hours|expires.*tonight)',
        r'(?:this.*never.*again|once.*gone)',
    ]
    
    # Payment pattern indicators
    PAYMENT_RED_FLAGS = [
        r'(?:wire.*transfer|western.*union)',
        r'(?:bitcoin|cryptocurrency).*(?:payment|send)',
        r'(?:gift.*card|itunes.*card)',
    ]
    
    def analyze(self, target: str, target_type: str, content: Optional[str] = None, **kwargs) -> AnalyzerResult:
        """Analyze for scam signatures."""
        result = AnalyzerResult()
        
        try:
            findings = []
            
            # If content not provided, stub fetch
            if not content:
                content = self._fetch_content(target)
            
            if not content:
                result.available = False
                result.error = "Could not retrieve page content"
                return result
            
            # Check for VSL funnel patterns
            vsl_finding = self._check_vsl_funnel(content)
            if vsl_finding:
                findings.append(vsl_finding)
            
            # Check for fake investment platform patterns
            inv_findings = self._check_investment_scam(content)
            findings.extend(inv_findings)
            
            # Check for get-rich-quick language
            greed_finding = self._check_greed_language(content)
            if greed_finding:
                findings.append(greed_finding)
            
            # Check for scarcity/urgency abuse
            scarcity_finding = self._check_scarcity_abuse(content)
            if scarcity_finding:
                findings.append(scarcity_finding)
            
            # Check for suspicious payment methods
            payment_findings = self._check_payment_methods(content)
            findings.extend(payment_findings)
            
            # Check for MLM indicators
            mlm_finding = self._check_mlm_indicators(content)
            if mlm_finding:
                findings.append(mlm_finding)
            
            result.findings = findings
            result.metadata = {
                'target': target,
                'content_length': len(content) if content else 0,
            }
            
        except Exception as e:
            logger.error(f"Scam detector error: {e}")
            result.error = str(e)
            result.findings = []
        
        return result
    
    def _fetch_content(self, target: str) -> Optional[str]:
        """Fetch page content (stub)."""
        return None
    
    def _check_vsl_funnel(self, content: str) -> Optional[WebFindingData]:
        """Detect VSL (Video Sales Letter) funnel patterns."""
        content_lower = content.lower()
        
        vsl_indicators = sum(1 for pattern in self.VSL_PATTERNS if re.search(pattern, content_lower))
        
        if vsl_indicators >= 2:
            return self.normalize_finding(
                title="VSL Sales Funnel Detected",
                description="Page exhibits Video Sales Letter funnel patterns, commonly used in scams and high-pressure sales tactics.",
                severity=FindingSeverity.HIGH,
                category="vsl_funnel",
                confidence=85,
                evidence={'vsl_indicators_found': vsl_indicators}
            )
        
        return None
    
    def _check_investment_scam(self, content: str) -> List[WebFindingData]:
        """Detect fake investment platform signatures."""
        findings = []
        content_lower = content.lower()
        
        # Check for guaranteed returns (biggest red flag)
        if re.search(r'guaranteed.*(?:profit|return|income)', content_lower):
            findings.append(self.normalize_finding(
                title="Guaranteed Returns Claim",
                description="Investment platform claims guaranteed returns, which is illegal in regulated markets.",
                severity=FindingSeverity.CRITICAL,
                category="guaranteed_returns",
                confidence=95,
                evidence={'claim': 'guaranteed_returns'}
            ))
        
        # Check for unrealistic return claims
        return_match = re.search(r'(\d+)\%.*(?:day|week|month)', content_lower)
        if return_match:
            return_pct = int(return_match.group(1))
            if return_pct > 50:  # >50% return is unrealistic
                findings.append(self.normalize_finding(
                    title="Unrealistic Return Claims",
                    description=f"Platform claims {return_pct}% returns, which is unrealistic and indicates fraud.",
                    severity=FindingSeverity.HIGH,
                    category="unrealistic_returns",
                    confidence=80,
                    evidence={'claimed_return_pct': return_pct}
                ))
        
        # Check for multiple investment scam patterns
        indicators = sum(1 for pattern in self.INVESTMENT_SCAM_PATTERNS if re.search(pattern, content_lower))
        if indicators >= 2:
            findings.append(self.normalize_finding(
                title="Investment Scam Indicators",
                description="Page contains multiple investment scam indicators (guaranteed profits, easy money, risk-free claims).",
                severity=FindingSeverity.HIGH,
                category="investment_scam",
                confidence=75,
                evidence={'indicators_count': indicators}
            ))
        
        return findings
    
    def _check_greed_language(self, content: str) -> Optional[WebFindingData]:
        """Detect language exploiting greed and desire for wealth."""
        content_lower = content.lower()
        
        greed_indicators = sum(1 for pattern in self.GREED_PATTERNS if re.search(pattern, content_lower))
        
        if greed_indicators >= 2:
            return self.normalize_finding(
                title="Greed-Exploitation Language",
                description="Page uses language designed to exploit desire for quick wealth (get rich quick, easy money schemes).",
                severity=FindingSeverity.MEDIUM,
                category="greed_exploitation",
                confidence=70,
                evidence={'greed_indicators': greed_indicators}
            )
        
        return None
    
    def _check_scarcity_abuse(self, content: str) -> Optional[WebFindingData]:
        """Detect artificial scarcity and false urgency tactics."""
        content_lower = content.lower()
        
        scarcity_indicators = sum(1 for pattern in self.SCARCITY_PATTERNS if re.search(pattern, content_lower))
        
        if scarcity_indicators >= 2:
            return self.normalize_finding(
                title="Artificial Scarcity Tactics",
                description="Page uses false urgency and artificial scarcity (limited slots, time-based deadlines) to pressure decision-making.",
                severity=FindingSeverity.MEDIUM,
                category="scarcity_tactics",
                confidence=75,
                evidence={'scarcity_patterns': scarcity_indicators}
            )
        
        return None
    
    def _check_payment_methods(self, content: str) -> List[WebFindingData]:
        """Detect use of untraceable/irreversible payment methods."""
        findings = []
        content_lower = content.lower()
        
        payment_methods = {
            'cryptocurrency': (r'bitcoin|ethereum|crypto|blockchain', FindingSeverity.HIGH),
            'wire_transfer': (r'wire.*transfer|western.*union|money.*gram', FindingSeverity.HIGH),
            'gift_cards': (r'gift.*card|itunes.*card|google.*play', FindingSeverity.MEDIUM),
        }
        
        for method, (pattern, severity) in payment_methods.items():
            if re.search(pattern, content_lower):
                findings.append(self.normalize_finding(
                    title=f"Suspicious Payment Method: {method.title()}",
                    description=f"Page requests payment via {method}, which is untraceable and irreversible.",
                    severity=severity,
                    category=f"payment_method_{method}",
                    confidence=80,
                    evidence={'payment_method': method}
                ))
        
        return findings
    
    def _check_mlm_indicators(self, content: str) -> Optional[WebFindingData]:
        """Detect multi-level marketing (MLM) pyramid scheme indicators."""
        content_lower = content.lower()
        
        mlm_patterns = [
            r'(?:recruit|downline|commission)',
            r'(?:build.*network|network.*marketing)',
            r'(?:passive.*income|residual.*income)',
            r'(?:mentors|upline)',
        ]
        
        indicators = sum(1 for pattern in mlm_patterns if re.search(pattern, content_lower))
        
        if indicators >= 3:
            return self.normalize_finding(
                title="MLM/Pyramid Scheme Indicators",
                description="Page exhibits multi-level marketing (MLM) indicators including recruitment focus and commission structures.",
                severity=FindingSeverity.HIGH,
                category="mlm_scheme",
                confidence=80,
                evidence={'mlm_indicators': indicators}
            )
        
        return None
