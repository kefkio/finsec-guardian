# FinSec Guardian

FinSec Guardian is a research-oriented platform for auditing Solidity smart contracts before deployment. It combines multiple analysis engines, normalises their findings into a unified model, and produces explainable risk outputs for security review and reporting.

## Current Build

The current implementation spans a React frontend and a Django REST API backend. The backend now includes a domain-driven analysis flow for correlated findings, where raw findings are transformed into correlation edges, graph components, and attack paths before being surfaced as structured attack-path results.

### Repository layout

- Frontend: React + Vite + Tailwind in the finsec-guardian workspace
- Backend: Django + DRF in the finsec-guardian-api workspace
- Domain layer: correlation, graph, component, and attack-path services under the scanner domain package

## Core capabilities

- Multi-engine contract analysis with Slither, Mythril, Echidna, and heuristic checks
- Unified finding model with severity, confidence, remediation guidance, and metadata
- Deterministic risk scoring and scan-level reporting
- Domain-based attack-path discovery from correlated vulnerabilities
- Tamper-evident audit records and threat-model integration

## Architecture at a glance

```text
Frontend (React + Vite)
        ↓
API (Django + DRF)
        ↓
Scanner pipeline
  ├─ Analysis engines
  ├─ Normalisation
  ├─ Risk scoring
  └─ Persistence
        ↓
Domain analysis
  ├─ FindingCorrelationService
  ├─ CorrelationGraph
  ├─ CorrelationComponent
  └─ AttackPathService
```

## Quick start

### Backend

```bash
cd finsec-guardian-api
python3 -m venv .venv
source .venv/bin/activate
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

### Access

- Frontend: http://localhost:8080
- Backend: http://localhost:8000

## Project status

Current status: active development prototype.

Implemented:
- Full-stack web platform
- Multi-engine orchestration
- Risk scoring and reporting
- Correlation-based attack-path discovery

In progress:
- Expanded reporting workflows
- Additional risk assessment capabilities
- Further hardening and CI integration

## Documentation

- [docs/README.md](docs/README.md) for the main documentation index
- [finsec-guardian-api/README.md](finsec-guardian-api/README.md) for backend architecture and workflow details

## Requirements

- Node.js 18+
- Python 3.10+
- PostgreSQL
- Docker (optional for Echidna-based runs)

University of Michigan–Dearborn  

Research Interests:
Cybersecurity, Applied AI Security, Blockchain Security, Secure Systems
