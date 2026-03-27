# FinSec Guardian

FinSec Guardian is a smart contract security operations console — a React frontend backed by a Django REST Framework API for Solidity contract analysis and DeFi risk operations.

## Architecture

```
finsec-guardian/          ← React + Vite frontend (this repo)
finsec-guardian-api/      ← Django REST Framework backend (separate repo)
```

The frontend communicates with the DRF backend over a REST API. All data (scan jobs, findings, threat records, audit events, tamper-proof records) is persisted in PostgreSQL via the backend.

## Feature Set

### 1) Contract Scanner
- Paste Solidity source code and submit to the backend scan API
- Progress indicator while scan is processing
- View categorized findings (critical/high/medium/low/info) with SWC IDs, line numbers, and remediation guidance

> Scanner results currently come from the backend placeholder logic. Real static analysis (Slither/Mythril) is the next integration milestone.

### 2) Security Dashboard
- KPI cards: contracts scanned, critical vulnerabilities, active threats, risk score
- Scan activity chart and vulnerability distribution chart
- Live recent scans list pulled from the API

### 3) Threat Model
- STRIDE-oriented threat cards with likelihood/impact scoring
- Derived risk score per threat
- Mitigation recommendations — live data from the API (create/update/delete threats)

### 4) Audit Log
- Searchable, severity-tagged security event timeline
- Actor, resource, and IP context per event
- Live data from the API audit log endpoint

### 5) Tamper-Proof Records
- SHA-256 hash chain — records are stored and hashed server-side
- Add records and verify chain integrity via the API
- Displays a simulated Solidity contract for on-chain anchoring concept

## Tech Stack

### Frontend
- React 18 + JavaScript (JSX)
- Vite 5
- TanStack Query v5 (server state, caching, loading/error states)
- Tailwind CSS + shadcn/ui + Radix UI
- Recharts (visualizations)
- React Router

### Backend (`finsec-guardian-api/`)
- Django 5 + Django REST Framework
- PostgreSQL
- `django-cors-headers`, `python-decouple`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET/POST` | `/api/scanner/scans/` | List scans / submit new scan |
| `GET` | `/api/scanner/scans/{id}/findings/` | Findings for a specific scan |
| `GET/POST/PATCH` | `/api/threats/threats/` | STRIDE threat records |
| `GET/POST` | `/api/audit/events/` | Audit log (append-only) |
| `GET/POST` | `/api/records/records/` | Tamper-proof hash chain records |
| `GET` | `/api/records/records/verify/` | Verify full chain integrity |

## Project Structure

```
src/
├── lib/
│   ├── api.js              ← API service layer (all fetch calls)
│   └── utils.js
├── pages/
│   ├── Scanner.jsx         ← useMutation → POST /api/scanner/scans/
│   ├── Dashboard.jsx       ← useQuery → GET /api/scanner/scans/
│   ├── ThreatModel.jsx     ← useQuery/useMutation → /api/threats/
│   ├── AuditLog.jsx        ← useQuery → GET /api/audit/events/
│   ├── TamperProofRecords.jsx ← useQuery/useMutation → /api/records/
│   └── Settings.jsx
└── components/
    ├── AppLayout.jsx
    └── ui/                 ← shadcn/ui components
```

## Getting Started

### Prerequisites
- Node.js 18+
- The `finsec-guardian-api` backend running on port 8000 (see its README)

### Install & Configure

```bash
npm install
```

Copy and edit the environment file:
```bash
cp .env.example .env
# Set VITE_API_URL=http://localhost:8000/api
```

### Run Development Server

```bash
npm run dev
# Runs on http://localhost:8080
```

### Build for Production

```bash
npm run build
```

### Run Tests

```bash
npm run test
npm run test:watch
```

## Backend Setup (Quick Reference)

```bash
cd ../finsec-guardian-api
cp .env.example .env          # fill in DB credentials
createdb finsec_guardian
venv/bin/python manage.py migrate
venv/bin/python manage.py runserver
# API available at http://localhost:8000/api/
```

## Known Limitations

- No real Solidity static analysis engine yet (scanner stores submissions, returns empty findings until integrated)
- No authentication — API is open (JWT auth is the next planned milestone)
- No file upload / multi-contract project support
- No blockchain RPC, wallet, or on-chain contract deployment
- Dashboard aggregate stats (KPI cards, charts) are still static placeholders

## Roadmap

1. Integrate Slither/Mythril for real static analysis in the scanner backend
2. Add JWT authentication + RBAC
3. Add finding suppression, baselines, and JSON report export
4. Add on-chain anchoring for tamper-proof records
5. CI mode for repository-based contract scans

## Vision

FinSec Guardian is positioned as a unified smart contract security operations console:
- Analyze Solidity contracts with real static analysis
- Track threat posture over time
- Preserve tamper-evident, API-backed security events
- Support audit and compliance workflows

