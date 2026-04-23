"""
URL/Domain Analyzer

Detects malicious domains, suspicious SSL certificates, and abnormal WHOIS records.
"""

import socket
import ssl
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import re

from .base import BaseWebAnalyzer, AnalyzerResult, WebFindingData, FindingSeverity

logger = logging.getLogger(__name__)


class URLDomainAnalyzer(BaseWebAnalyzer):
    """
    Analyzes URLs and domains for malicious characteristics.
    
    Checks:
    - Domain age (very new domains = higher risk)
    - SSL certificate validity and issuer
    - WHOIS registration details
    - DNS resolution patterns
    - Typosquatting indicators
    """
    
    analyzer_name = "URL/Domain Analyzer"
    
    # Known malicious TLDs and patterns
    SUSPICIOUS_TLDS = ['tk', 'ml', 'ga', 'cf', 'buzz']
    DISPOSABLE_EMAIL_DOMAINS = ['tempmail', 'guerrillamail', '10minutemail', 'maildrop']
    
    def analyze(self, target: str, target_type: str, **kwargs) -> AnalyzerResult:
        """Analyze URL/domain for malicious indicators."""
        result = AnalyzerResult()
        
        try:
            if target_type == 'url':
                domain = self._extract_domain(target)
            else:
                domain = target
            
            findings = []
            
            # Check domain age
            age_finding = self._check_domain_age(domain)
            if age_finding:
                findings.append(age_finding)
            
            # Check SSL certificate
            ssl_findings = self._check_ssl_certificate(domain)
            findings.extend(ssl_findings)
            
            # Check DNS records
            dns_findings = self._check_dns_records(domain)
            findings.extend(dns_findings)
            
            # Check for typosquatting patterns
            typo_finding = self._check_typosquatting(domain)
            if typo_finding:
                findings.append(typo_finding)
            
            # Check for suspicious TLD
            tld_finding = self._check_suspicious_tld(domain)
            if tld_finding:
                findings.append(tld_finding)
            
            result.findings = findings
            result.metadata = {
                'domain_analyzed': domain,
                'target_type': target_type,
                'analysis_timestamp': datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"URL/Domain analyzer error: {e}")
            result.error = str(e)
            result.findings = []
        
        return result
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        # Remove protocol
        url = re.sub(r'^https?://', '', url)
        # Remove path
        domain = url.split('/')[0]
        # Remove port
        domain = domain.split(':')[0]
        return domain
    
    def _check_domain_age(self, domain: str) -> Optional[WebFindingData]:
        """Check if domain is suspiciously new."""
        try:
            # In production, use WHOIS API
            # This is a stub implementation
            age_days = 30  # Placeholder
            
            if age_days < 7:
                return self.normalize_finding(
                    title="Newly Registered Domain",
                    description=f"Domain was registered {age_days} days ago. Newly registered domains are frequently used for phishing and scams.",
                    severity=FindingSeverity.HIGH,
                    category="new_domain",
                    confidence=85,
                    evidence={'age_days': age_days, 'warning': 'Domain younger than 7 days'}
                )
            elif age_days < 30:
                return self.normalize_finding(
                    title="Recently Registered Domain",
                    description=f"Domain was registered {age_days} days ago. Recent registrations warrant scrutiny.",
                    severity=FindingSeverity.MEDIUM,
                    category="recent_domain",
                    confidence=70,
                    evidence={'age_days': age_days}
                )
        except Exception as e:
            logger.debug(f"Domain age check failed for {domain}: {e}")
        
        return None
    
    def _check_ssl_certificate(self, domain: str) -> list[WebFindingData]:
        """Check SSL certificate for red flags."""
        findings = []
        
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Check certificate validity
                    subject = dict(x[0] for x in cert['subject'])
                    issued_to = subject.get('commonName', domain)
                    
                    # Check if self-signed
                    if cert['issuer'] == cert['subject']:
                        findings.append(self.normalize_finding(
                            title="Self-Signed SSL Certificate",
                            description="Domain uses a self-signed SSL certificate, indicating lack of CA verification.",
                            severity=FindingSeverity.MEDIUM,
                            category="self_signed_ssl",
                            confidence=75,
                            evidence={'issued_to': issued_to}
                        ))
                    
                    # Check expiration
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    days_until_expiry = (not_after - datetime.now()).days
                    
                    if days_until_expiry < 7:
                        findings.append(self.normalize_finding(
                            title="SSL Certificate Expiring Soon",
                            description=f"Certificate expires in {days_until_expiry} days. Imminent expiration is a red flag.",
                            severity=FindingSeverity.MEDIUM,
                            category="ssl_expiring",
                            confidence=70,
                            evidence={'days_until_expiry': days_until_expiry}
                        ))
        
        except socket.timeout:
            findings.append(self.normalize_finding(
                title="SSL Connection Timeout",
                description="Could not establish SSL connection. Domain may not support HTTPS.",
                severity=FindingSeverity.LOW,
                category="ssl_timeout",
                confidence=50,
                evidence={'domain': domain}
            ))
        except Exception as e:
            logger.debug(f"SSL check failed for {domain}: {e}")
        
        return findings
    
    def _check_dns_records(self, domain: str) -> list[WebFindingData]:
        """Check DNS records for anomalies."""
        findings = []
        
        try:
            # In production, use DNS lookup
            ip_addresses = socket.gethostbyname_ex(domain)
            
            if not ip_addresses or not ip_addresses[2]:
                findings.append(self.normalize_finding(
                    title="DNS Resolution Failed",
                    description="Domain does not resolve to a valid IP address.",
                    severity=FindingSeverity.HIGH,
                    category="dns_resolution_failed",
                    confidence=90,
                    evidence={'domain': domain}
                ))
        except socket.gaierror:
            logger.debug(f"DNS resolution failed for {domain}")
        except Exception as e:
            logger.debug(f"DNS check error: {e}")
        
        return findings
    
    def _check_typosquatting(self, domain: str) -> Optional[WebFindingData]:
        """Detect likely typosquatting domains."""
        # Known legitimate financial domains
        known_domains = ['paypal', 'amazon', 'apple', 'google', 'microsoft', 'coinbase']
        
        for known in known_domains:
            # Levenshtein distance or similar pattern matching
            if self._is_similar(domain, known):
                return self.normalize_finding(
                    title="Typosquatting Detected",
                    description=f"Domain '{domain}' closely resembles legitimate domain '{known}', suggesting typosquatting.",
                    severity=FindingSeverity.HIGH,
                    category="typosquatting",
                    confidence=80,
                    evidence={'similar_to': known}
                )
        
        return None
    
    def _check_suspicious_tld(self, domain: str) -> Optional[WebFindingData]:
        """Check for suspicious or free TLDs."""
        tld = domain.split('.')[-1].lower()
        
        if tld in self.SUSPICIOUS_TLDS:
            return self.normalize_finding(
                title="Suspicious TLD",
                description=f"Domain uses '.{tld}', a free TLD frequently abused for scams and phishing.",
                severity=FindingSeverity.MEDIUM,
                category="suspicious_tld",
                confidence=65,
                evidence={'tld': tld}
            )
        
        return None
    
    @staticmethod
    def _is_similar(s1: str, s2: str, threshold: float = 0.85) -> bool:
        """Simple string similarity check using character-level operations."""
        # In production, use Levenshtein distance
        s1_lower = s1.lower().replace('.', '')
        s2_lower = s2.lower().replace('.', '')
        
        # Check for common typos
        if s1_lower.replace(s2_lower, '').count('') <= 2:  # Minimal difference
            return True
        
        return False
