# FinSec Guardian

FinSec Guardian is a **secure-by-design** Solidity smart contract security platform. It practises the security disciplines it audits: every layer of the stack — frontend, API, transport, and crawl surface — is hardened against the threat vectors described in the OWASP Top 10 and OWASP Smart Contract Top 10.

The platform combines four analysis engines — static analysis via [Slither](https://github.com/crytic/slither) (Trail of Bits), symbolic execution via [Mythril](https://github.com/Consensys/mythril) (ConsenSys), property-based fuzzing via [Echidna](https://github.com/crytic/echidna) (Crytic), and a custom regex-based heuristic analyzer — normalises findings into a unified schema, computes aggregate risk scores, and delivers tamper-proof audit reports with risk grades (A–F). All without requiring contract deployment.

| Repo | Purpose |
| --- | --- |
| `finsec-guardian` (this repo) | React frontend — landing page, scanner UI, dashboard, threat model, audit log, records |
| `finsec-guardian-api` | Django REST Framework backend — four-engine scanner pipeline, risk scoring, scan persistence, STRIDE threats, audit events, tamper-proof records |

---

## Application Security Architecture

> FinSec Guardian is itself a hardened web application. This section documents the security controls built into every layer of the platform.

### 1. Authentication & Session Management  *(OWASP A07)*

| Control | Implementation |
| --- | --- |
| Authentication scheme | JWT (access + refresh tokens) via `djangorestframework-simplejwt` |
| Token storage | `localStorage` with explicit `clear()` on logout; no cookies |
| Silent token refresh | Expired access tokens are refreshed transparently via `/api/auth/refresh/`; on failure the session is cleared and the user is redirected to `/login` |
| Protected routes | All authenticated routes are wrapped in a `ProtectedRoute` component; unauthenticated requests receive HTTP 401 |
| Password policy | Django's `AUTH_PASSWORD_VALIDATORS` enforces minimum length, blocks common passwords, and rejects passwords too similar to the username |
| Registration input | `RegisterSerializer` validates and sanitises all user-supplied fields before the ORM handles them |

### 2. API Authorisation  *(OWASP A01)*

- Every API endpoint requires `IsAuthenticated` (`permission_classes = [IsAuthenticated]`) — anonymous access returns HTTP 401
- JWT authentication is the sole `DEFAULT_AUTHENTICATION_CLASS`; session/cookie auth is not enabled on the API
- The Django admin interface is available only at a non-guessable path and is not exposed in the public API router

### 3. Injection & Input Validation  *(OWASP A03)*

- All database queries are issued through Django's ORM — raw SQL is not used anywhere
- DRF serialisers validate and whitelist all incoming fields before any model interaction
- Solidity source code submitted for scanning is passed directly to Slither as file input — it is never executed, interpreted, or rendered as HTML
- Honeypot hidden fields on the login and registration forms silently reject automated bot submissions that fill invisible inputs

### 4. Cross-Origin Resource Sharing  *(OWASP A05)*

- `django-cors-headers` is installed as the first response middleware
- `CORS_ALLOWED_ORIGINS` is set via environment variable — no wildcard (`*`) origins are permitted
- In production, only the exact frontend origin is whitelisted

### 5. Security HTTP Headers  *(OWASP A05)*

**Backend (Django middleware stack):**

| Header | Middleware |
| --- | --- |
| `X-Frame-Options: DENY` | `XFrameOptionsMiddleware` |
| `X-Content-Type-Options: nosniff` | `SecurityMiddleware` |
| HTTPS redirect (production) | `SecurityMiddleware` (`SECURE_SSL_REDIRECT`) |
| HSTS (production) | `SecurityMiddleware` (`SECURE_HSTS_SECONDS`) |
| CSRF protection | `CsrfViewMiddleware` |

**Frontend (`index.html` meta tags):**

| Header / Meta | Value |
| --- | --- |
| `Content-Security-Policy` | `default-src 'self'`; scripts, styles, images, and connections locked to same-origin + explicit API origins; `object-src 'none'`; `base-uri 'self'` |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |

### 6. Bot & Automated Threat Mitigation  *(OWASP A09)*

- **`robots.txt`** explicitly blocks known malicious scrapers and data-harvesting bots (AhrefsBot, SemrushBot, MJ12bot, DotBot, BLEXBot, Bytespider, GPTBot, CCBot, `python-requests`, Scrapy, and others) while still allowing search engine crawler access to public pages
- `/api/` and `/admin/` paths are `Disallow`-ed for all crawlers, preventing automated discovery of API endpoints
- **Honeypot fields** on authentication forms (hidden via CSS, never populated by real users) silently reject requests from bots that blindly fill all form fields — no error is shown; the submission is discarded server-side
- Rate throttling (DRF `AnonRateThrottle` / `UserRateThrottle`) is applied to all endpoints, with tighter limits on the authentication and registration routes to resist credential-stuffing attacks

### 7. Sensitive Data Exposure  *(OWASP A02)*

- `SECRET_KEY` and all credentials are loaded from environment variables via `python-decouple` — no secrets appear in source code
- The `DEBUG` flag is environment-controlled; in production it is `False`, suppressing stack traces in HTTP responses
- `ALLOWED_HOSTS` is explicitly set via environment variable, preventing HTTP Host header injection
- Scan job source code is stored in the database only for the authenticated user's own records and is never returned in list endpoints — only in the detail view of the owning user

### 8. Tamper-Evident Audit Trail  *(OWASP A09)*

- Every significant action (scan creation, threat update, record addition) produces an immutable `AuditEvent` record in the database
- Client-side record integrity uses `window.crypto.subtle` SHA-256 hashing in a hash-chain structure — any record modification or deletion breaks the chain and is immediately detectable on the Records page

---

## Platform Features

### Smart Contract Scanner

- Paste any Solidity source code (supports 0.4.x → 0.8.x via automatic compiler selection)
- Four analysis engines run in parallel: **Slither** (80+ static detectors), **Mythril** (symbolic execution), **Echidna** (property-based fuzzing with auto-generated invariants), and a **Heuristic Analyzer** (6 regex-based logic-flaw checks)
- Each tool runs in full process / container isolation — Slither and Mythril in dedicated Python venvs, Echidna in a hardened Docker container, heuristic in-process
- Findings include SWC ID, severity (critical / high / medium / low / info), description, specific remediation, and originating tool
- Aggregate risk score computed via weighted exponential saturation model (0–100 scale) with per-tool reliability multipliers
- Results presented as a human-readable audit report with a risk grade (A–F), severity distribution, and expandable finding cards
- Every finding mapped to the OWASP Smart Contract Top 10

### Security Dashboard

- KPI cards: contracts scanned, critical vulnerabilities, active threats, overall risk score
- Scan activity chart and vulnerability distribution by severity

### Threat Model

- STRIDE-oriented threat catalogue (Spoofing, Tampering, Repudiation, Info Disclosure, DoS, Elevation of Privilege)
- Likelihood / impact scoring with derived risk scores and mitigation recommendations

### Audit Log

- Searchable, severity-tagged event timeline with actor, resource, and context per event

### Tamper-Proof Records

- SHA-256 hash chain with client-side chain verification and tampering detection

---

## Platform Security Domains & Codebase Mapping

| Domain | Backend | Frontend |
| --- | --- | --- |
| Security Scanning | [`finsec-guardian-api/scanner/`](../finsec-guardian-api/scanner/) | [`src/pages/Scanner.jsx`](src/pages/Scanner.jsx) |
| Threat Management | [`finsec-guardian-api/threats/`](../finsec-guardian-api/threats/) | [`src/pages/ThreatModel.jsx`](src/pages/ThreatModel.jsx) |
| Audit & Compliance | [`finsec-guardian-api/audit/`](../finsec-guardian-api/audit/) | [`src/pages/AuditLog.jsx`](src/pages/AuditLog.jsx) |
| Records Management | [`finsec-guardian-api/records/`](../finsec-guardian-api/records/) | [`src/pages/TamperProofRecords.jsx`](src/pages/TamperProofRecords.jsx) |
| Auth & Settings | [`finsec-guardian-api/config/`](../finsec-guardian-api/config/) | [`src/pages/Login.jsx`](src/pages/Login.jsx), [`src/pages/Settings.jsx`](src/pages/Settings.jsx) |

---

## Tech Stack

### Frontend

- React 18 (JSX) · Vite 5 · Tailwind CSS
- shadcn/ui + Radix UI · lucide-react · Recharts
- React Router v6 · TanStack Query v5
- Vitest + Testing Library · Playwright (E2E)

### Backend

- Python 3.11+ · Django 5 · Django REST Framework
- `djangorestframework-simplejwt` · `django-cors-headers` · `python-decouple`
- Slither (Trail of Bits) · Mythril (ConsenSys) · Echidna (Crytic) — each in a dedicated virtualenv or Docker container
- Custom Heuristic Analyzer — 6 regex-based logic-flaw checks
- Risk Scoring Engine — weighted exponential saturation model
- PostgreSQL

---

## Project Structure

```text
src/
  pages/
    Login.jsx              # Public landing page + auth (honeypot, sign in, register)
    Index.jsx              # Security dashboard (KPIs, charts, recent scans)
    Scanner.jsx            # Contract scanner — paste Solidity, view findings
    ThreatModel.jsx        # STRIDE threat catalogue and risk scoring
    AuditLog.jsx           # Security event timeline
    TamperProofRecords.jsx # Hash-chain record verification
    Settings.jsx           # Security and scanner settings
  components/
    AppLayout.jsx          # Sidebar + routed layout shell (authenticated area)
  hooks/
    use-theme.js           # Light/dark theme toggle with localStorage persistence
    use-mobile.js          # Mobile breakpoint detection
  lib/
    api.js                 # JWT API client — silent refresh, 401 handling, tokenStorage
    utils.js               # Tailwind class utilities
public/
  robots.txt              # Crawler policy — bad bots blocked, /api/ disallowed globally
```

---

## Getting Started

### Prerequisites

- Node.js 18+ (20+ recommended)
- `finsec-guardian-api` running locally (see that repo's README)

### Install

```bash
npm install
```

### Run Development Server

```bash
npm run dev
```

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

### Lint

```bash
npm run lint
```

### Unit / Component Tests

```bash
npm run test
```

### Watch Tests

```bash
npm run test:watch
```

---

## Known Limitations

- No file upload parser (multi-file / Hardhat project support not yet implemented)
- Tamper-proof records use a client-side SHA-256 simulation — no on-chain anchoring yet
- Dashboard metrics are derived from persisted scan data; no real-time streaming
- Invariant generation is regex-based — AST-based approach via Slither IR planned for future iterations

## Roadmap

1. Public `/free-audit` scanner — unauthenticated contract scan with limited results
2. File upload and multi-contract project support
3. On-chain record anchoring (EVM compatible)
4. CI mode — GitHub Action / CLI for repository-based scans
5. AST-based invariant generation (upgrade from regex to Slither IR)
6. Foundry and Semgrep integration as additional analysis engines

---

## Vision

FinSec Guardian is a unified smart contract security operations console — and a demonstration that security tooling must itself be built securely. The platform practises the OWASP principles it teaches: hardened HTTP headers, strict authentication, input validation at every boundary, tamper-evident audit records, and active bot mitigation. Four analysis engines (Slither, Mythril, Echidna, Heuristic) are orchestrated through a normalised pipeline with explainable risk scoring — findings are actionable, not just noise.

Built on [OWASP SC Top 10](https://scs.owasp.org/sctop10/) · Powered by [Slither](https://github.com/crytic/slither), [Mythril](https://github.com/Consensys/mythril) & [Echidna](https://github.com/crytic/echidna) · Contact [datasubjectsrights@finsec.com](mailto:datasubjectsrights@finsec.com)
