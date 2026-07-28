# Backend — Architecture

**Status:** Current  
**Last Updated:** April 2026  
**Audience:** Developers, Architects

---

## Table of Contents

1. [Layered Design](#layered-design)
2. [Django App Layout](#django-app-layout)
3. [Service Layer Design](#service-layer-design)
4. [View Layer](#view-layer)
5. [Serializer Layer](#serializer-layer)
6. [URL Routing](#url-routing)
7. [Dependency Graph](#dependency-graph)

---

## Layered Design

The backend follows a three-layer architecture within Django:

```
┌──────────────────────────────────────────────┐
│ View Layer (views.py, views_auth.py)         │
│ - HTTP request/response handling             │
│ - Authentication enforcement                 │
│ - Input validation via serializers           │
│ - Audit logging bridge                       │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│ Service Layer (services/)                    │
│ - ScanOrchestrator (pipeline)                │
│ - FindingNormalizer (schema unification)     │
│ - RiskScorer (score computation)             │
│ - ScanPersistence (DB abstraction)           │
│ - Analyzers (slither, mythril, echidna, etc.)│
│ - Etherscan (client, fetcher, analyzer, rep.)│
│ - Invariants (generator, injector, patterns) │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│ Model Layer (models.py per app)              │
│ - ScanJob, Finding, FindingCategory          │
│ - SuppressionBaseline, ScanReport            │
│ - ThreatRecord, TamperRecord, AuditEvent     │
└──────────────────────────────────────────────┘
```

**Key principle:** Views never contain business logic. The view layer delegates to the service layer which coordinates models and external tools.

---

## Django App Layout

### scanner (core)

The largest app — handles the entire scan lifecycle.

**Models:** `ScanJob`, `Finding`, `FindingCategory`, `SuppressionBaseline`, `ScanReport`, `SolidityVersion`

**Views:**
- `ScanJobViewSet` — full CRUD + custom actions (findings, statistics, risk, suppress, acknowledge, resolve, export-report)
- `trigger_scan` — function-based view for synchronous quick-scan
- `quick_scan` — simplified one-shot scan interface
- `RegisterView` — user registration (in `views_auth.py`)

**Services:** See [Service Layer Design](#service-layer-design) below.

### threats

STRIDE threat catalogue. Simple CRUD.

**Models:** `ThreatRecord` (title, category, description, likelihood, impact, mitigation)

**Views:** `ThreatRecordViewSet` — standard `ModelViewSet`

### records

Tamper-proof hash chain.

**Models:** `TamperRecord` (content, content_hash, previous_hash, chain_valid)

**Views:** `TamperRecordViewSet` — append-only (`http_method_names = ['get', 'post', 'head', 'options']`) with custom `perform_create()` for hash computation and `verify()` action for chain integrity check.

### audit

Security event log.

**Models:** `AuditEvent` (event_type, severity, actor, resource, ip_address, message, metadata, timestamp)

**Views:** `AuditEventViewSet` — append-only (same method restriction as records)

---

## Service Layer Design

All business logic resides in `scanner/services/`. Services are stateless classes instantiated by the orchestrator.

### ScanOrchestrator

The pipeline coordinator. Key methods:

| Method | Purpose |
|--------|---------|
| `run_scan()` | Synchronous scan pipeline — returns findings dict |
| `run_scan_job(job_id)` | Full lifecycle for persisted ScanJob |
| `_run_etherscan_layer(address)` | Etherscan pipeline — returns normalised onchain_data |
| `_get_etherscan_components()` | Lazy-loads Etherscan services (or returns None) |
| `_build_insights_from_onchain_data()` | Reconstructs OnChainInsights from normalised dict |

### FindingNormalizer

Converts raw tool output to the canonical finding dict. Key methods:

| Method | Purpose |
|--------|---------|
| `normalize(result)` | Dispatch by `result.tool` to tool-specific normalisers |
| `normalize_slither(detectors)` | Slither JSON → finding dicts |
| `normalize_mythril(issues)` | Mythril JSON → finding dicts |
| `normalize_echidna(tests, ...)` | Echidna results → finding dicts |
| `normalize_onchain(insights, rep.)` | OnChainInsights + ReputationResult → onchain_data dict |
| `enrich_findings_with_onchain(...)` | Annotate findings with on-chain context |
| `tag_findings(findings, tool)` | Stamp tool metadata and tags |

### RiskScorer

Deterministic risk calculator. Single method:

| Method | Purpose |
|--------|---------|
| `compute(findings, onchain_data)` | Returns `{risk_score, verdict, breakdown, tool_contributions, ...}` |

### ScanPersistence

DB operations abstraction:

| Method | Purpose |
|--------|---------|
| `mark_analyzing(job)` | Set status='analyzing', started_at |
| `update_progress(job, pct)` | Update progress percentage |
| `persist_findings(job, findings)` | Create Finding records, update severity counts |
| `mark_complete(job, metadata, risk)` | Set status='complete', store metadata + risk |
| `mark_failed(job, error)` | Set status='failed', store error |

---

## View Layer

### ScanJobViewSet

```python
class ScanJobViewSet(viewsets.ModelViewSet):
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    queryset = ScanJob.objects.all()
    serializer_class = ScanJobSerializer
    permission_classes = [IsAuthenticated]
```

**get_queryset()** filters by `user=request.user` — users can only see their own scans.

**get_serializer_class()** returns `ScanJobListSerializer` for list actions (lighter response).

**Custom actions:**

| Action | Method | URL Path | Description |
|--------|--------|----------|-------------|
| `trigger_scan` | POST | `scans/trigger/` | Synchronous quick-scan |
| `findings` | GET | `scans/{id}/findings/` | Filterable finding list |
| `statistics` | GET | `scans/{id}/statistics/` | Severity breakdown |
| `risk` | GET | `scans/{id}/risk/` | Risk assessment |
| `suppress_finding` | POST | `scans/{id}/suppress-finding/` | Suppress finding |
| `acknowledge_finding` | POST | `scans/{id}/acknowledge-finding/` | Acknowledge finding |
| `mark_resolved` | POST | `scans/{id}/mark-resolved/` | Resolve finding |
| `export_report` | POST | `scans/{id}/export-report/` | Export JSON/PDF/HTML |

---

## Serializer Layer

### ScanJobSerializer (detail)

**Fields:** `id`, `contract_name`, `contract_address`, `source_code`, `source_type`, `uploaded_filename`, `uploaded_file_size`, `syntax_valid`, `compilation_error`, `status`, `created_at`, `completed_at`, `findings` (nested), `finding_count`, `total_findings`, `critical_count`, `high_count`, `medium_count`, `low_count`, `info_count`, `risk_score`, `risk_verdict`, `risk_assessment`, `uploaded_file` (write-only), `requested_solidity_version` (write-only)

**Validation:** `source_code XOR uploaded_file` — exactly one must be provided.

### ScanJobListSerializer (list)

Lighter serializer without nested findings or source_code. Fields: `id`, `contract_name`, `contract_address`, `source_type`, `uploaded_filename`, `status`, `syntax_valid`, `created_at`, `completed_at`, `finding_count`, `total_findings`, `risk_score`, `risk_verdict`

### FindingSerializer

Fields: `id`, `swc_id`, `title`, `severity`, `description`, `recommendation`, `line_number`

---

## URL Routing

### Root (config/urls.py)

```
/admin/                → Django admin
/api/scanner/          → scanner.urls
/api/threats/          → threats.urls
/api/audit/            → audit.urls
/api/records/          → records.urls
/api/auth/login/       → TokenObtainPairView
/api/auth/refresh/     → TokenRefreshView
```

### Scanner (scanner/urls.py)

Uses DRF DefaultRouter:
```
/api/scanner/scans/             → ScanJobViewSet (list, create)
/api/scanner/scans/{pk}/        → ScanJobViewSet (retrieve, update, destroy)
/api/scanner/scans/{pk}/..../   → Custom actions
/api/scanner/register/          → RegisterView
```

---

## Dependency Graph

```
views.py ──→ serializers.py ──→ models.py
    │
    └──→ services/
            ├── orchestrator.py
            │   ├── analyzers/slither.py
            │   ├── analyzers/mythril.py
            │   ├── analyzers/echidna.py
            │   ├── analyzers/heuristic.py
            │   ├── etherscan/client.py
            │   │   └── fetcher.py → analyzer.py → reputation.py
            │   ├── normalizer.py
            │   ├── risk_scorer.py
            │   └── persistence.py ──→ models.py
            │
            ├── file_processing.py
            ├── compilation_service.py
            └── invariants/
```

**Key insight:** The orchestrator is the only service that imports other services. Views only import the orchestrator (and file processing). This keeps the dependency chain clean and testable.
