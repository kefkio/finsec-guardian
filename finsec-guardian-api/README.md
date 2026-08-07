# FinSec Guardian — API

This backend provides the REST API for the FinSec Guardian platform. It coordinates analysis runs, normalises findings, computes risk output, and stores scan-related records for the frontend experience.

## Current backend architecture

The backend is structured around a layered pipeline:

```text
Analyzers → Orchestrator → Normalizer → Risk Scorer → Persistence → API
```

### Core responsibilities

- Run analysis engines and collect tool output
- Normalise heterogeneous findings into a common schema
- Compute aggregate risk scores and scan summaries
- Persist scan state, findings, threats, and audit events
- Expose the workflow through DRF endpoints

## Domain analysis flow

The current domain layer adds a second analytical stage on top of raw findings. Findings are correlated, assembled into graph components, and transformed into attack paths.

```text
Raw findings
  ↓
FindingCorrelationService
  ↓
CorrelationEdge
  ↓
CorrelationGraph
  ↓
CorrelationComponent
  ↓
AttackPathService
  ↓
AttackPath
```

## Main backend modules

| Area | Purpose |
| --- | --- |
| scanner/services/analyzers | Tool-specific execution and result parsing |
| scanner/services/orchestrator.py | Coordinates the scan pipeline |
| scanner/services/normalizer.py | Converts raw output into the canonical finding schema |
| scanner/services/risk_scorer.py | Computes aggregate risk values |
| scanner/domain/services | Correlation and attack-path discovery services |
| scanner/domain/value_objects | Immutable domain artefacts such as attack paths and graph components |

## Quick start

```bash
cd finsec-guardian-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Notes

The backend remains under active development. The focus is now on tightening the analysis pipeline, improving the domain layer, and making the outputs easier to reason about for both users and contributors.
**Severity weights (10-point scale):**

| Severity | Weight |
| --- | --- |
| Critical | 10 |
| High | 7 |
| Medium | 4 |
| Low | 2 |
| Info | 1 |

**Tool reliability multipliers:**

| Tool | Weight | Rationale |
| --- | --- | --- |
| Echidna | 1.2 | Runtime-verified exploits (highest confidence) |
| Mythril | 1.0 | Symbolic execution with formal reasoning |
| Slither | 0.9 | Pattern-based static analysis |
| Heuristic | 0.85 | Regex-based logic-flaw detection |

**Aggregate scoring:**

$$\text{Risk} = 100 \times \left(1 - e^{-0.08 \times S}\right)$$

where $S$ is the sum of all per-finding scores plus a diversity bonus (capped at 5.0). The exponential saturation function bounds the score to 0–100 and prevents a single low-severity finding from inflating the risk.

**Risk verdicts:**

| Score | Verdict |
| --- | --- |
| 85+ | CRITICAL RISK |
| 70–84 | HIGH RISK |
| 50–69 | MEDIUM RISK |
| 25–49 | LOW RISK |
| 0–24 | MINIMAL RISK |

A single critical finding enforces a minimum floor score of 80. Echidna findings receive an additional 1.5× boost as runtime exploit evidence.

### Per-Finding Risk Score

Each persisted `Finding` also exposes a per-finding risk score via `get_risk_score()`:

$$\text{risk\_score} = W_{\text{severity}} \times \frac{\text{confidence}}{100}$$

| Severity | Weight |
| --- | --- |
| Critical | 100 |
| High | 75 |
| Medium | 50 |
| Low | 25 |
| Info | 5 |

`ScanJob` maintains pre-aggregated counts (`critical_count`, `high_count`, `medium_count`, `low_count`, `info_count`) updated on scan completion for efficient API responses.

### Adding New Engines

The analyzer-based architecture allows additional engines to be integrated with minimal changes:

- Foundry fuzzing (`forge test`)
- Semgrep (pattern-based static analysis)
- Custom ML-based vulnerability classifiers

Only a new analyzer implementation conforming to the `AnalyzerResult` contract is required; orchestration, normalisation, and persistence remain unchanged.

### Django Apps

| App | Responsibility |
| --- | --- |
| `scanner` | Scan job lifecycle, Slither + Mythril + Echidna + Heuristic orchestration, finding persistence, risk scoring, report generation |
| `threats` | STRIDE threat catalogue with likelihood / impact scoring |

| `audit` | Immutable audit event log |
| `records` | Tamper-evident records using SHA-256 hash chaining (blockchain-style integrity model) |

---

## API Reference

All endpoints require a `Bearer` JWT token in the `Authorization` header unless stated otherwise.

### Authentication

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/scanner/register/` | Register new user |
| `POST` | `/api/auth/login/` | Obtain JWT access + refresh tokens |
| `POST` | `/api/auth/refresh/` | Refresh expired access token |

### Scanner

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/scanner/scans/` | List authenticated user's scan jobs |
| `POST` | `/api/scanner/scans/` | Submit Solidity source for analysis |
| `GET` | `/api/scanner/scans/{id}/` | Retrieve scan job detail and findings |
| `GET` | `/api/scanner/scans/{id}/findings/` | Get findings (filterable by severity) |
| `GET` | `/api/scanner/scans/{id}/statistics/` | Get scan statistics and severity breakdown |
| `GET` | `/api/scanner/scans/{id}/risk/` | Get aggregate risk assessment |
| `POST` | `/api/scanner/scans/{id}/suppress_finding/` | Suppress a finding with reason |
| `POST` | `/api/scanner/scans/{id}/acknowledge_finding/` | Mark a finding as reviewed |
| `POST` | `/api/scanner/scans/{id}/mark_resolved/` | Mark a finding as resolved |
| `POST` | `/api/scanner/scans/{id}/export_report/` | Export report (JSON, HTML, or PDF) |
| `POST` | `/api/scanner/scans/trigger/` | Ad-hoc scan without persistence |
| `DELETE` | `/api/scanner/scans/{id}/` | Delete a scan job |

**Submit scan — request body:**

```json
{
  "contract_name": "MyToken",
  "source_code": "pragma solidity ^0.8.0; ..."
}
```

### Threats

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/threats/threats/` | List threat records |
| `POST` | `/api/threats/threats/` | Create threat record |
| `GET` | `/api/threats/threats/{id}/` | Retrieve threat detail |
| `PUT` | `/api/threats/threats/{id}/` | Update threat record |
| `DELETE` | `/api/threats/threats/{id}/` | Delete threat record |

### Audit Log

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/audit/events/` | List audit events (read-only) |
| `GET` | `/api/audit/events/{id}/` | Retrieve single audit event |

### Tamper-Proof Records

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/records/records/` | List records |
| `POST` | `/api/records/records/` | Create record |
| `GET` | `/api/records/records/{id}/` | Retrieve record |
| `DELETE` | `/api/records/records/{id}/` | Delete record |

---

## Testing

### Running All Tests

```bash
.venv/bin/python manage.py test scanner --settings=config.test_settings --verbosity=2
```

### Test Suite Summary

**35 tests** across two modules — all passing.

#### Pipeline Integration Tests (`scanner/tests/test_pipeline.py` — 7 tests)

| Test | Description |
| --- | --- |
| `test_slither_service_detects_reentrancy` | Verifies Slither detects `reentrancy-eth` in a vulnerable bank contract |
| `test_create_scan_returns_findings_for_source_code` | End-to-end: POST source code → scan completes → findings returned |
| `test_create_scan_accepts_solidity_file_upload` | End-to-end: multipart `.sol` file upload → scan completes → findings returned |
| `test_invalid_solidity_upload_is_recorded_as_failed_scan` | Invalid Solidity → `status=failed`, `syntax_valid=false`, compilation error captured |
| `test_export_report_returns_structured_audit_report` | JSON export contains summary, severity levels, vulnerabilities, function breakdown |
| `test_export_report_returns_html_document` | HTML export returns valid `text/html` with audit report content |
| `test_export_report_returns_pdf_document_when_reportlab_installed` | PDF export returns valid `application/pdf` (skipped if reportlab not installed) |

#### Invariant Engine Unit Tests (`scanner/tests/test_invariant_generator.py` — 28 tests)

| Category | Tests | What is validated |
| --- | --- | --- |
| **Correct Generation** (4) | Basic contract, token contract, naming convention, count consistency | Each Solidity type produces the correct `echidna_*` invariants |
| **Determinism** (3) | Code output, cross-instance, name ordering | Identical input always produces identical output (research reproducibility) |
| **Deduplication** (2) | Name uniqueness, no duplicate function bodies | Duplicate state variable declarations emit unique invariants |
| **Pattern Isolation** (7) | uint-only, keyword filtering, owner-only, multi-owner, bool-only, balance always fires, custom override | Each pattern matches only its target variable category |
| **Empty Contract Safety** (3) | Empty contract, empty string, comment-only source | Generator handles edge cases without crashing |
| **No False Positives** (1) | `string`/`bytes` types only produce the baseline invariant | Non-matching types do not trigger spurious invariants |
| **Injector** (4) | Simple injection, last-contract targeting, empty code passthrough, no-contract fallback | Safe Solidity code injection into contract bodies |
| **End-to-End** (3) | Generate → inject round trip, original code preservation, inherited contract | Full pipeline from generation to injection |
| **Robustness** (1) | 11 adversarial inputs including null bytes and 10 KB strings | Generator never crashes on arbitrary input |

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Docker Engine (for Echidna fuzzer)
- `solc` binary on `PATH` (install via [solc-select](https://github.com/crytic/solc-select))

```bash
pip install solc-select
solc-select install 0.8.21
solc-select use 0.8.21
```

### 1. Clone and create the main virtualenv

```bash
cd finsec-guardian-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Create the Slither virtualenv

```bash
python3 -m venv venv-slither
venv-slither/bin/pip install slither-analyzer py-solc-x
```

### 3. Create the Mythril virtualenv

```bash
python3 -m venv venv-mythril
venv-mythril/bin/pip install mythril
```

### 4. Set up Echidna (Docker)

Echidna runs inside a Docker container — no Haskell toolchain needed on the host.

```bash
# Ensure your user is in the docker group (relogin after this)
sudo usermod -aG docker $USER

# Pull the Echidna image and verify
bash setup_echidna.sh
```

The setup script pulls `ghcr.io/crytic/echidna/echidna:v2.2.5` and runs a smoke test. The container runs as your host UID/GID with `--network none`, a read-only root FS, and capped CPU/memory.

### 5. Configure environment variables

Copy `.env.example` to `.env` (or create `.env`) and set:

```env
SECRET_KEY=<your-django-secret-key>
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://user:password@localhost:5432/finsec
CORS_ALLOWED_ORIGINS=http://localhost:8080

# Echidna (optional — defaults shown)
ECHIDNA_DOCKER_IMAGE=ghcr.io/crytic/echidna/echidna:v2.2.5
ECHIDNA_TIMEOUT=120
```

### 6. Apply migrations

```bash
.venv/bin/python manage.py migrate
```

### 7. Create a superuser (optional)

```bash
.venv/bin/python manage.py createsuperuser
```

### 8. Run the development server

```bash
.venv/bin/python manage.py runserver
```

The API will be available at `http://localhost:8000`.

---

## Security Controls

- All endpoints require `IsAuthenticated` — anonymous access returns HTTP 401
- JWT is the sole authentication class; session/cookie auth is disabled on the API
- All database queries use Django ORM — no raw SQL
- DRF serialisers validate and whitelist all incoming fields
- Solidity source is passed to analysis tools as a file — never executed or rendered as HTML
- `SECRET_KEY` and credentials loaded from environment variables via `python-decouple`
- `DEBUG=False` in production suppresses stack traces in HTTP responses
- Rate throttling via DRF `AnonRateThrottle` / `UserRateThrottle` on all endpoints
- Echidna Docker container runs as host UID/GID with `--network none`, read-only root FS, `--tmpfs /tmp:rw,noexec,nosuid`, and capped CPU (2) / memory (1 GB)

---

## Tech Stack

- Python 3.11+ · Django 5 · Django REST Framework 3
- `djangorestframework-simplejwt` · `django-cors-headers` · `python-decouple`
- Slither 0.11.5 (Trail of Bits) — static analysis, 80+ detectors
- Mythril 0.24.8 (ConsenSys) — symbolic execution
- Echidna 2.2.5 (Crytic) — property-based fuzzing (Docker)
- Heuristic Analyzer — regex-based logic-flaw detection (6 checks)
- PostgreSQL · psycopg2-binary

---

Built on [OWASP SC Top 10](https://scs.owasp.org/sctop10/) · Powered by [Slither](https://github.com/crytic/slither), [Mythril](https://github.com/Consensys/mythril) & [Echidna](https://github.com/crytic/echidna)
