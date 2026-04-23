# FinSec Guardian — Technical Documentation

**Status:** Current  
**Last Updated:** April 2026  
**Platform:** Multi-Engine Smart Contract Security Analysis

---

## About

FinSec Guardian is a **composable multi-engine security analysis platform** for auditing Solidity smart contracts pre-deployment. It integrates five heterogeneous analysis methodologies into a unified pipeline with normalised findings, deterministic risk scoring, automated invariant generation, on-chain intelligence, and tamper-evident audit logging.

**Key capabilities:**
- **Multi-engine analysis** — Slither (static), Mythril (symbolic), Echidna (fuzz), Heuristic (regex), Etherscan (on-chain)
- **Normalised findings** — Unified schema across all engines with SWC IDs, severity, confidence, and remediation
- **Deterministic risk scoring** — Weighted exponential saturation model with on-chain reputation adjustment
- **Automated invariant generation** — Regex-based property synthesis for Echidna fuzzing
- **Address-only scanning** — On-chain intelligence from contract address alone (no source code required)
- **Tamper-evident audit trail** — SHA-256 hash-chain integrity records with STRIDE threat model
- **Secure-by-design** — JWT authentication, CORS whitelist, input validation, OWASP Top 10 alignment

---

## Documentation Map

### System-Level

| Document | Description |
|----------|-------------|
| [System Architecture](system-architecture.md) | High-level component model, layer architecture, deployment topology |
| [Data Flow](data-flow.md) | Request-level walk-through of every data transformation |
| [Design Decisions](design-decisions.md) | Rationale for major architectural choices |
| [Threat Model](threat-model.md) | STRIDE-based threat analysis, attack surfaces, mitigations |

### Backend

| Document | Description |
|----------|-------------|
| [Overview](backend/overview.md) | Django application structure, service layer organisation |
| [Architecture](backend/architecture.md) | Deep-dive into service classes, models, and ViewSets |
| [Data Model](backend/data-model.md) | ORM schema: ScanJob, Finding, ThreatRecord, AuditEvent, etc. |
| [Analyzers](backend/analyzers.md) | Individual engine details: Slither, Mythril, Echidna, Heuristic, Etherscan |
| [Orchestrator](backend/orchestrator.md) | `ScanOrchestrator` pipeline coordination, Etherscan layer, graceful degradation |
| [Scan Pipeline](backend/scan-pipeline.md) | End-to-end lifecycle: source-code and address-only scan flows |
| [Risk Scoring](backend/risk-scoring.md) | Weighted composite scoring formula, on-chain adjustment, verdict classification |
| [Invariants](backend/invariants.md) | Automated invariant generation and injection for Echidna fuzzing |

### Frontend

| Document | Description |
|----------|-------------|
| [Overview](frontend/overview.md) | React application architecture, features, project structure, development workflow |
| [UI System](frontend/ui-system.md) | Component library, data fetching, styling system, patterns |
| [Security Architecture](frontend/security-architecture.md) | JWT management, route protection, CSP, input validation, OWASP alignment |

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, Vite 5, Tailwind CSS, shadcn/ui (Radix), TanStack Query v5, React Router v6, Recharts, Lucide |
| **API** | Django 5, Django REST Framework 3.17, SimpleJWT, django-cors-headers |
| **Database** | PostgreSQL (psycopg2-binary) |
| **Analysis** | Slither (Python subprocess), Mythril (Python subprocess), Echidna (Docker), Heuristic (in-process) |
| **On-Chain** | Etherscan API (rate-limited HTTP client) |
| **Testing** | Vitest, React Testing Library, Playwright, Django TestCase |

---

## Architecture Overview

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
│  JWT Auth │ Input Validation │ CORS │ Rate Limiting │ Audit Log      │
└──────────────────────────────┬────────────────────────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────┐
│  Analysis       │  │  On-Chain       │  │  Support Services    │
│  Engine Tier    │  │  Intelligence   │  │  Compilation         │
│  Slither        │  │  Client         │  │  File Processing     │
│  Mythril        │  │  Fetcher        │  │  Pattern Detection   │
│  Echidna        │  │  Analyzer       │  │  Invariant Gen       │
│  Heuristic      │  │  Reputation     │  │                      │
└────────┬────────┘  └────────┬────────┘  └──────────┬───────────┘
         └────────────────────┼──────────────────────┘
                              ▼
┌───────────────────────────────────────────────────────────────────────┐
│  Orchestrator → Normalizer → RiskScorer → Persistence                │
└──────────────────────────────┬────────────────────────────────────────┘
                               ▼
┌───────────────────────────────────────────────────────────────────────┐
│  PostgreSQL: ScanJob │ Finding │ ThreatRecord │ AuditEvent           │
└───────────────────────────────────────────────────────────────────────┘
```

---

## Analysis Pipeline

The orchestrator runs engines sequentially with graceful degradation:

| Layer | Engine | Timeout | Required? |
|-------|--------|---------|-----------|
| L1 | Slither (static analysis) | 120 s | Yes — failure aborts |
| L2 | Mythril (symbolic execution) | 60 s | No — skip on error |
| L3 | Echidna (property fuzzing) | 120 s | No — skip on error |
| L4 | Heuristic (regex rules) | < 1 s | Yes — always runs |
| L5 | Etherscan (on-chain intelligence) | 30 s | No — only when address provided |
| L6 | Normalisation | < 100 ms | Yes |
| L7 | Risk scoring | < 10 ms | Yes |
| L8 | Persistence | < 50 ms | Yes (job-based only) |

---

## Risk Scoring Model

Per-finding weighted scores with exponential saturation:

$$S_i = W_{\text{severity}} \times W_{\text{tool}} \times \frac{\text{confidence}}{100}$$

$$\text{Risk} = 100 \times \left(1 - e^{-0.08 \times S_{\text{total}}}\right)$$

- **Critical floor:** Any critical finding → minimum score 80
- **On-chain adjustment:** Etherscan reputation ±15 max
- **Verdicts:** CRITICAL RISK (≥85) → HIGH (≥70) → MEDIUM (≥50) → LOW (≥25) → MINIMAL (<25)

See [Risk Scoring](backend/risk-scoring.md) for the complete algorithm.

---

## Scan Modes

| Mode | Input | Engines | Persistence |
|------|-------|---------|-------------|
| **Source-code scan** | Solidity source (+ optional address) | All 5 engines | ScanJob created |
| **Address-only scan** | Contract address only | Etherscan only | ScanJob created |
| **Trigger scan** | Source or address | All applicable | No persistence |

See [Scan Pipeline](backend/scan-pipeline.md) for flow diagrams.

---

## Research Contributions

1. **Multi-engine integration** — First system normalising findings across Slither, Mythril, Echidna, and custom heuristics
2. **Deterministic risk scoring** — Explainable weighted model combining severity, tool reliability, confidence, and on-chain reputation
3. **Automated invariant generation** — Regex-based property synthesis for differential fuzzing with Echidna
4. **On-chain intelligence layer** — Live Etherscan data enriches static findings with behavioral context
5. **Secure-by-design** — STRIDE threat model, OWASP Top 10 compliance, tamper-evident hash chains

---

## Quick Start

### Backend

```bash
cd finsec-guardian-api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd finsec-guardian
npm install
npm run dev
```

### Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `SECRET_KEY` | Yes | Django secret key |
| `DEBUG` | No | Debug mode (default: False) |
| `ALLOWED_HOSTS` | Yes | Comma-separated hostnames |
| `CORS_ALLOWED_ORIGINS` | Yes | Comma-separated origins |
| `ETHERSCAN_API_KEY` | No | Enables on-chain intelligence layer |
| `ETHERSCAN_BASE_URL` | No | Override for testnets/alt chains |
| `ECHIDNA_DOCKER_IMAGE` | No | Echidna Docker image tag |
| `VITE_API_URL` | No | Frontend → backend API URL |

---

**Document Version:** 2.0  
**Last Updated:** April 2026
