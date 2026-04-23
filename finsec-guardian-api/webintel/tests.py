"""
WebIntel Tests
"""

from django.test import TestCase
from django.contrib.auth.models import User
from webintel.models import WebScan, WebFinding, WebThreat


class WebScanTestCase(TestCase):
    """Test WebScan model and operations."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.scan = WebScan.objects.create(
            user=self.user,
            target='https://example.com',
            target_type='url',
            title='Test Scan',
        )
    
    def test_scan_creation(self):
        """Test WebScan creation."""
        self.assertEqual(self.scan.target, 'https://example.com')
        self.assertEqual(self.scan.status, 'pending')
        self.assertEqual(self.scan.risk_score, 0)
    
    def test_finding_creation(self):
        """Test WebFinding creation."""
        finding = WebFinding.objects.create(
            scan=self.scan,
            title='Test Finding',
            description='Test description',
            severity='high',
            analyzer='Phishing Detector',
            category='test',
        )
        
        self.assertEqual(finding.scan, self.scan)
        self.assertEqual(finding.severity, 'high')
    
    def test_threat_creation(self):
        """Test WebThreat creation."""
        threat = WebThreat.objects.create(
            threat_type='phishing_campaign',
            name='Test Campaign',
            severity_level='high',
        )
        
        self.assertEqual(threat.name, 'Test Campaign')
        self.assertEqual(threat.occurrence_count, 1)
