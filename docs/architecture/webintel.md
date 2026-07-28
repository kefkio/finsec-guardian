# FinSec WebIntel Module - Architecture

**Status:** Initial Implementation  
**Date:** April 2026  
**Module:** FinSec Web Intelligence  

---

## Overview

FinSec WebIntel is an independent intelligence module within the broader FinSec platform designed to detect, analyze, and score financial deception risks in web-based systems. It complements the scanner module (which analyzes smart contracts) by providing threat intelligence on malicious web infrastructure.

**Key Capabilities:**
- Detect scam websites (VSL funnels, fake investment platforms)
- Identify phishing pages and credential harvesters
- Analyze social engineering patterns in financial contexts
- Score fraudulent monetization pipelines
- Generate threat intelligence for downstream integration

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                    React Frontend (WebIntel Panel)                   │
│              URL Analysis │ Threat Intelligence │ Reports            │
└─────────────────────────────────────────────────────────────────────┘
                              │ HTTPS + JWT
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                   Django REST Framework API                           │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ JWT Auth │ Input Validation │ CORS │ Rate Limiting           │ │
│  └────────────────────────────────────────────────────────────────┘ │
│      WebScanViewSet │ WebFindingViewSet │ WebThreatViewSet      │
│      WebReportViewSet │ QuickScan endpoint                       │
└─────────────────────────────┬──────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
          ┌──────────────────┐  ┌──────────────────┐
          │  Orchestrator    │  │  Persistence     │
          │  Pipeline        │  │  & Reporting     │
          └──────────────────┘  └──────────────────┘
                    │
      ┌─────────────┼─────────────┬─────────────┬──────────────┐
      ▼             ▼             ▼             ▼              ▼
 ┌────────┐  ┌─────────┐  ┌─────────┐  ┌────────┐  ┌────────────┐
 │  URL   │  │Phishing │  │  Scam   │  │SocEng  │  │Monetization│
 │Analyzer│  │Detector │  │Detector │  │Analyzer│  │ Analyzer   │
 └────────┘  └─────────┘  └─────────┘  └────────┘  └────────────┘
      │             │             │             │              │
      └─────────────┴─────────────┴─────────────┴──────────────┘
                              │
                    ┌─────────┴──────────┐
                    ▼                    ▼
            ┌──────────────┐      ┌─────────────┐
            │ Normalizer   │      │Risk Scorer  │
            │ & Dedup      │      │(0-100)      │
            └──────────────┘      └─────────────┘
                    │                    │
                    └─────────┬──────────┘
                              ▼
            ┌─────────────────────────────────────┐
            │  Persistence Tier (PostgreSQL)      │
            │  WebScan │ WebFinding │ WebThreat  │
            │  Report │ SuppressionBaseline      │
            └─────────────────────────────────────┘
```

---

## Layer Architecture

| Layer | Component | Responsibility | Timeout |
|-------|-----------|----------------|---------|
| **L0 — Input** | API Gateway | URL/domain validation | < 1 s |
| **L1 — URL/Domain Analysis** | URLDomainAnalyzer | Domain age, SSL, DNS, typosquatting | ≤ 10 s |
| **L2 — Phishing Detection** | PhishingDetector | Credential forms, brand spoofing, redirects | ≤ 15 s |
| **L3 — Scam Detection** | ScamDetector | VSL funnels, fake investments, MLM | ≤ 15 s |
| **L4 — Social Engineering** | SocialEngineeringAnalyzer | Psychological manipulation, fear appeals | ≤ 5 s |
| **L5 — Monetization** | MonetizationAnalyzer | Payment processors, crypto, money laundering | ≤ 5 s |
| **L6 — Normalization** | FindingNormalizer | Unified finding schema, deduplication | < 100 ms |
| **L7 — Risk Scoring** | WebRiskScorer | Exponential saturation composite score | < 10 ms |
| **L8 — Persistence** | WebIntelPersistence | Idempotent DB writes | < 50 ms |

---

## Data Models

### WebScan
```python
id: UUID (primary key)
user: ForeignKey(User)
target: CharField (URL/domain/IP)
target_type: CharField (url|domain|ip)
status: CharField (pending|running|completed|failed)
created_at, started_at, completed_at: DateTime
risk_score: Int (0-100)
finding_count: Int
threat_count: Int
run_url_analysis, run_phishing_detection, etc.: Boolean
```

### WebFinding
```python
id: UUID
scan: ForeignKey(WebScan)
title, description: String
severity: CharField (critical|high|medium|low|info)
analyzer: CharField (url|phishing|scam|soceng|monetization)
category: CharField
confidence_score: Int (0-100)
fingerprint: String (deduplication key)
evidence: JSON
```

### WebThreat
```python
id: UUID
threat_type: CharField (phishing_campaign|investment_scam|vsl_funnel|...)
name: CharField
severity_level: CharField
first_seen, last_seen: DateTime
occurrence_count: Int
indicators_of_compromise: JSON
known_attributes: JSON
financial_impact: CharField
targeted_vertical: CharField
geographic_focus: CharField
findings: M2M(WebFinding)
```

### WebSuppressionBaseline
```python
id: UUID
user: OneToOne(User)
whitelisted_domains: JSON List
whitelisted_patterns: JSON List (regex)
ignored_threat_types: JSON List
created_at, updated_at: DateTime
```

---

## Analysis Engines

### 1. URL/Domain Analyzer
**Purpose:** Detect malicious domains and suspicious infrastructure.

**Checks:**
- Domain age (new domains = higher risk)
- SSL certificate validity and issuer
- DNS resolution
- Typosquatting patterns
- Suspicious TLDs (free registrars)

**Output:** 0-N findings with confidence scores

### 2. Phishing Detector
**Purpose:** Identify credential harvesting and fake login pages.

**Checks:**
- Credential harvesting forms (username/password fields)
- Form action domain mismatch
- Brand spoofing (PayPal, Apple, Microsoft, etc.)
- Urgent action language
- Redirect/JavaScript navigation attempts

**Output:** 0-N phishing-related findings

### 3. Scam Detector
**Purpose:** Identify known scam patterns and fraudulent platforms.

**Checks:**
- VSL (Video Sales Letter) funnel indicators
- Guaranteed return claims
- Unrealistic return percentages
- Get-rich-quick language
- MLM/pyramid scheme patterns
- Artificial scarcity tactics

**Output:** 0-N scam detection findings

### 4. Social Engineering Analyzer
**Purpose:** Detect psychological manipulation tactics.

**Checks:**
- Authority exploitation (government, celebrity impersonation)
- Fear appeals (account closure, legal action)
- False social proof (fake reviews, statistics)
- Reciprocity manipulation (free offers before ask)
- Foot-in-door commitment tactics
- FOMO (Fear of Missing Out) language

**Output:** 0-N social engineering findings

### 5. Monetization Pipeline Analyzer
**Purpose:** Detect fraudulent money flows and payment infrastructure.

**Checks:**
- High-risk payment processors (Payoneer, 2Checkout)
- Cryptocurrency payment infrastructure
- Ad fraud networks and excessive tracking
- Money laundering indicators
- Non-existent or non-refundable policies
- Suspicious affiliate networks

**Output:** 0-N monetization fraud findings

---

## Risk Scoring Model

**Formula:** $R = 100 \times (1 - e^{-kS})$ where $k = 0.08$, $S$ = weighted severity sum

**Components:**

1. **Base Score (Exponential Saturation)**
   - Sums weighted severity contributions: Critical=3.0, High=1.5, Medium=0.8, Low=0.3, Info=0.1
   - Applies exponential saturation to prevent unbounded scores
   - Adjusts by analyzer reliability (0.5-1.0)
   - Adjusts by finding confidence (0-1.0)

2. **Critical Floor**
   - Any critical finding forces minimum score of 80

3. **Diversity Bonus**
   - Unique finding categories add +0.5 each (max +5.0)
   - Penalizes broad vulnerability surfaces

4. **Confidence Weighting**
   - Multiplies final score by average finding confidence factor (0.5-1.0)

**Result:** 0-100 score with levels:
- **CRITICAL** (80-100): Immediate action required
- **HIGH** (60-79): Multiple high-severity threats
- **MEDIUM** (40-59): Moderate risk identified
- **LOW** (20-39): Low risk but warrants monitoring
- **INFO** (0-19): Informational findings

---

## API Endpoints

### Scans
- `POST /api/webintel/scans/` - Create and start scan
- `GET /api/webintel/scans/` - List user's scans
- `GET /api/webintel/scans/{id}/` - Get scan details with findings
- `POST /api/webintel/scans/quick_scan/` - Synchronous analysis
- `GET /api/webintel/scans/{id}/risk_explanation/` - Detailed risk breakdown

### Findings
- `GET /api/webintel/findings/` - List findings across scans
- `GET /api/webintel/findings/{id}/` - Get finding details

### Threats
- `GET /api/webintel/threats/` - List threat intelligence
- `GET /api/webintel/threats/{id}/` - Get threat details
- `GET /api/webintel/threats/recent/` - Recently active threats

### Reports
- `POST /api/webintel/reports/` - Generate aggregated report
- `GET /api/webintel/reports/` - List user's reports
- `GET /api/webintel/reports/{id}/` - Get report content

---

## Integration with FinSec Platform

WebIntel integrates with the broader FinSec platform through:

1. **Shared Threat Catalogue** (threats app)
   - WebThreat records link to the global threat catalogue
   - Enables cross-module threat correlation

2. **Unified Audit Trail** (audit app)
   - All WebIntel scans logged to audit events
   - User actions tracked for compliance

3. **Records & Compliance** (records app)
   - WebIntel findings can be attached to compliance records
   - Risk scores contribute to organizational risk profile

4. **Frontend Integration**
   - OnChainIntelligence panel (scanner module) parallels WebIntelligence panel
   - Unified dashboard showing both on-chain and web-based risks

---

## Graceful Degradation

If any analyzer fails or is unavailable:
- Pipeline continues with available analyzers
- Scan completes with available findings
- Unavailable analyzers marked in metadata
- Risk score calculated from available data

Example: If HTML content fetch fails, DOM-based analyzers (Phishing, Scam) marked unavailable but URL/Domain analyzer still runs.

---

## Security Considerations

1. **Content Fetching**
   - Timeout protection (15s max)
   - Size limits on HTML content (max 10MB)
   - DNS rebinding protection

2. **Rate Limiting**
   - API endpoints rate-limited to prevent abuse
   - Analyzer internal timeouts prevent hanging

3. **Data Privacy**
   - Sensitive evidence sanitized before logging
   - User scans isolated by authentication

4. **Suppression Baseline**
   - Users can whitelist false positives
   - Per-user configuration prevents over-blocking

---

## Future Enhancements

1. **ML-Based Detection**
   - Train classifier on known scam domains
   - Behavioral pattern recognition
   - Anomaly detection

2. **Screenshot Analysis**
   - Visual similarity to legitimate sites
   - Layout analysis for phishing indicators

3. **Threat Feed Integration**
   - Ingest external threat intelligence
   - Real-time indicator matching

4. **Async Processing**
   - Celery task queue for long-running scans
   - WebSocket updates to frontend

5. **Geographic Analysis**
   - Hosting location analysis
   - Geo-blocking patterns
   - International money transfer flows
