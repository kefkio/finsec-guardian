"""
WebIntel Risk Scorer

Calculates composite risk score from normalized findings.
Uses exponential saturation model similar to scanner/services/risk_scorer.py
"""

import logging
import math
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class WebRiskScorer:
    """
    Calculates composite web intelligence risk score (0-100).
    
    Model: Exponential saturation $R = 100 \times (1 - e^{-kS})$ with adjustments:
    - Base: Weighted severity contributions
    - Critical floor: Any critical finding forces minimum score of 80
    - Diversity bonus: Unique finding categories add confidence
    - Analyzer reliability: Weight results by analyzer confidence
    """
    
    # Exponential saturation parameters
    SATURATION_K = 0.08
    CRITICAL_FLOOR = 80
    
    # Severity weights (contribution to saturation)
    SEVERITY_WEIGHTS = {
        'critical': 3.0,
        'high': 1.5,
        'medium': 0.8,
        'low': 0.3,
        'info': 0.1,
    }
    
    # Category diversity bonus
    CATEGORY_BONUS = 0.5  # Per unique category
    MAX_CATEGORY_BONUS = 5.0
    
    # Analyzer reliability scores (0.5-1.0)
    ANALYZER_RELIABILITY = {
        'URL/Domain Analyzer': 0.85,
        'Phishing Detector': 0.90,
        'Scam Signature Matcher': 0.80,
        'Social Engineering Analyzer': 0.75,
        'Monetization Pipeline Analyzer': 0.70,
    }
    
    def calculate_score(self, findings: List[Dict[str, Any]]) -> int:
        """
        Calculate composite risk score.
        
        Args:
            findings: List of normalized findings
        
        Returns:
            Risk score (0-100)
        """
        
        if not findings:
            return 0
        
        # Calculate base score from severity contributions
        base_score = self._calculate_base_score(findings)
        
        # Apply critical floor
        if any(f.get('severity') == 'critical' for f in findings):
            base_score = max(base_score, self.CRITICAL_FLOOR)
        
        # Apply diversity bonus
        unique_categories = len(set(f.get('category') for f in findings))
        diversity_bonus = min(
            unique_categories * self.CATEGORY_BONUS,
            self.MAX_CATEGORY_BONUS
        )
        base_score = min(base_score + diversity_bonus, 100)
        
        # Apply confidence weighting
        avg_confidence = sum(f.get('confidence_score', 50) for f in findings) / len(findings)
        confidence_factor = 0.5 + (avg_confidence / 100 * 0.5)  # 0.5-1.0
        
        final_score = int(base_score * confidence_factor)
        
        logger.debug(
            f"Risk Score Calculation: "
            f"findings={len(findings)}, "
            f"base={base_score:.1f}, "
            f"diversity_bonus={diversity_bonus:.1f}, "
            f"confidence_factor={confidence_factor:.2f}, "
            f"final={final_score}"
        )
        
        return final_score
    
    def _calculate_base_score(self, findings: List[Dict[str, Any]]) -> float:
        """
        Calculate base score using exponential saturation model.
        
        Accounts for analyzer reliability in weighting.
        """
        
        if not findings:
            return 0
        
        # Sum weighted severity contributions
        total_weight = 0.0
        
        for finding in findings:
            severity = finding.get('severity', 'info').lower()
            analyzer = finding.get('analyzer', 'unknown')
            confidence = finding.get('confidence_score', 50)
            
            # Base weight from severity
            weight = self.SEVERITY_WEIGHTS.get(severity, 0.1)
            
            # Adjust by analyzer reliability
            reliability = self.ANALYZER_RELIABILITY.get(analyzer, 0.75)
            
            # Adjust by finding confidence
            confidence_factor = confidence / 100.0
            
            # Final weight
            finding_weight = weight * reliability * confidence_factor
            total_weight += finding_weight
        
        # Apply exponential saturation
        # R = 100 * (1 - e^(-k*S))
        saturated_score = 100 * (1 - math.exp(-self.SATURATION_K * total_weight))
        
        return saturated_score
    
    def get_risk_level(self, score: int) -> str:
        """Classify risk score into severity level."""
        if score >= 80:
            return "CRITICAL"
        elif score >= 60:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        elif score >= 20:
            return "LOW"
        else:
            return "INFO"
    
    def explain_score(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate detailed explanation of risk score calculation.
        
        Useful for debugging and transparency.
        """
        
        if not findings:
            return {
                'score': 0,
                'level': 'INFO',
                'explanation': 'No findings detected',
                'contributing_factors': [],
            }
        
        score = self.calculate_score(findings)
        level = self.get_risk_level(score)
        
        # Analyze contributing factors
        factors = []
        
        # Critical findings
        critical_count = len([f for f in findings if f.get('severity') == 'critical'])
        if critical_count > 0:
            factors.append(f"{critical_count} critical finding(s) detected")
        
        # Category diversity
        unique_categories = len(set(f.get('category') for f in findings))
        if unique_categories > 1:
            factors.append(f"Diverse threat categories ({unique_categories})")
        
        # High confidence findings
        high_confidence = len([f for f in findings if f.get('confidence_score', 50) >= 80])
        if high_confidence > 0:
            factors.append(f"High-confidence findings ({high_confidence})")
        
        # Analyzer distribution
        analyzer_counts = {}
        for finding in findings:
            analyzer = finding.get('analyzer', 'unknown')
            analyzer_counts[analyzer] = analyzer_counts.get(analyzer, 0) + 1
        
        return {
            'score': score,
            'level': level,
            'total_findings': len(findings),
            'critical_findings': critical_count,
            'unique_categories': unique_categories,
            'contributing_factors': factors,
            'analyzer_breakdown': analyzer_counts,
            'explanation': self._generate_explanation(score, level, factors),
        }
    
    @staticmethod
    def _generate_explanation(score: int, level: str, factors: List[str]) -> str:
        """Generate human-readable explanation of score."""
        
        base_msg = f"Risk score {score}/100 ({level})"
        
        if not factors:
            return f"{base_msg}: No significant threats detected."
        
        factors_text = "; ".join(factors)
        
        if level == "CRITICAL":
            return f"{base_msg}: Immediate action required. {factors_text}"
        elif level == "HIGH":
            return f"{base_msg}: Multiple high-severity threats detected. {factors_text}"
        elif level == "MEDIUM":
            return f"{base_msg}: Moderate risk identified. {factors_text}"
        else:
            return f"{base_msg}: Low risk but requires monitoring. {factors_text}"
