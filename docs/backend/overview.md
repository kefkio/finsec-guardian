# Backend — Overview

**Status:** Current  
**Last Updated:** April 2026  
**Audience:** Developers, Architects

---

## Table of Contents

1. [Technology Stack](#technology-stack)
2. [Project Structure](#project-structure)
3. [Django Applications](#django-applications)
4. [Configuration](#configuration)
5. [API Overview](#api-overview)
6. [Service Layer](#service-layer)
7. [Quick Start](#quick-start)

---

## Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Framework** | Django | 5.x | Web framework |
| **API** | Django REST Framework | 3.17 | RESTful API layer |
| **Auth** | SimpleJWT | 5.x | JWT access + refresh tokens |
| **CORS** | django-cors-headers | — | Cross-origin request control |
| **Database** | PostgreSQL | 14+ | Primary data store |
| **DB Driver** | psycopg2-binary | — | PostgreSQL adapter |
| **Config** | python-decouple | — | Environment variable management |
| **Static Analysis** | Slither | latest | Solidity vulnerability detection |
| **Symbolic Execution** | Mythril | latest | EVM path exploration |
| **Fuzzing** | Echidna | v2.2.5 | Property-based testing (Docker) |
| **Compiler** | solcx (py-solc-x) | — | Solidity compilation |

---

## Project Structure

```
finsec-guardian-api/
├── manage.py                      # Django management entry point
├── requirements.txt               # Python dependencies
├── setup_echidna.sh               # Echidna Docker setup script
│
├── config/                        # Django project configuration
│   ├── settings.py                # All settings (DB, auth, CORS, engines)
│   ├── urls.py                    # Root URL routing
│   ├── wsgi.py                    # WSGI entry point
│   └── asgi.py                    # ASGI entry point
│
├── scanner/                       # Core scanning application
│   ├── models.py                  # ScanJob, Finding, ScanReport, etc.
│   ├── views.py                   # ScanJobViewSet + quick_scan
│   ├── views_auth.py              # RegisterView
│   ├── serializers.py             # ScanJob/Finding serializers
│   ├── serializers_auth.py        # Registration serializer
│   ├── urls.py                    # Scanner URL routing
│   ├── admin.py                   # Django admin config
│   ├── compiler.py                # SolidityCompiler (solcx wrapper)
│   ├── slither_runner.py          # Legacy Slither runner
│   ├── slither_parser.py          # Slither output parser
│   ├── reporting.py               # Report generation (JSON/PDF/HTML)
│   ├── tasks.py                   # Async task definitions
│   │
│   ├── services/                  # Business logic layer
│   │   ├── orchestrator.py        # ScanOrchestrator (pipeline coordinator)
│   │   ├── normalizer.py          # FindingNormalizer (schema unification)
│   │   ├── risk_scorer.py         # RiskScorer (deterministic scoring)
│   │   ├── persistence.py         # ScanPersistence (DB operations)
│   │   ├── file_processing.py     # SolidityFileProcessingService
│   │   ├── compilation_service.py # Compilation wrapper
│   │   ├── gas_service.py         # Gas analysis
│   │   ├── compliance_service.py  # Regulatory checks
│   │   │
│   │   ├── analyzers/             # Pluggable analysis engines
│   │   │   ├── base.py            # AnalyzerResult dataclass
│   │   │   ├── slither.py         # SlitherAnalyzer
│   │   │   ├── mythril.py         # MythrilAnalyzer
│   │   │   ├── echidna.py         # EchidnaAnalyzer (Docker)
│   │   │   └── heuristic.py       # HeuristicAnalyzer (regex)
│   │   │
│   │   ├── etherscan/             # On-chain intelligence layer
│   │   │   ├── client.py          # EtherscanClient (API wrapper)
│   │   │   ├── fetcher.py         # EtherscanFetcher (data aggregator)
│   │   │   ├── analyzer.py        # EtherscanAnalyzer (behavioral analysis)
│   │   │   └── reputation.py      # ReputationScorer (0–100)
│   │   │
│   │   └── invariants/            # Automated invariant generation
│   │       ├── generator.py       # AST → invariant rules
│   │       ├── injector.py        # Inject into test contracts
│   │       └── patterns.py        # Template library
│   │
│   ├── management/                # Custom management commands
│   ├── migrations/                # Database schema migrations
│   └── tests/                     # Test suite
│
├── threats/                       # STRIDE threat catalogue
│   ├── models.py                  # ThreatRecord
│   ├── views.py                   # ThreatRecordViewSet
│   ├── serializers.py             # ThreatRecordSerializer
│   └── urls.py
│
├── records/                       # Tamper-proof hash chain
│   ├── models.py                  # TamperRecord
│   ├── views.py                   # TamperRecordViewSet (append-only)
│   ├── serializers.py             # TamperRecordSerializer
│   └── urls.py
│
├── audit/                         # Audit event logging
│   ├── models.py                  # AuditEvent
│   ├── views.py                   # AuditEventViewSet (append-only)
│   ├── serializers.py             # AuditEventSerializer
│   └── urls.py
│
├── venv-slither/                  # Slither Python virtual environment
└── venv-mythril/                  # Mythril Python virtual environment
```

---

## Django Applications

| App | Purpose | Key Models | Access Pattern |
|-----|---------|-----------|----------------|
| **scanner** | Smart contract scanning pipeline | `ScanJob`, `Finding`, `FindingCategory`, `SuppressionBaseline`, `ScanReport`, `SolidityVersion` | Full CRUD |
| **threats** | STRIDE threat catalogue | `ThreatRecord` | Full CRUD |
| **records** | Tamper-proof hash chain | `TamperRecord` | Append-only + verify |
| **audit** | Security event log | `AuditEvent` | Append-only |

---

## Configuration

Settings are managed through `config/settings.py` and environment variables via `python-decouple`.

### Key Settings

| Setting | Source | Default | Description |
|---------|--------|---------|-------------|
| `SECRET_KEY` | `.env` | dev key | Django secret key |
| `DEBUG` | `.env` | `True` | Debug mode |
| `ALLOWED_HOSTS` | `.env` | `localhost,127.0.0.1` | Allowed host headers |
| `CORS_ALLOWED_ORIGINS` | `.env` | `localhost:8080,5173` | CORS whitelist |
| `SLITHER_TIMEOUT` | `settings.py` | 120 s | Slither subprocess timeout |
| `ECHIDNA_DOCKER_IMAGE` | `.env` | `echidna:v2.2.5` | Echidna Docker image |
| `ECHIDNA_TIMEOUT` | `.env` | 120 s | Echidna execution timeout |
| `ETHERSCAN_API_KEY` | `.env` | `""` (disabled) | Etherscan API key |
| `ETHERSCAN_BASE_URL` | `.env` | `https://api.etherscan.io/api` | Etherscan endpoint |
| `ETHERSCAN_TIMEOUT` | `.env` | 30 s | Etherscan HTTP timeout |

### Database

PostgreSQL with the following connection:
```
ENGINE: django.db.backends.postgresql
NAME: finsec_guardian_api
USER: finsec_admin
HOST: localhost
PORT: 5432
```

---

## API Overview

### URL Routing

```python
# config/urls.py
urlpatterns = [
    path('admin/',         admin.site.urls),
    path('api/scanner/',   include('scanner.urls')),
    path('api/threats/',   include('threats.urls')),
    path('api/audit/',     include('audit.urls')),
    path('api/records/',   include('records.urls')),
    path('api/auth/login/',   TokenObtainPairView),
    path('api/auth/refresh/', TokenRefreshView),
]
```

### Scanner Endpoints

| Method | Path | Description |
|--------|------|------------|
| `POST` | `/api/scanner/scans/` | Create new scan (source_code or file upload) |
| `GET` | `/api/scanner/scans/` | List user's scans |
| `GET` | `/api/scanner/scans/{id}/` | Get scan detail (includes findings, onchain_data) |
| `POST` | `/api/scanner/scans/trigger/` | Synchronous scan (no persistence) |
| `GET` | `/api/scanner/scans/{id}/findings/` | Get scan findings (filterable by severity) |
| `GET` | `/api/scanner/scans/{id}/statistics/` | Get severity breakdown + metrics |
| `GET` | `/api/scanner/scans/{id}/risk/` | Get risk assessment |
| `POST` | `/api/scanner/scans/{id}/suppress-finding/` | Suppress a finding |
| `POST` | `/api/scanner/scans/{id}/acknowledge-finding/` | Acknowledge a finding |
| `POST` | `/api/scanner/scans/{id}/mark-resolved/` | Mark finding resolved |
| `POST` | `/api/scanner/scans/{id}/export-report/` | Export as JSON/PDF/HTML |
| `POST` | `/api/scanner/register/` | User registration |

---

## Service Layer

The business logic lives in `scanner/services/`, separated from views and models. The orchestrator coordinates all services.

**Core services:**
- `ScanOrchestrator` — pipeline coordinator, runs all engines + Etherscan
- `FindingNormalizer` — converts tool output to canonical schema
- `RiskScorer` — computes risk score with on-chain adjustment
- `ScanPersistence` — DB operations (create/update findings, status management)

**Analysis engines:**
- `SlitherAnalyzer` — static analysis via subprocess
- `MythrilAnalyzer` — symbolic execution via subprocess
- `EchidnaAnalyzer` — property-based fuzzing via Docker
- `HeuristicAnalyzer` — regex-based rule matching

**On-chain intelligence:**
- `EtherscanClient` — REST API wrapper with rate limiting
- `EtherscanFetcher` — data aggregator
- `EtherscanAnalyzer` — behavioral analysis
- `ReputationScorer` — reputation scoring (0–100)

**Details:** [Architecture](architecture.md) · [Orchestrator](orchestrator.md) · [Analyzers](analyzers.md) · [Risk Scoring](risk-scoring.md)

---

## Quick Start

```bash
# Navigate to backend
cd finsec-guardian-api

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up PostgreSQL database
createdb finsec_guardian_api

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver

# (Optional) Set up Echidna Docker
./setup_echidna.sh

# (Optional) Configure Etherscan
# Add ETHERSCAN_API_KEY to .env file
```
