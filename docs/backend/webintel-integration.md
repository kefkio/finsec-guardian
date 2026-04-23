# FinSec WebIntel Integration Guide

**Purpose:** Setup and integration steps for the WebIntel module

---

## Installation & Setup

### 1. Database Migrations

```bash
cd finsec-guardian-api
python manage.py makemigrations webintel
python manage.py migrate webintel
```

### 2. Verify Installation

```bash
# Check app is registered
python manage.py shell
>>> from django.apps import apps
>>> print(apps.get_app_config('webintel'))
<AppConfig: webintel>

# Check models
>>> from webintel.models import WebScan, WebFinding, WebThreat
```

### 3. Create Superuser (if needed)

```bash
python manage.py createsuperuser
```

### 4. Access Admin Interface

Navigate to `http://localhost:8000/admin/` and login to manage WebIntel data.

---

## API Usage Examples

### 1. Create a Web Intelligence Scan

```bash
curl -X POST http://localhost:8000/api/webintel/scans/ \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "https://suspicious-site.com",
    "target_type": "url",
    "title": "Suspicious Investment Platform",
    "description": "User reported claiming 100% returns",
    "run_url_analysis": true,
    "run_phishing_detection": true,
    "run_scam_detection": true,
    "run_social_engineering": true,
    "run_monetization_analysis": true
  }'
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "target": "https://suspicious-site.com",
  "target_type": "url",
  "status": "pending",
  "risk_score": 0,
  "finding_count": 0,
  "created_at": "2026-04-16T10:30:00Z"
}
```

### 2. Quick Scan (Synchronous)

```bash
curl -X POST http://localhost:8000/api/webintel/scans/quick_scan/ \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "https://example.com",
    "target_type": "url"
  }'
```

**Response:**
```json
{
  "success": true,
  "target": "https://example.com",
  "risk_score": 42,
  "findings": [
    {
      "title": "Artificial Scarcity Tactics",
      "description": "Page uses false urgency...",
      "severity": "medium",
      "category": "scarcity_tactics",
      "confidence_score": 75
    }
  ],
  "findings_count": 1,
  "execution_time": 8.5
}
```

### 3. Get Scan Details with Findings

```bash
curl -X GET http://localhost:8000/api/webintel/scans/550e8400-e29b-41d4-a716-446655440000/ \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

### 4. Get Risk Score Explanation

```bash
curl -X GET http://localhost:8000/api/webintel/scans/550e8400-e29b-41d4-a716-446655440000/risk_explanation/ \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

**Response:**
```json
{
  "score": 75,
  "level": "HIGH",
  "total_findings": 5,
  "critical_findings": 1,
  "unique_categories": 3,
  "contributing_factors": [
    "1 critical finding(s) detected",
    "Diverse threat categories (3)",
    "High-confidence findings (3)"
  ],
  "analyzer_breakdown": {
    "Phishing Detector": 2,
    "Scam Signature Matcher": 2,
    "Monetization Pipeline Analyzer": 1
  },
  "explanation": "Risk score 75/100 (HIGH): Multiple high-severity threats detected..."
}
```

### 5. List Findings

```bash
curl -X GET http://localhost:8000/api/webintel/findings/ \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

### 6. Get Threat Intelligence

```bash
curl -X GET http://localhost:8000/api/webintel/threats/ \
  -H "Authorization: Bearer <JWT_TOKEN>"

# Get recent threats
curl -X GET http://localhost:8000/api/webintel/threats/recent/ \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

### 7. Generate Report

```bash
curl -X POST http://localhost:8000/api/webintel/reports/ \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Q1 2026 Web Threat Report",
    "scan_ids": ["550e8400-e29b-41d4-a716-446655440000", "660f8400-e29b-41d4-a716-446655440111"]
  }'
```

---

## Frontend Integration

### Add WebIntel to Dashboard

In `finsec-guardian/src/pages/Dashboard.jsx`:

```jsx
import { useState, useEffect } from 'react';
import api from '../lib/api';

export function WebIntelWidget() {
  const [recentScans, setRecentScans] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRecentScans();
  }, []);

  const fetchRecentScans = async () => {
    try {
      const response = await api.get('/webintel/scans/?limit=5');
      setRecentScans(response.data.results);
    } catch (error) {
      console.error('Failed to fetch scans:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="webintel-widget">
      <h2>Web Intelligence Scans</h2>
      {loading ? (
        <p>Loading...</p>
      ) : (
        <ul>
          {recentScans.map(scan => (
            <li key={scan.id}>
              <strong>{scan.target}</strong> - Risk: {scan.risk_score}/100
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

### Create WebIntel Scanner Page

In `finsec-guardian/src/pages/WebIntelScanner.jsx`:

```jsx
export function WebIntelScanner() {
  const [target, setTarget] = useState('');
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState(null);

  const handleScan = async () => {
    setScanning(true);
    try {
      const response = await api.post('/webintel/scans/quick_scan/', {
        target: target,
        target_type: 'url'
      });
      setResult(response.data);
    } catch (error) {
      console.error('Scan failed:', error);
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="webintel-scanner">
      <input
        type="url"
        value={target}
        onChange={e => setTarget(e.target.value)}
        placeholder="Enter URL or domain..."
      />
      <button onClick={handleScan} disabled={scanning}>
        {scanning ? 'Scanning...' : 'Scan'}
      </button>
      
      {result && (
        <div className="results">
          <h3>Risk Score: {result.risk_score}/100</h3>
          <p>Findings: {result.findings_count}</p>
          {result.findings.map((finding, i) => (
            <div key={i} className={`finding severity-${finding.severity}`}>
              <strong>{finding.title}</strong>
              <p>{finding.description}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## Analyzer Configuration

### Customize Analyzer Behavior

In `webintel/services/analyzers/base.py`, adjust confidence thresholds:

```python
# Make phishing detection stricter
CONFIDENCE_MULTIPLIER = 1.2  # Increase confidence scores
```

### Add Custom Patterns

In `webintel/services/analyzers/scam.py`:

```python
# Add new VSL funnel pattern
VSL_PATTERNS.append(r'(?:revolutionary|breakthrough).*(?:system|method)')

# Add new investment scam pattern
INVESTMENT_SCAM_PATTERNS.append(r'(?:sec.*compliant|approved.*by)')
```

---

## Monitoring & Debugging

### Check Scan Status

```bash
python manage.py shell
>>> from webintel.models import WebScan
>>> scans = WebScan.objects.all().order_by('-created_at')
>>> for scan in scans[:5]:
...     print(f"{scan.target} - {scan.status} - Risk: {scan.risk_score}")
```

### View Findings for a Scan

```bash
>>> scan = WebScan.objects.first()
>>> findings = scan.findings.all()
>>> for finding in findings:
...     print(f"{finding.title} ({finding.severity}): {finding.confidence_score}%")
```

### Debug Risk Scoring

```python
from webintel.services.risk_scorer import WebRiskScorer

scorer = WebRiskScorer()
scan = WebScan.objects.first()
findings = list(scan.findings.all().values())

explanation = scorer.explain_score(findings)
print(explanation)
```

---

## Performance Optimization

### Async Task Processing (Future)

When enabling Celery:

```python
# webintel/tasks.py
from celery import shared_task

@shared_task
def execute_scan_task(scan_id):
    from .models import WebScan
    from .services.orchestrator import WebIntelOrchestrator
    
    scan = WebScan.objects.get(id=scan_id)
    orchestrator = WebIntelOrchestrator()
    # ... run scan
```

### Database Indexing

Already configured in models:

```python
class WebScan(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['target']),
        ]
```

### Caching

```python
from django.views.decorators.cache import cache_page

@cache_page(60)  # Cache recent threats for 60 seconds
def get_recent_threats(request):
    # ...
```

---

## Troubleshooting

### Issue: Migrations not applying

```bash
# Check migration status
python manage.py showmigrations webintel

# Force migrate
python manage.py migrate webintel --fake-initial
```

### Issue: AttributeError in analyzers

Ensure all analyzer imports are correct:

```bash
python manage.py shell
>>> from webintel.services.analyzers.phishing import PhishingDetector
>>> detector = PhishingDetector()
>>> print(detector.analyzer_name)
```

### Issue: Risk score always 0

Check that findings are being persisted:

```bash
>>> from webintel.models import WebFinding
>>> WebFinding.objects.count()
```

---

## Next Steps

1. **Frontend Component:** Build WebIntel dashboard panel in React
2. **Threat Intelligence Feed:** Integrate external threat data sources
3. **ML Classification:** Train ML model on known scam domains
4. **Screenshot Analysis:** Add visual similarity detection
5. **Async Processing:** Implement Celery for long-running scans
