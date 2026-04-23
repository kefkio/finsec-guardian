"""
Phishing Detector

Analyzes HTML content for phishing indicators: credential harvesting forms,
fake login pages, and deceptive layout patterns.
"""

import re
import logging
from typing import Dict, Any, Optional, List
from html.parser import HTMLParser

from .base import BaseWebAnalyzer, AnalyzerResult, WebFindingData, FindingSeverity

logger = logging.getLogger(__name__)


class FormExtractor(HTMLParser):
    """Extract forms from HTML content."""
    
    def __init__(self):
        super().__init__()
        self.forms = []
        self.current_form = None
        self.current_inputs = []
    
    def handle_starttag(self, tag, attrs):
        if tag == 'form':
            self.current_form = {'action': dict(attrs).get('action'), 'inputs': []}
        elif tag == 'input' and self.current_form is not None:
            input_attrs = dict(attrs)
            self.current_inputs.append({
                'type': input_attrs.get('type', 'text'),
                'name': input_attrs.get('name'),
                'placeholder': input_attrs.get('placeholder'),
            })
    
    def handle_endtag(self, tag):
        if tag == 'form' and self.current_form is not None:
            self.current_form['inputs'] = self.current_inputs
            self.forms.append(self.current_form)
            self.current_form = None
            self.current_inputs = []


class PhishingDetector(BaseWebAnalyzer):
    """
    Detects phishing pages and credential harvesting forms.
    
    Red flags:
    - Login-like forms (username/password fields)
    - Mismatch between form action and domain
    - Fake payment forms
    - Urgent action language
    - Redirect attempts
    """
    
    analyzer_name = "Phishing Detector"
    
    # Credential field name patterns
    CREDENTIAL_PATTERNS = [
        r'(?:user|login|email|username)',
        r'(?:pass|password|pwd)',
        r'(?:card|credit)',
    ]
    
    # Urgency language patterns
    URGENCY_PATTERNS = [
        r'(?:urgent|immediate|action required)',
        r'(?:verify|confirm|authenticate)',
        r'(?:unusual activity|suspicious|alert)',
        r'(?:expire|expir|limit|limited time)',
    ]
    
    def analyze(self, target: str, target_type: str, content: Optional[str] = None, **kwargs) -> AnalyzerResult:
        """Analyze webpage for phishing indicators."""
        result = AnalyzerResult()
        
        try:
            findings = []
            
            # If content not provided, in production would fetch it
            if not content:
                content = self._fetch_content(target)
            
            if not content:
                result.available = False
                result.error = "Could not retrieve page content"
                return result
            
            # Check for credential harvesting forms
            form_findings = self._check_credential_forms(content, target)
            findings.extend(form_findings)
            
            # Check for urgency language
            urgency_finding = self._check_urgency_language(content)
            if urgency_finding:
                findings.append(urgency_finding)
            
            # Check for redirect attempts
            redirect_findings = self._check_redirects(content)
            findings.extend(redirect_findings)
            
            # Check for spoofed brand elements
            spoof_findings = self._check_brand_spoofing(content, target)
            findings.extend(spoof_findings)
            
            result.findings = findings
            result.metadata = {
                'target': target,
                'content_length': len(content),
                'analysis_timestamp': None,
            }
            
        except Exception as e:
            logger.error(f"Phishing detector error: {e}")
            result.error = str(e)
            result.findings = []
        
        return result
    
    def _fetch_content(self, target: str) -> Optional[str]:
        """Fetch page content (stub - implement with requests library)."""
        # In production: import requests; return requests.get(target, timeout=5).text
        return None
    
    def _check_credential_forms(self, content: str, target: str) -> List[WebFindingData]:
        """Detect forms designed to harvest credentials."""
        findings = []
        
        try:
            parser = FormExtractor()
            parser.feed(content)
            
            for form in parser.forms:
                form_action = form.get('action', '')
                inputs = form.get('inputs', [])
                
                # Check if form looks like credential harvester
                input_types = [inp['type'] for inp in inputs]
                input_names = [inp['name'] or '' for inp in inputs]
                
                has_password = any('pass' in t.lower() for t in input_types + input_names)
                has_email = any('email' in n.lower() or 'user' in n.lower() for n in input_names)
                
                if has_password or (has_email and len(inputs) >= 2):
                    # Form looks like login form
                    is_cross_domain = form_action and target not in form_action
                    
                    severity = FindingSeverity.CRITICAL if is_cross_domain else FindingSeverity.HIGH
                    
                    findings.append(self.normalize_finding(
                        title="Credential Harvesting Form Detected",
                        description="Page contains a form requesting sensitive credentials (username/password/email).",
                        severity=severity,
                        category="credential_form",
                        confidence=90,
                        evidence={
                            'form_action': form_action,
                            'input_types': input_types,
                            'cross_domain': is_cross_domain,
                            'inputs_count': len(inputs),
                        }
                    ))
        
        except Exception as e:
            logger.debug(f"Form extraction error: {e}")
        
        return findings
    
    def _check_urgency_language(self, content: str) -> Optional[WebFindingData]:
        """Detect urgent action language used in phishing."""
        content_lower = content.lower()
        
        matches = []
        for pattern in self.URGENCY_PATTERNS:
            if re.search(pattern, content_lower):
                matches.append(pattern)
        
        if len(matches) >= 2:
            return self.normalize_finding(
                title="Urgent Action Language Detected",
                description="Page contains multiple urgent calls-to-action, a common phishing tactic.",
                severity=FindingSeverity.MEDIUM,
                category="urgency_language",
                confidence=75,
                evidence={'urgency_patterns_found': len(matches)}
            )
        
        return None
    
    def _check_redirects(self, content: str) -> List[WebFindingData]:
        """Detect redirect or JavaScript-based navigation attempts."""
        findings = []
        
        # Check for window.location patterns
        redirect_patterns = [
            r'window\.location\.href\s*=',
            r'window\.location\s*=',
            r'document\.location\s*=',
            r'location\.href\s*=',
        ]
        
        for pattern in redirect_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                findings.append(self.normalize_finding(
                    title="Redirect Script Detected",
                    description="Page contains JavaScript code that redirects users, potentially to a phishing site.",
                    severity=FindingSeverity.HIGH,
                    category="redirect_script",
                    confidence=80,
                    evidence={'pattern': pattern}
                ))
                break  # One finding is enough
        
        return findings
    
    def _check_brand_spoofing(self, content: str, target: str) -> List[WebFindingData]:
        """Detect spoofed brand names and logos."""
        findings = []
        
        # List of brands commonly spoofed
        brand_patterns = {
            'PayPal': [r'paypal', r'pp-logo'],
            'Apple': [r'apple', r'itunes', r'icloud'],
            'Microsoft': [r'microsoft', r'office365', r'outlook'],
            'Amazon': [r'amazon', r'aws'],
            'Bank of America': [r'bofa', r'bank of america'],
            'Wells Fargo': [r'wells fargo', r'wf-'],
            'Coinbase': [r'coinbase', r'crypto'],
        }
        
        content_lower = content.lower()
        
        for brand, patterns in brand_patterns.items():
            # Check if domain mentions brand but doesn't belong to them
            mentions_brand = any(re.search(p, content_lower) for p in patterns)
            is_official = brand.lower().replace(' ', '') in target.lower()
            
            if mentions_brand and not is_official:
                findings.append(self.normalize_finding(
                    title=f"Spoofed {brand} Brand Elements",
                    description=f"Page displays {brand} branding/logos but is hosted on a different domain.",
                    severity=FindingSeverity.CRITICAL,
                    category="brand_spoofing",
                    confidence=85,
                    evidence={'brand_spoofed': brand, 'actual_domain': target}
                ))
        
        return findings
