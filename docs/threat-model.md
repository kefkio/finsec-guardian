# Threat Model

**Status:** Current  
**Last Updated:** April 2026  
**Audience:** Security Engineers, Auditors, Architects

---

## Table of Contents

1. [Overview](#overview)
2. [STRIDE Analysis](#stride-analysis)
3. [Attack Surface Map](#attack-surface-map)
4. [Trust Boundaries](#trust-boundaries)
5. [Threat Catalogue](#threat-catalogue)
6. [Mitigations](#mitigations)
7. [Residual Risks](#residual-risks)

---

## Overview

This threat model applies the Microsoft **STRIDE** framework to FinSec Guardian's attack surface. The system processes untrusted Solidity source code and communicates with external services (Etherscan API), creating a non-trivial threat landscape for a security analysis tool.

**Scope:** API backend, frontend SPA, analysis engines, Etherscan integration, persistence layer.

**Out of scope:** Host OS and network infrastructure, third-party Solidity compiler (solc) internals.

**Related documents:**
- [System Architecture](system-architecture.md) — component model
- [Frontend Security](frontend/security-architecture.md) — client-side controls
- [Design Decisions](design-decisions.md) — rationale for security choices

---

## STRIDE Analysis

### S — Spoofing Identity

| Threat | Description | Likelihood | Impact | Risk |
|--------|-------------|-----------|--------|------|
| **T-S1** Token theft | Attacker steals JWT from localStorage via XSS | 3 | 5 | 15 |
| **T-S2** Credential stuffing | Automated login attempts with leaked credentials | 3 | 4 | 12 |
| **T-S3** API key exposure | ETHERSCAN_API_KEY leaked in client-side code or logs | 2 | 3 | 6 |

**Mitigations:**
- T-S1: CSP headers, input sanitisation, HTTPOnly not applicable (SPA), Content-Type enforcement
- T-S2: Rate limiting on `/api/auth/login/`, strong password policy
- T-S3: API key only in Django settings (server-side), never exposed to frontend; read via `python-decouple`

### T — Tampering with Data

| Threat | Description | Likelihood | Impact | Risk |
|--------|-------------|-----------|--------|------|
| **T-T1** Finding manipulation | Attacker modifies scan results in transit | 2 | 5 | 10 |
| **T-T2** Audit log deletion | Administrator deletes audit events to cover tracks | 2 | 5 | 10 |
| **T-T3** Hash chain break | Attacker modifies TamperRecord content without updating chain | 2 | 4 | 8 |

**Mitigations:**
- T-T1: HTTPS (TLS) for API transport; CORS whitelist prevents cross-origin requests
- T-T2: `AuditEventViewSet` is append-only (`http_method_names = ['get', 'post', 'head', 'options']`)
- T-T3: Hash chain verification (`verify()` action walks entire chain; any break is detectable)

### R — Repudiation

| Threat | Description | Likelihood | Impact | Risk |
|--------|-------------|-----------|--------|------|
| **T-R1** Scan denial | User denies having submitted a scan | 2 | 3 | 6 |
| **T-R2** Action denial | User denies suppressing/acknowledging a finding | 2 | 3 | 6 |

**Mitigations:**
- T-R1, T-R2: All mutations create `AuditEvent` records with actor, IP, timestamp, and action metadata. The hash-chain `TamperRecord` provides cryptographic non-repudiation.

### I — Information Disclosure

| Threat | Description | Likelihood | Impact | Risk |
|--------|-------------|-----------|--------|------|
| **T-I1** Source code exposure | Another user's scanned contract source leaked | 3 | 5 | 15 |
| **T-I2** Finding exposure | Vulnerability details visible to unauthorized users | 3 | 5 | 15 |
| **T-I3** Etherscan data leakage | On-chain transaction data cached improperly | 1 | 2 | 2 |

**Mitigations:**
- T-I1, T-I2: `get_queryset()` filters scans by `user=request.user`; no cross-user data access. JWT-required on all data endpoints.
- T-I3: Etherscan data is public blockchain data; not stored in DB (only in scan metadata JSON). No sensitive information beyond what's publicly visible on Etherscan.

### D — Denial of Service

| Threat | Description | Likelihood | Impact | Risk |
|--------|-------------|-----------|--------|------|
| **T-D1** Analysis resource exhaustion | Malicious contract causes analyzer to consume excessive CPU/memory | 3 | 4 | 12 |
| **T-D2** Etherscan rate limit exhaustion | Attacker triggers many scans with contract addresses to exhaust API quota | 2 | 3 | 6 |
| **T-D3** Large source upload | Oversized Solidity file overwhelms compilation | 2 | 3 | 6 |

**Mitigations:**
- T-D1: Slither timeout (120 s), Mythril timeout (60 s), Echidna Docker with `--memory 1g` and timeout (120 s)
- T-D2: Etherscan client rate-limits at 0.22 s per request; API key has Etherscan's own rate limits
- T-D3: DRF serializer validation; file processing service validates size and format

### E — Elevation of Privilege

| Threat | Description | Likelihood | Impact | Risk |
|--------|-------------|-----------|--------|------|
| **T-E1** Container escape | Malicious Solidity triggers Echidna Docker container escape | 1 | 5 | 5 |
| **T-E2** Command injection | Crafted contract name injected into subprocess command | 2 | 5 | 10 |
| **T-E3** Django admin access | Unauthorized access to `/admin/` | 2 | 5 | 10 |

**Mitigations:**
- T-E1: Docker `--network none`, `--read-only`, `--tmpfs` with `noexec`, memory limits
- T-E2: Contract source written to temp files; no shell=True in subprocess calls; input sanitised
- T-E3: Admin URL, strong admin password, Django middleware stack

---

## Attack Surface Map

```
┌─────────────────────────────────────────────────────┐
│                  EXTERNAL                            │
│                                                     │
│  Browser ──HTTPS──→ React SPA                       │
│                       │                             │
│  Etherscan API ◀──HTTP──┐                           │
│                         │                           │
└────────────────────────┼────────────────────────────┘
                         │
┌────────────────────────┼────────────────────────────┐
│              TRUST BOUNDARY: API Gateway              │
│                         │                            │
│  Django REST Framework  │                            │
│  ├─ JWT Validation      │                            │
│  ├─ CORS Enforcement    │                            │
│  ├─ Input Validation    │                            │
│  └─ Audit Logging       │                            │
│                         │                            │
└────────────────────────┼────────────────────────────┘
                         │
┌────────────────────────┼────────────────────────────┐
│        TRUST BOUNDARY: Analysis Engine                │
│                         │                            │
│  Orchestrator           │                            │
│  ├─ Slither (subprocess)│                            │
│  ├─ Mythril (subprocess)│                            │
│  ├─ Echidna (Docker)    │                            │
│  ├─ Heuristic (in-proc) │                            │
│  └─ Etherscan (HTTP)    │                            │
│                         │                            │
└────────────────────────┼────────────────────────────┘
                         │
┌────────────────────────┼────────────────────────────┐
│        TRUST BOUNDARY: Data Store                     │
│  PostgreSQL             │                            │
│  ├─ ScanJob, Finding    │                            │
│  ├─ ThreatRecord        │                            │
│  ├─ TamperRecord        │                            │
│  └─ AuditEvent          │                            │
└─────────────────────────────────────────────────────┘
```

---

## Trust Boundaries

| Boundary | Components | Controls |
|----------|-----------|----------|
| **Frontend ↔ API** | React SPA ↔ Django REST | JWT auth, CORS, HTTPS, input validation |
| **API ↔ Analyzers** | Django ↔ Slither/Mythril/Echidna | Subprocess isolation, timeouts, temp file cleanup |
| **API ↔ Etherscan** | Django ↔ Etherscan REST | API key auth, rate limiting, timeout, error handling |
| **API ↔ Database** | Django ORM ↔ PostgreSQL | Parameterised queries (ORM), connection pooling |

---

## Threat Catalogue

The `threats` Django app maintains a STRIDE-based threat catalogue in the database. Each `ThreatRecord` has:

| Field | Type | Description |
|-------|------|-------------|
| `title` | CharField(255) | Threat name |
| `category` | Enum | spoofing, tampering, repudiation, info_disclosure, dos, elevation |
| `description` | TextField | Detailed threat narrative |
| `likelihood` | 1–5 | Probability of exploitation |
| `impact` | 1–5 | Damage on successful exploitation |
| `mitigation` | TextField | Recommended controls |
| `risk_score` | Computed | `likelihood × impact` (1–25) |

---

## Mitigations

### Authentication & Access Control
- JWT access + refresh tokens (SimpleJWT)
- Per-user query scoping (`get_queryset()` filters by `user`)
- Append-only audit log and tamper records

### Input Validation
- DRF serializers validate all API input
- `source_code XOR uploaded_file` enforcement
- Contract address regex validation (`^0x[0-9a-fA-F]{40}$`)
- File size and type validation in `SolidityFileProcessingService`

### Process Isolation
- Echidna: Docker `--network none`, `--read-only`, `--memory 1g`, `--tmpfs noexec`
- Slither/Mythril: subprocess with timeout, no `shell=True`
- Temp files cleaned up after each analysis

### Transport Security
- HTTPS between frontend and API
- CORS whitelist (no wildcard origins)
- API key for Etherscan stored server-side only

### Audit & Non-Repudiation
- `AuditEvent` created on every mutation
- `TamperRecord` SHA-256 hash chain
- Append-only constraints on audit and record endpoints

---

## Residual Risks

| Risk | Severity | Mitigation Status | Notes |
|------|----------|-------------------|-------|
| XSS leading to JWT theft | Medium | Partial — no HTTPOnly (SPA requirement) | CSP + sanitisation reduce likelihood |
| Unrestricted scan rate | Low | Partial — no per-user rate limiting yet | DRF throttle planned |
| Token revocation | Low | Not implemented | Deny-list or short-lived tokens planned |
| solc compiler vulnerabilities | Low | Accepted | Using official compiler; not in scope |
| Etherscan API downtime | Low | Mitigated — graceful degradation | Scans complete without on-chain layer |
