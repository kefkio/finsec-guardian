"""
Social Engineering Analyzer

Detects psychological manipulation tactics used in financial deception:
authority exploitation, fear appeals, false scarcity, reciprocity abuse, etc.
"""

import re
import logging
from typing import List, Optional

from .base import BaseWebAnalyzer, AnalyzerResult, WebFindingData, FindingSeverity

logger = logging.getLogger(__name__)


class SocialEngineeringAnalyzer(BaseWebAnalyzer):
    """
    Analyzes content for social engineering and psychological manipulation tactics.
    
    Based on Cialdini's principles of influence:
    - Authority: Pretending to be officials, experts, celebrities
    - Scarcity: False urgency and limited availability
    - Reciprocity: Offering free value before requesting money
    - Consensus: False social proof (fake reviews, testimonials)
    - Liking: Building false rapport or similarity
    - Commitment: Getting initial small agreement before large ask
    """
    
    analyzer_name = "Social Engineering Analyzer"
    
    # Authority exploitation patterns
    AUTHORITY_PATTERNS = [
        r'(?:official|authorized|verified|approved)',
        r'(?:doctor|attorney|expert|specialist)',
        r'(?:government|fbi|irs|federal)',
        r'(?:official.*logo|certified.*badge)',
    ]
    
    # Fear and threat patterns
    FEAR_PATTERNS = [
        r'(?:urgent|emergency|critical)',
        r'(?:verify.*account|confirm.*identity)',
        r'(?:suspicious.*activity|unauthorized.*access)',
        r'(?:account.*will.*close|funds.*will.*freeze)',
        r'(?:legal.*action|lawsuit|prosecution)',
    ]
    
    # False social proof patterns
    SOCIAL_PROOF_PATTERNS = [
        r'(?:\d+.*people?.*(?:joined|bought|trust|recommend))',
        r'(?:(?:5|4) star|highly.*rated)',
        r'(?:as seen on|featured in)',
        r'(?:thousands.*(?:happy|satisfied))',
    ]
    
    # Reciprocity patterns (free offer before asking for payment)
    RECIPROCITY_PATTERNS = [
        r'(?:free.*(?:guide|ebook|report|training))',
        r'(?:no.*obligation|free.*trial)',
        r'(?:gift.*(?:valued at|\$))',
    ]
    
    # Commitment patterns (foot-in-door)
    COMMITMENT_PATTERNS = [
        r'(?:just.*click|quick.*step)',
        r'(?:first.*free|no.*commitment)',
        r'(?:sign.*up.*now|register.*free)',
    ]
    
    def analyze(self, target: str, target_type: str, content: Optional[str] = None, **kwargs) -> AnalyzerResult:
        """Analyze content for social engineering tactics."""
        result = AnalyzerResult()
        
        try:
            findings = []
            
            if not content:
                content = self._fetch_content(target)
            
            if not content:
                result.available = False
                result.error = "Could not retrieve page content"
                return result
            
            # Check for authority exploitation
            auth_finding = self._check_authority_exploitation(content)
            if auth_finding:
                findings.append(auth_finding)
            
            # Check for fear appeals
            fear_finding = self._check_fear_appeals(content)
            if fear_finding:
                findings.append(fear_finding)
            
            # Check for false social proof
            proof_finding = self._check_social_proof(content)
            if proof_finding:
                findings.append(proof_finding)
            
            # Check for reciprocity manipulation
            recip_finding = self._check_reciprocity(content)
            if recip_finding:
                findings.append(recip_finding)
            
            # Check for commitment tactics
            commit_finding = self._check_commitment_tactics(content)
            if commit_finding:
                findings.append(commit_finding)
            
            # Check for emotional manipulation
            emotion_findings = self._check_emotional_appeals(content)
            findings.extend(emotion_findings)
            
            result.findings = findings
            result.metadata = {'target': target}
            
        except Exception as e:
            logger.error(f"Social engineering analyzer error: {e}")
            result.error = str(e)
            result.findings = []
        
        return result
    
    def _fetch_content(self, target: str) -> Optional[str]:
        """Fetch page content (stub)."""
        return None
    
    def _check_authority_exploitation(self, content: str) -> Optional[WebFindingData]:
        """Detect false authority claims."""
        content_lower = content.lower()
        
        # Check for government impersonation
        if re.search(r'(?:official|legitimate).*(?:government|irs|fbi|federal)', content_lower):
            return self.normalize_finding(
                title="Potential Government Impersonation",
                description="Page claims to represent a government agency, a common phishing tactic.",
                severity=FindingSeverity.CRITICAL,
                category="government_impersonation",
                confidence=90,
                evidence={'impersonation_type': 'government'}
            )
        
        # Check for expert/celebrity impersonation
        if re.search(r'(?:as recommended by|endorsed by|celebrity).*\w+', content_lower):
            return self.normalize_finding(
                title="False Celebrity/Expert Endorsement",
                description="Page falsely claims endorsement by celebrities or experts.",
                severity=FindingSeverity.HIGH,
                category="false_endorsement",
                confidence=75,
                evidence={'endorsement_type': 'celebrity_or_expert'}
            )
        
        return None
    
    def _check_fear_appeals(self, content: str) -> Optional[WebFindingData]:
        """Detect manipulative fear-based appeals."""
        content_lower = content.lower()
        
        fear_indicators = sum(1 for pattern in self.FEAR_PATTERNS if re.search(pattern, content_lower))
        
        if fear_indicators >= 3:
            return self.normalize_finding(
                title="Manipulative Fear Appeals",
                description="Page uses multiple fear-based appeals to manipulate users into taking action.",
                severity=FindingSeverity.HIGH,
                category="fear_appeals",
                confidence=80,
                evidence={'fear_indicators': fear_indicators}
            )
        
        return None
    
    def _check_social_proof(self, content: str) -> Optional[WebFindingData]:
        """Detect fake social proof (reviews, testimonials, statistics)."""
        content_lower = content.lower()
        
        # Check for fake customer counts
        fake_customer_match = re.search(r'(\d+)\s+(?:million|thousand|customer|user|member)', content_lower)
        if fake_customer_match:
            count = int(fake_customer_match.group(1))
            if count > 100000:  # Suspiciously large
                return self.normalize_finding(
                    title="Suspicious Customer Statistics",
                    description=f"Page claims {count:,} customers, which may be fabricated social proof.",
                    severity=FindingSeverity.MEDIUM,
                    category="fake_statistics",
                    confidence=70,
                    evidence={'claimed_customers': count}
                )
        
        # Check for fake reviews/ratings
        proof_indicators = sum(1 for pattern in self.SOCIAL_PROOF_PATTERNS if re.search(pattern, content_lower))
        
        if proof_indicators >= 2:
            return self.normalize_finding(
                title="Potential Fake Social Proof",
                description="Page displays customer reviews/ratings that may be fabricated.",
                severity=FindingSeverity.MEDIUM,
                category="fake_reviews",
                confidence=65,
                evidence={'social_proof_indicators': proof_indicators}
            )
        
        return None
    
    def _check_reciprocity(self, content: str) -> Optional[WebFindingData]:
        """Detect reciprocity manipulation (free offer before paid ask)."""
        content_lower = content.lower()
        
        recip_indicators = sum(1 for pattern in self.RECIPROCITY_PATTERNS if re.search(pattern, content_lower))
        
        # Reciprocity alone is not malicious, but combined with other tactics is concerning
        if recip_indicators >= 2 and any(
            re.search(pattern, content_lower) for pattern in self.SCARCITY_PATTERNS
        ):
            return self.normalize_finding(
                title="Reciprocity Exploitation",
                description="Page uses free offers combined with artificial scarcity to manipulate users.",
                severity=FindingSeverity.MEDIUM,
                category="reciprocity_manipulation",
                confidence=70,
                evidence={'reciprocity_indicators': recip_indicators}
            )
        
        return None
    
    def _check_commitment_tactics(self, content: str) -> Optional[WebFindingData]:
        """Detect foot-in-door commitment tactics."""
        content_lower = content.lower()
        
        commit_indicators = sum(1 for pattern in self.COMMITMENT_PATTERNS if re.search(pattern, content_lower))
        
        if commit_indicators >= 2:
            return self.normalize_finding(
                title="Foot-in-Door Tactics",
                description="Page uses small commitment requests (free sign-up) before larger financial asks.",
                severity=FindingSeverity.LOW,
                category="commitment_tactics",
                confidence=70,
                evidence={'commitment_patterns': commit_indicators}
            )
        
        return None
    
    def _check_emotional_appeals(self, content: str) -> List[WebFindingData]:
        """Detect emotional manipulation language."""
        findings = []
        content_lower = content.lower()
        
        # FOMO (Fear of Missing Out)
        fomo_patterns = [r'never.*again', r'once.*gone', r'last.*chance', r'don\'t.*miss']
        if sum(1 for p in fomo_patterns if re.search(p, content_lower)) >= 2:
            findings.append(self.normalize_finding(
                title="FOMO (Fear of Missing Out) Manipulation",
                description="Page uses scarcity language to create fear of missing out.",
                severity=FindingSeverity.MEDIUM,
                category="fomo_manipulation",
                confidence=70,
                evidence={'tactic': 'fomo'}
            ))
        
        # Guilt or obligation language
        guilt_patterns = [r'you.*owe', r'must.*act', r'cannot.*refuse']
        if sum(1 for p in guilt_patterns if re.search(p, content_lower)) >= 1:
            findings.append(self.normalize_finding(
                title="Guilt/Obligation Language",
                description="Page uses language to create sense of obligation or guilt.",
                severity=FindingSeverity.LOW,
                category="guilt_appeals",
                confidence=65,
                evidence={'tactic': 'guilt'}
            ))
        
        return findings
    
    # Scarcity patterns for reference (could be combined)
    SCARCITY_PATTERNS = [
        r'(?:limited|only)',
        r'(?:expires|deadline)',
        r'(?:slots.*left|spots.*remaining)',
    ]
