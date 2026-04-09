# FinSec Guardian

FinSec Guardian is a smart contract security operations console: a React frontend backed by a Django REST Framework API that drives real Solidity static analysis via [Slither](https://github.com/crytic/slither).

It provides:

- **Real Slither-powered contract scanning** — paste Solidity, click Scan, receive live findings
- Contract scan workflow and findings panel (critical / high / medium / low / info, SWC IDs)
- Threat model visualization and management
- Audit log timeline (auto-populated on every scan)
- Tamper-evident hash-chained record store
- Security settings dashboard

## What This Project Is

- A React + Vite frontend (JavaScript / JSX)
- A Django + Django REST Framework backend with Slither integration
- Full-stack: every page talks to a real API backed by SQLite (swappable to Postgres)

## Current Feature Set

### 1) Contract Scanner

- Paste Solidity source code in an editor panel
- Trigger a scan workflow with progress state
- View categorized findings (critical/high/medium/low/info)
- Read recommendations per finding with SWC-style IDs

Current behavior:

- Scanner results are mock findings defined in the frontend
- No compiler parsing, AST pass, symbolic execution, or bytecode analysis yet

### 2) Security Dashboard


## Platform Security Domains & Codebase Mapping

The platform is organized into the following security domains:

### 1. Security Scanning Domain
- **Backend:** [`backend/scanner/`](backend/scanner/) — Scan job models, Slither runner, DRF views
- **Frontend:** [`src/pages/Scanner.jsx`](src/pages/Scanner.jsx) — UI for submitting and viewing scan results

### 2. Threat Management Domain
- **Backend:** [`backend/threats/`](backend/threats/) — Threat CRUD with STRIDE categories and risk scoring
- **Frontend:** [`src/pages/ThreatModel.jsx`](src/pages/ThreatModel.jsx) — UI for threat modeling and management

### 3. Audit & Compliance Domain
- **Backend:** [`backend/audit/`](backend/audit/) — Audit event log (auto-populated by signals on every scan)
- **Frontend:** [`src/pages/AuditLog.jsx`](src/pages/AuditLog.jsx) — Interface for viewing audit trails

### 4. Records Management Domain
- **Backend:** [`backend/records/`](backend/records/) — SHA-256 hash-chained tamper-evident records with server-side verification
- **Frontend:** [`src/pages/TamperProofRecords.jsx`](src/pages/TamperProofRecords.jsx) — UI for managing and viewing records

### 5. Configuration
- **Settings:** [`backend/config/settings.py`](backend/config/settings.py) — Django settings (CORS, DRF, DB)
- **Routing:** [`backend/config/urls.py`](backend/config/urls.py) — API endpoint routing for all domains

---

- High-level KPI cards (contracts scanned, critical vulns, active threats, risk score)
- Scan activity chart and vulnerability distribution chart
- Recent scans list

Current behavior:

- Dashboard data is static demo data

### 3) Threat Model

- STRIDE-oriented threat cards
- Likelihood/impact scoring and derived risk score
- Mitigation recommendations by threat type

Current behavior:

- Threat records are static demo scenarios

### 4) Audit Log

- Searchable event stream UI
- Severity-tagged timeline entries with actor/resource/IP context

Current behavior:

- Entries are static demo events

### 5) Tamper-Proof Records

- Client-side hash chain simulation (SHA-256 via browser crypto API)
- Add records, verify chain integrity, and simulate tampering
- Display simulated Solidity contract for anchoring concept

Current behavior:

- No wallet connection, no deployed contract, no on-chain writes yet

## Tech Stack

- React 18
- TypeScript
- Vite 5
- Tailwind CSS
- shadcn/ui + Radix UI
- Recharts (visualizations)
- React Router
- TanStack Query (available in app setup)
- Vitest + Testing Library
- Playwright (configured)

## Project Structure

- src/pages/Scanner.tsx: scanner flow and findings UI (mock analysis)
- src/pages/Dashboard.tsx: security metrics and charts
- src/pages/ThreatModel.tsx: threat catalog and risk modeling view
- src/pages/AuditLog.tsx: security event timeline
- src/pages/TamperProofRecords.tsx: hash-chain simulation and verification
- src/pages/Settings.tsx: security and scanner settings UI
- src/components/AppLayout.tsx: sidebar + routed layout shell

## Getting Started

### Prerequisites

- Node.js 18+ (Node.js 20+ recommended)
- npm
- Python 3.10+
- pip

---

### Backend Setup (Django + Slither)

```bash
cd backend

# Install Python dependencies (Django, DRF, Slither, solc-select)
pip install -r requirements.txt

# Install and activate the Solidity compiler (required by Slither)
solc-select install 0.8.20
solc-select use 0.8.20

# Apply database migrations
python manage.py migrate

# Start the API server (default: http://localhost:8000)
python manage.py runserver
```

> **Tip:** A convenience script is available:
> ```bash
> bash backend/setup.sh
> ```

#### Environment Variables (optional)

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | dev-only default | Django secret key — **set in production** |
| `DJANGO_DEBUG` | `True` | Set to `False` in production |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hosts |

---

### Frontend Setup

### Install

```bash
npm install
```

Copy `.env.example` to `.env` (already points to `http://localhost:8000/api`):

```bash
cp .env.example .env
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

### Unit/Component Tests

```bash
npm run test
```

### Backend Tests

```bash
cd backend
python manage.py test scanner.tests -v 2
```

### Watch Tests

```bash
npm run test:watch
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/scanner/scans/` | List all scans |
| POST | `/api/scanner/scans/` | Submit contract for Slither analysis |
| GET | `/api/scanner/scans/{id}/` | Get scan details + findings |
| GET | `/api/scanner/scans/{id}/findings/` | Get findings for a scan |
| GET | `/api/threats/threats/` | List threat model entries |
| POST | `/api/threats/threats/` | Create a threat |
| PATCH | `/api/threats/threats/{id}/` | Update a threat |
| DELETE | `/api/threats/threats/{id}/` | Delete a threat |
| GET | `/api/audit/events/` | List audit events (supports `?search=`) |
| GET | `/api/records/records/` | List tamper-proof records |
| POST | `/api/records/records/` | Add a new record (server hashes + chains) |
| GET | `/api/records/records/verify/` | Verify entire hash chain integrity |


## Security Scanner Scope (Planned)

The intended scanner scope includes:

- SWC-aligned rule detection
- Reentrancy, access control, arithmetic safety, DoS patterns
- Compiler/version hygiene checks
- Severity scoring and remediation guidance
- JSON report export and CI integration

Suggested implementation path:

1. Add a backend analysis service (Node/Python)
2. Integrate Slither or Mythril for first-pass findings
3. Normalize findings to a shared schema
4. Replace mock findings in the scanner page with API responses
5. Persist scan history and audit events

## Known Limitations

- No real static analysis pipeline yet
- No file upload parser or multi-contract project support
- No authentication backend
- No persistent storage/database
- No blockchain RPC, wallet, or contract deployment integration
- Most pages currently use in-memory/static data

## Recommended Next Milestones

1. Build a real scanner API and connect the scanner UI
2. Add finding suppression/baselines and report export
3. Add user auth + RBAC + persistent audit storage
4. Add on-chain anchoring for tamper-proof records
5. Add CI mode for repository-based contract scans

## Vision

FinSec Guardian is positioned as a unified smart contract security operations console:

- Analyze Solidity contracts
- Track threat posture over time
- Preserve tamper-evident security events
- Support audit and compliance workflows

This repository currently delivers the interface foundation and interaction model needed to evolve into that full platform.
