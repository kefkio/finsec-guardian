"""
Monetization Pipeline Analyzer

Detects fraudulent monetization infrastructure: ad networks, affiliate tracking,
payment processors, and money laundering pipelines.
"""

import re
import logging
from typing import List, Optional

from .base import BaseWebAnalyzer, AnalyzerResult, WebFindingData, FindingSeverity

logger = logging.getLogger(__name__)


class MonetizationAnalyzer(BaseWebAnalyzer):
    """
    Analyzes monetization pipeline for fraud indicators.
    
    Detects:
    - Suspicious affiliate networks and tracking
    - High-risk payment processors (often used by scams)
    - Ad fraud networks
    - Cryptocurrency payment infrastructure
    - Money laundering indicators
    - Suspicious refund/chargeback patterns
    """
    
    analyzer_name = "Monetization Pipeline Analyzer"
    
    # High-risk affiliate networks
    SUSPECT_AFFILIATE_NETWORKS = [
        'sharesale',  # Used by scam networks
        'cpa-network',  # Cost-per-action, often fraud
        'a8.net',  # Japanese affiliate network with fraud issues
        'hitbox',  # Tracking network with poor compliance
    ]
    
    # Tracking scripts associated with fraud
    FRAUD_TRACKING_PATTERNS = [
        r'(?:fbq|facebook.*pixel)',  # FB pixel for audience building (not inherently bad but combined with other factors)
        r'(?:gtag|google.*analytics)',  # Analytics
        r'(?:amplitude|mixpanel)',  # Behavioral tracking
    ]
    
    # High-risk payment processors
    HIGH_RISK_PROCESSORS = [
        r'payoneer',  # Often flagged for high-risk merchants
        r'stripe.*connect',  # When used with high-risk accounts
        r'2checkout',  # Known for high-risk merchant acceptance
        r'skrill',  # Money transfer often used for fraud
        r'neteller',  # Similar to Skrill
    ]
    
    # Cryptocurrency payment indicators
    CRYPTO_PAYMENT_PATTERNS = [
        r'0x[a-fA-F0-9]{40}',  # Ethereum address
        r'(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}',  # Bitcoin address
        r'(?:coinbase commerce|stripe.*crypto)',
    ]
    
    # Money laundering red flags
    MONEY_LAUNDERING_PATTERNS = [
        r'(?:wire.*transfer|international.*transfer)',
        r'(?:cash.*out|convert.*to.*fiat)',
        r'(?:money.*service|currency.*exchange)',
    ]
    
    # Refund manipulation patterns
    REFUND_FRAUD_PATTERNS = [
        r'(?:no.*refund|non-refundable)',
        r'(?:billing.*cycle|subscription)',
        r'(?:difficult.*to.*cancel|hard.*to.*unsubscribe)',
    ]
    
    def analyze(self, target: str, target_type: str, content: Optional[str] = None, **kwargs) -> AnalyzerResult:
        """Analyze monetization pipeline."""
        result = AnalyzerResult()
        
        try:
            findings = []
            
            if not content:
                content = self._fetch_content(target)
            
            if not content:
                result.available = False
                result.error = "Could not retrieve page content"
                return result
            
            # Check for suspicious payment processors
            processor_findings = self._check_payment_processors(content)
            findings.extend(processor_findings)
            
            # Check for cryptocurrency infrastructure
            crypto_finding = self._check_crypto_infrastructure(content)
            if crypto_finding:
                findings.append(crypto_finding)
            
            # Check for ad fraud networks
            ad_findings = self._check_ad_networks(content)
            findings.extend(ad_findings)
            
            # Check for money laundering indicators
            ml_finding = self._check_money_laundering(content)
            if ml_finding:
                findings.append(ml_finding)
            
            # Check for refund manipulation
            refund_finding = self._check_refund_policies(content)
            if refund_finding:
                findings.append(refund_finding)
            
            # Check for suspicious affiliate networks
            affiliate_findings = self._check_affiliate_networks(content)
            findings.extend(affiliate_findings)
            
            result.findings = findings
            result.metadata = {'target': target}
            
        except Exception as e:
            logger.error(f"Monetization analyzer error: {e}")
            result.error = str(e)
            result.findings = []
        
        return result
    
    def _fetch_content(self, target: str) -> Optional[str]:
        """Fetch page content (stub)."""
        return None
    
    def _check_payment_processors(self, content: str) -> List[WebFindingData]:
        """Detect high-risk payment processors."""
        findings = []
        content_lower = content.lower()
        
        for pattern in self.HIGH_RISK_PROCESSORS:
            if re.search(pattern, content_lower):
                processor = re.search(pattern, content_lower).group(0)
                findings.append(self.normalize_finding(
                    title="High-Risk Payment Processor Detected",
                    description=f"Page uses {processor}, a payment processor frequently associated with high-risk merchants.",
                    severity=FindingSeverity.HIGH,
                    category="high_risk_processor",
                    confidence=75,
                    evidence={'processor': processor}
                ))
        
        return findings
    
    def _check_crypto_infrastructure(self, content: str) -> Optional[WebFindingData]:
        """Detect cryptocurrency payment infrastructure."""
        # Check for wallet addresses or crypto payment processors
        if re.search(r'coinbase.*commerce|stripe.*crypto', content.lower()):
            return self.normalize_finding(
                title="Cryptocurrency Payment Infrastructure",
                description="Page accepts cryptocurrency payments, often preferred by scammers for irreversibility.",
                severity=FindingSeverity.MEDIUM,
                category="crypto_payment",
                confidence=70,
                evidence={'payment_type': 'cryptocurrency'}
            )
        
        # Check for specific wallet addresses (more suspicious)
        if re.search(r'0x[a-fA-F0-9]{40}|bc1[a-z0-9]{39,59}', content):
            return self.normalize_finding(
                title="Direct Cryptocurrency Wallet Detected",
                description="Page contains direct cryptocurrency wallet address, bypassing traditional payment processors.",
                severity=FindingSeverity.HIGH,
                category="direct_crypto_wallet",
                confidence=85,
                evidence={'wallet_type': 'direct'}
            )
        
        return None
    
    def _check_ad_networks(self, content: str) -> List[WebFindingData]:
        """Detect ad fraud and malvertising networks."""
        findings = []
        content_lower = content.lower()
        
        # Check for multiple tracking scripts (ad fraud indicator)
        tracking_count = sum(1 for pattern in self.FRAUD_TRACKING_PATTERNS if re.search(pattern, content_lower))
        
        if tracking_count >= 3:
            findings.append(self.normalize_finding(
                title="Excessive Tracking Infrastructure",
                description="Page contains multiple tracking/analytics scripts, suggesting ad fraud or extensive user profiling.",
                severity=FindingSeverity.MEDIUM,
                category="excessive_tracking",
                confidence=70,
                evidence={'tracking_scripts_count': tracking_count}
            ))
        
        # Check for known malvertising networks
        if re.search(r'(?:adroll|criteo|taboola|outbrain).*(?:config|script)', content_lower):
            findings.append(self.normalize_finding(
                title="Native Advertising Network Detected",
                description="Page uses native advertising networks, sometimes used for deceptive ad placement.",
                severity=FindingSeverity.LOW,
                category="native_ads",
                confidence=60,
                evidence={'ad_type': 'native_advertising'}
            ))
        
        return findings
    
    def _check_money_laundering(self, content: str) -> Optional[WebFindingData]:
        """Detect money laundering infrastructure indicators."""
        content_lower = content.lower()
        
        ml_indicators = sum(1 for pattern in self.MONEY_LAUNDERING_PATTERNS if re.search(pattern, content_lower))
        
        if ml_indicators >= 2:
            return self.normalize_finding(
                title="Money Laundering Infrastructure Indicators",
                description="Page exhibits multiple money laundering indicators (international transfers, fiat conversion).",
                severity=FindingSeverity.HIGH,
                category="money_laundering",
                confidence=80,
                evidence={'ml_indicators': ml_indicators}
            )
        
        return None
    
    def _check_refund_policies(self, content: str) -> Optional[WebFindingData]:
        """Detect deceptive or non-existent refund policies."""
        content_lower = content.lower()
        
        # Check for absence of refund policy
        has_refund_policy = re.search(r'refund.*policy|return.*policy|money.*back', content_lower)
        
        if not has_refund_policy:
            return self.normalize_finding(
                title="No Refund Policy Found",
                description="Page lacks a clearly visible refund or return policy, a common scam indicator.",
                severity=FindingSeverity.HIGH,
                category="no_refund_policy",
                confidence=80,
                evidence={'policy_found': False}
            )
        
        # Check for non-refundable language
        no_refund_match = re.search(r'(?:no|non-|final)\s+(?:refund|return)', content_lower)
        if no_refund_match:
            return self.normalize_finding(
                title="Non-Refundable Purchase Warning",
                description="Page explicitly states purchases are non-refundable, removing buyer protection.",
                severity=FindingSeverity.MEDIUM,
                category="non_refundable",
                confidence=75,
                evidence={'clause': 'non-refundable'}
            )
        
        # Check for subscription auto-renewal language
        if re.search(r'auto.*renew|recurring|subscription', content_lower):
            return self.normalize_finding(
                title="Automatic Subscription Renewal",
                description="Page contains automatic subscription renewal language, often used in deceptive billing practices.",
                severity=FindingSeverity.MEDIUM,
                category="auto_renewal",
                confidence=70,
                evidence={'payment_model': 'subscription'}
            )
        
        return None
    
    def _check_affiliate_networks(self, content: str) -> List[WebFindingData]:
        """Detect suspicious affiliate networks."""
        findings = []
        content_lower = content.lower()
        
        for network in self.SUSPECT_AFFILIATE_NETWORKS:
            if network.lower() in content_lower:
                findings.append(self.normalize_finding(
                    title="Suspicious Affiliate Network Detected",
                    description=f"Page uses {network}, an affiliate network with known fraud association.",
                    severity=FindingSeverity.MEDIUM,
                    category="suspect_affiliate",
                    confidence=70,
                    evidence={'network': network}
                ))
        
        return findings
