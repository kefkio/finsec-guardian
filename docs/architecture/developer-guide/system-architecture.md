# System Architecture

**Status:** Current  
**Last Updated:** April 2026  
**Audience:** Developers, Architects, Researchers

---

## Table of Contents

1. [Overview](#overview)
2. [High-Level Component Model](#high-level-component-model)
3. [Layer Architecture](#layer-architecture)
4. [Frontend Tier](#frontend-tier)
5. [API Gateway Tier](#api-gateway-tier)
6. [Analysis Engine Tier](#analysis-engine-tier)
7. [On-Chain Intelligence Tier](#on-chain-intelligence-tier)
8. [Persistence Tier](#persistence-tier)
9. [Cross-Cutting Concerns](#cross-cutting-concerns)
10. [Deployment Topology](#deployment-topology)

---

## Overview

FinSec Guardian follows a **layered pipeline architecture** where each tier is responsible for a single concern and communicates with neighbours through well-defined interfaces. The system processes Solidity smart contracts through five distinct tiers from ingestion to report generation.

**Related documents:**
- [Data Flow](data-flow.md) — request-level walk-through of every data transformation
- [Design Decisions](design-decisions.md) — rationale for major architectural choices
- [Backend Architecture](backend/architecture.md) — deep-dive into Django service layout
- [Frontend Overview](frontend/overview.md) — React application architecture

---

## High-Level Component Model

```
┌───────────────────────────────────────────────────────────────────────┐
│                     React Frontend (Vite 5 + Tailwind)               │
│  Dashboard │ Scanner │ ScanDetail │ Threats │ Audit │ Records        │
│  ─── On-Chain Intelligence Panel (Etherscan data) ───                │
└──────────────────────────────┬────────────────────────────────────────┘
                               │ HTTPS + JWT Bearer tokens
                               ▼
┌───────────────────────────────────────────────────────────────────────┐
│                   Django REST Framework API Gateway                   │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ JWT Auth │ Input Validation │ CORS │ Rate Limiting │ Audit Log  │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│      ScanJobViewSet │ ThreatRecordViewSet │ TamperRecordViewSet      │
│      AuditEventViewSet │ RegisterView                                │
└──────────────────────────────┬────────────────────────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────┐
│  Analysis       │  │  On-Chain       │  │  Support Services    │
│  Engine Tier    │  │  Intelligence   │  │                      │
│                 │  │  Tier           │  │  - Compilation       │
│  - Slither      │  │                 │  │  - File Processing   │
│  - Mythril      │  │  - Client       │  │  - Pattern Detection │
│  - Echidna      │  │  - Fetcher      │  │  - Gas Analysis      │
│  - Heuristic    │  │  - Analyzer     │  │  - Compliance        │
│                 │  │  - Reputation   │  │  - Invariant Gen     │
└────────┬────────┘  └────────┬────────┘  └──────────┬───────────┘
         │                    │                      │
         └────────────────────┼──────────────────────┘
                              ▼
┌───────────────────────────────────────────────────────────────────────┐
│                    Orchestrator (ScanOrchestrator)                    │
│  Pipeline: Analyzers → Etherscan → Normalizer → RiskScorer → Persist│
└──────────────────────────────┬────────────────────────────────────────┘
                               ▼
┌───────────────────────────────────────────────────────────────────────┐
│                         Persistence Tier                              │
│  PostgreSQL │ ScanJob │ Finding │ ThreatRecord │ TamperRecord        │
│  AuditEvent │ ScanReport │ FindingCategory │ SuppressionBaseline    │
└───────────────────────────────────────────────────────────────────────┘
```

---

## Layer Architecture

| Layer | Responsibility | Technology | Latency Budget |
|-------|---------------|------------|----------------|
| **L0 — Input** | Source validation, compilation | `SolidityFileProcessingService`, `SolidityCompiler` | < 5 s |
| **L1 — Static Analysis** | Pattern-based vulnerability detection | Slither (subprocess, 120 s timeout) | ≤ 120 s |
| **L2 — Symbolic Execution** | Formal path exploration | Mythril (subprocess, 60 s timeout) | ≤ 60 s |
| **L3 — Fuzz Testing** | Property-based invariant violation | Echidna (Docker, 120 s timeout) | ≤ 120 s |
| **L4 — Heuristic Analysis** | Regex-based logic flaw detection | In-process Python | < 1 s |
| **L5 — On-Chain Intelligence** | Etherscan behavioral analysis | HTTP API (rate-limited) | ≤ 30 s |
| **L6 — Normalisation** | Unified finding schema | `FindingNormalizer` | < 100 ms |
| **L7 — Risk Scoring** | Weighted composite risk + reputation | `RiskScorer` | < 10 ms |
| **L8 — Persistence** | Idempotent DB writes | `ScanPersistence` via PostgreSQL | < 50 ms |

All layers degrade gracefully — if Mythril, Echidna, or Etherscan is unavailable, the pipeline continues with available engines and marks the missing layer in scan metadata.

---

## Frontend Tier

**Stack:** React 18, Vite 5, Tailwind CSS, shadcn/ui (Radix primitives), TanStack Query v5, React Router v6, Recharts, Lucide Icons.

**Key pages:**

| Route | Component | Purpose |
|-------|-----------|---------|
| `/` | `Index` (Dashboard) | KPI cards, severity charts, recent scans |
| `/scanner` | `Scanner` | Code editor, scan creation, live results |
| `/scanner/:id` | `ScanDetail` | Findings, risk grade, statistics, **On-Chain Intelligence panel** |
| `/threats` | `ThreatModel` | STRIDE threat catalogue with risk matrix |
| `/audit-log` | `AuditLog` | Searchable event timeline |
| `/records` | `TamperProofRecords` | SHA-256 hash-chain integrity records |
| `/settings` | `Settings` | UI preferences |
| `/login` | `Login` | JWT authentication |

**Data strategy:** All API calls use TanStack Query with cascading `enabled` flags for lazy-fetching. Stale times are tuned per endpoint (30 s for scan metadata, 60 s for findings/statistics).

**Details:** [Frontend Overview](frontend/overview.md) · [UI System](frontend/ui-system.md) · [Security Architecture](frontend/security-architecture.md)

---

## API Gateway Tier

**Stack:** Django 5, Django REST Framework 3.17, SimpleJWT, django-cors-headers, PostgreSQL.

**Security layers:**
1. **CORS** — whitelist-only origins (`localhost:8080`, `localhost:5173`)
2. **JWT authentication** — access + refresh token pair via SimpleJWT
3. **Input validation** — DRF serializer enforcement on all endpoints
4. **Audit logging** — every mutating operation creates an `AuditEvent`

**URL routing:**

| Prefix | App | ViewSet |
|--------|-----|---------|
| `/api/scanner/scans/` | `scanner` | `ScanJobViewSet` — CRUD, findings, statistics, risk, reports |
| `/api/scanner/register/` | `scanner` | `RegisterView` — user registration |
| `/api/threats/threats/` | `threats` | `ThreatRecordViewSet` |
| `/api/records/records/` | `records` | `TamperRecordViewSet` — append-only with chain verification |
| `/api/audit/events/` | `audit` | `AuditEventViewSet` |
| `/api/auth/login/` | SimpleJWT | `TokenObtainPairView` |
| `/api/auth/refresh/` | SimpleJWT | `TokenRefreshView` |

**Details:** [Backend Overview](backend/overview.md) · [Backend Architecture](backend/architecture.md)

---

## Analysis Engine Tier

Four heterogeneous analysis engines run in the orchestrator pipeline. Each implements the `AnalyzerResult` dataclass contract and is normalised through `FindingNormalizer`.

| Engine | Execution Model | Security Hardening | Output Format |
|--------|-----------------|-------------------|---------------|
| **Slither** | Python subprocess | Timeout (120 s), temp file cleanup | JSON detectors list |
| **Mythril** | Python subprocess | Timeout (60 s), temp file cleanup | JSON issues list |
| **Echidna** | Docker container | `--network none`, `--read-only`, `--memory 1g`, tmpfs mounts | JSON test results |
| **Heuristic** | In-process regex | No external calls | Normalised findings list |

**Details:** [Analyzers](backend/analyzers.md) · [Scan Pipeline](backend/scan-pipeline.md) · [Invariants](backend/invariants.md)

---

## On-Chain Intelligence Tier

A **separate** analytical layer (not mixed into static/symbolic analyzers) that fetches live blockchain data from the Etherscan API and derives behavioral insights.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ EtherscanClient│ → │ EtherscanFetcher│ → │ EtherscanAnalyzer│ → │ ReputationScorer│
│               │     │               │     │               │     │               │
│ API wrapper   │     │ ContractData  │     │ OnChainInsights│    │ ReputationResult│
│ Rate limiting │     │ Source + ABI  │     │ Tx stats      │     │ Score 0–100   │
│ Auth          │     │ Transactions  │     │ Patterns      │     │ Risk adjustment│
│ Error norm    │     │ Token xfers   │     │ Value flows   │     │               │
│               │     │ Event logs    │     │ Caller graph  │     │               │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

**API endpoints consumed:**
- `getsourcecode` — verified source + ABI
- `getabi` — contract ABI
- `txlist` — normal transactions
- `tokentx` — ERC-20 token transfers
- `getLogs` — event log retrieval

**Key outputs:**
- Transaction count, unique callers, failure rate
- High-value transaction table (≥ 10 ETH threshold)
- Repeated caller detection (bot/exploit patterns)
- Function call distribution (top method signatures)
- Contract age computation
- Suspicious pattern flags (high failure rate, abnormal withdrawals, etc.)
- Reputation score (0–100) with signed risk adjustment (±15 max)

**Integration:** The orchestrator runs this layer via `_run_etherscan_layer()` only when a `contract_address` (0x-prefixed, 40 hex chars) is provided. On the frontend, the `OnChainIntelligence` component renders all insights in collapsible accordion sections.

**Configuration (settings.py):**
- `ETHERSCAN_API_KEY` — required to enable the layer
- `ETHERSCAN_BASE_URL` — supports mainnet, testnets, Polygon, BSC
- `ETHERSCAN_TIMEOUT` — HTTP timeout per request (default 30 s)

**Details:** [Design Decisions](design-decisions.md) · [Data Flow](data-flow.md)

---

## Persistence Tier

**Database:** PostgreSQL (via `psycopg2-binary`)

**Core models:**

| Model | App | Purpose |
|-------|-----|---------|
| `ScanJob` | `scanner` | Scan lifecycle (pending → analyzing → complete/failed) |
| `Finding` | `scanner` | Individual vulnerability with severity, SWC ID, location |
| `FindingCategory` | `scanner` | Categorised finding types |
| `SuppressionBaseline` | `scanner` | Suppressed findings with expiry |
| `ScanReport` | `scanner` | Generated reports (JSON, PDF, HTML) |
| `SolidityVersion` | `scanner` | Supported compiler versions |
| `ThreatRecord` | `threats` | STRIDE-based threat entries with risk matrix |
| `TamperRecord` | `records` | SHA-256 hash-chained integrity records |
| `AuditEvent` | `audit` | Append-only event timeline |

**Key indexes:** `ScanJob(-created_at, status)`, `ScanJob(user, -created_at)`, `ScanJob(source_code_hash)`, `ScanJob(contract_address)`, `Finding(scan, -severity)`, `Finding(swc_id)`.

**Details:** [Data Model](backend/data-model.md) · [Backend Architecture](backend/architecture.md)

---

## Cross-Cutting Concerns

### Authentication & Authorization
- JWT (access + refresh) via SimpleJWT
- `ProtectedRoute` wrapper on all frontend routes except `/login`
- Token auto-refresh with single-retry on 401
- `tokenStorage` in `localStorage` (access + refresh keys)

### Audit Trail
- Every CREATE, UPDATE, DELETE on scan resources creates an `AuditEvent`
- `AuditEvent` captures: event_type, actor, resource, severity, message, IP, metadata
- Records are append-only; the `TamperRecord` model enforces a SHA-256 hash chain

### Error Handling
- Backend: graceful degradation per-engine (Mythril/Echidna/Etherscan failures don't abort scans)
- Frontend: TanStack Query error states with fallback UI per component
- API: DRF exception handling with structured JSON error responses

### Security Hardening
- Echidna runs in Docker with `--network none`, `--read-only`, `--memory 1g`
- Temp files cleaned up after analysis
- Etherscan API key read from environment via `python-decouple`
- CORS whitelist-only; no wildcard origins
- Source code hashed (SHA-256) on save for deduplication

**Details:** [Threat Model](threat-model.md) · [Frontend Security](frontend/security-architecture.md)

---

## Deployment Topology

```
Production:
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Vite (static)│───▶│ Django (API) │───▶│ PostgreSQL   │
│ React SPA    │    │ Gunicorn     │    │              │
│ Port 5173    │    │ Port 8000    │    │ Port 5432    │
└──────────────┘    └──────┬───────┘    └──────────────┘
                           │
                    ┌──────┴───────┐
                    │ Docker       │
                    │ (Echidna)    │
                    │ Ephemeral    │
                    └──────────────┘

External:
 - Etherscan API (mainnet/testnet)
 - Slither binary (Python venv)
 - Mythril binary (Python venv)
```

**Required environment variables:**
- `SECRET_KEY` — Django secret
- `DEBUG` — boolean
- `ALLOWED_HOSTS` — comma-separated
- `CORS_ALLOWED_ORIGINS` — comma-separated
- `ETHERSCAN_API_KEY` — Etherscan API key (optional, enables on-chain layer)
- `ETHERSCAN_BASE_URL` — override for testnets/alt chains
- `ECHIDNA_DOCKER_IMAGE` — Echidna Docker image tag
- `ECHIDNA_TIMEOUT` — fuzzing timeout in seconds
