# FinSec Guardian — API

Django REST Framework backend for the [FinSec Guardian](../finsec-guardian) smart contract security platform.

Exposes a secured REST API that orchestrates **Slither**, **Mythril**, **Echidna**, and a custom **Heuristic Analyzer** (four analysis engines), persists scan results, computes aggregate risk scores, manages STRIDE threat records, and maintains a tamper-evident audit trail.

| Repo | Purpose |
| --- | --- |
| `finsec-guardian` | React frontend |
| `finsec-guardian-api` (this repo) | Django REST API — scanner, threats, audit, records |

---

## Architecture

### Scan Pipeline

Every scan flows through a layered pipeline:

```text
Pluggable Analyzers → Scan Orchestrator → Finding Normalizer → Risk Scorer → Persistence Layer → API Interface
```

| Layer | Module | Responsibility |
| --- | --- | --- |
| **Analyzers** | `scanner/services/analyzers/` | Run each tool in process / container isolation and return a typed `AnalyzerResult` |
| **Orchestrator** | `scanner/services/orchestrator.py` | Executes analyzers sequentially, enforces per-tool timeouts, aggregates results, ensures fault isolation |
| **Normalizer** | `scanner/services/normalizer.py` | Converts heterogeneous tool output into a unified finding schema; sanitises temporary file paths and raw Docker output |
| **Risk Scorer** | `scanner/services/risk_scorer.py` | Computes a weighted aggregate risk score (0–100) with per-tool reliability multipliers and exponential saturation |
| **Persistence** | `scanner/services/persistence.py` | Manages `ScanJob` lifecycle state machine and idempotent `Finding` upserts |
| **API** | `scanner/views.py` | DRF viewset exposing scan CRUD, risk assessment, finding management, and report export endpoints |

### Analysis Engines

Each tool runs in **full process / container isolation** — the main Django `.venv` contains none of the analysis runtimes.

| Engine | Isolation | Description |
| --- | --- | --- |
| **Slither** (Trail of Bits) | Python venv (`venv-slither/`) | Static analysis with 80+ detectors — executed in an isolated Python virtual environment via subprocess |
| **Mythril** (ConsenSys) | Python venv (`venv-mythril/`) | Symbolic execution and SMT-based bug finding — executed in an isolated Python virtual environment via subprocess |
| **Echidna** (Crytic) | Docker container | Property-based fuzzing engine that generates randomised transaction sequences to break user-defined invariants (`echidna_*` functions); outputs counterexamples when invariants are violated |
| **Heuristic Analyzer** | In-process | Regex-based source analysis that detects logic flaws Slither and Mythril miss — unguarded state mutations, missing input validation, unguarded Ether sends, DoS via external calls, missing events, and missing ownership patterns |

```text
finsec-guardian-api/
  .venv/                          # Django + DRF runtime (no analysis tools)
  venv-slither/                   # slither-analyzer 0.11.5 + py-solc-x
  venv-mythril/                   # mythril 0.24.8
  scanner/
    services/
      analyzers/
        base.py                   # AnalyzerResult dataclass
        slither.py                # Calls venv-slither via subprocess
        mythril.py                # Calls venv-mythril via subprocess
        echidna.py                # Calls Echidna via Docker container
        heuristic.py              # Regex-based logic-flaw detection (6 checks)
      invariants/
        patterns.py               # Pluggable invariant pattern rules
        generator.py              # Core invariant generation engine
        injector.py               # Safe Solidity source injection
      orchestrator.py             # Pipeline coordinator
      normalizer.py               # Unifies raw output into findings
      persistence.py              # ScanJob lifecycle + Finding upsert
      risk_scorer.py              # Weighted aggregate risk scoring engine
      _slither_runner_script.py   # Runs inside venv-slither; outputs JSON
      _mythril_runner_script.py   # Runs inside venv-mythril; outputs JSON
    tests/
      __init__.py
      test_pipeline.py            # 7 integration tests (API + Slither pipeline)
      test_invariant_generator.py # 28 unit tests (invariant engine)
```

### Analyzer Interface Contract

All analysis engines implement a common interface defined in `scanner/services/analyzers/base.py`:

```python
analyze(source_code: str, contract_name: str | None = None) -> AnalyzerResult
```

Where `AnalyzerResult` is a typed dataclass:

```python
@dataclass
class AnalyzerResult:
    success: bool                          # True if analysis completed without fatal error
    raw_output: dict = field(default_factory=dict)  # Tool-specific structured data
    error: str | None = None               # Error message (if failed)
    stderr: str = ""                       # Captured stderr from subprocess
    tool: str = ""                         # "slither", "mythril", "echidna", or "heuristic"
```

This abstraction allows all four engines to be plugged into the pipeline without modifying orchestration logic. Each analyzer:

1. Writes Solidity source to a temporary `.sol` file (or analyses in-process for heuristic)
2. Executes the tool via subprocess (or Docker)
3. Parses JSON output from stdout
4. Returns a structured `AnalyzerResult`

### Unified Finding Schema

All analyzer outputs are normalised by `FindingNormalizer` into a consistent canonical structure:

```json
{
  "swc_id": "SWC-107",
  "title": "Reentrancy",
  "severity": "critical | high | medium | low | info",
  "description": "Detailed explanation of the vulnerability",
  "recommendation": "Remediation guidance",
  "confidence": 90,
  "line_number": 42,
  "line_start": 40,
  "line_end": 45,
  "column": 8,
  "code_snippet": "msg.sender.call{value: amount}(\"\")",
  "tags": ["slither", "reentrancy"],
  "reference_url": "https://swcregistry.io/docs/SWC-107",
  "metadata": { "tool": "slither" }
}
```

Tool-specific mapping rules:

| Tool | Severity mapping | Confidence | Notes |
| --- | --- | --- | --- |
| **Slither** | `High → high`, `Medium → medium`, `Low → low`, `Informational/Optimization → info` | `High → 90`, `Medium → 65`, `Low → 40` | Extracts line info from `source_mapping.lines`; recommendations from curated lookup table |
| **Mythril** | `High → high`, `Medium → medium`, `Low → low`, others → `info` | Fixed at 70 | SWC IDs normalised to `SWC-XXX` format; titles from internal SWC label map |
| **Echidna** | Failed invariants → `high`, passed properties → `info` | 85 for failures | Counterexample transaction sequences embedded in description and metadata |
| **Heuristic** | Varies by check (critical / high / medium / low) | Fixed at 70 | Findings pass through normaliser unchanged; no post-processing needed |

The normaliser also sanitises temporary file paths from raw tool output and cleans up Docker error messages for human-readable reports.

### Heuristic Analyzer

The heuristic analyzer (`scanner/services/analyzers/heuristic.py`) complements Slither, Mythril, and Echidna by detecting semantic patterns that static and symbolic tools often miss. It performs six regex-based checks on the parsed function AST:

| Check | Method | Severity | Description |
| --- | --- | --- | --- |
| **Unguarded State Mutation** | `_check_unguarded_state_mutation()` | Critical / High | Flags public functions that write state via caller-supplied parameters without access control |
| **Missing Input Validation** | `_check_missing_input_validation()` | Medium | Flags public functions accepting `address` parameters without `address(0)` guards |
| **Unguarded Ether Send** | `_check_unguarded_ether_send()` | Critical / High | Flags public functions sending Ether without ACL — **critical** if entire balance is drained |
| **DoS via External Call** | `_check_dos_via_external_call()` | Medium | Flags direct Ether sends to `msg.sender` without pull-payment pattern (SWC-113) |
| **Missing Events** | `_check_missing_events()` | Low | Flags contracts with state-modifying functions but no event declarations or emissions |
| **Missing Ownership** | `_check_missing_ownership()` | High | Flags contracts lacking any governance mechanism (Ownable, AccessControl, `onlyOwner`) |

### Echidna Integration

Echidna is executed via a hardened Docker container with defence-in-depth isolation:

```bash
docker run --rm \
    --user <uid>:<gid> \
    --network none \
    --read-only \
    --tmpfs /tmp:rw,noexec,nosuid \
    --memory 1g \
    --cpus 2 \
    -v <host_dir>:<workdir>:ro \
    ghcr.io/crytic/echidna/echidna:v2.2.5 \
    <filename> --format json --timeout <seconds>
```

The analyzer workflow:

1. Checks Docker availability via `shutil.which("docker")` — fails fast with a clear error if missing
2. Auto-generates Echidna invariants from source via `InvariantGenerator` (see below)
3. Injects `echidna_*` functions into the contract body via `InvariantInjector`
4. Writes modified Solidity source to a temporary directory
5. Invokes `docker run` directly with `--format json` for structured output
6. Parses JSON stdout for test results (`passed`, `failed`, `error`)
7. Extracts counterexample transaction sequences from failed invariants
8. Cleans up via `shutil.rmtree()` (handles nested temp files)
9. Emits normalised findings — failed invariants mapped to severity `high`, auto-generated failures tagged with `auto-invariant`

Fallback: if stdout is not valid JSON, raw text output is captured and forwarded for manual inspection.

### Invariant Auto-Generation

The invariant engine (`scanner/services/invariants/`) automatically synthesises Echidna-compatible property functions from Solidity source code using regex-based heuristic pattern matching. This eliminates the need for hand-written `echidna_*` functions — the system infers safety properties from state variable declarations.

#### Invariant Pipeline

```text
Solidity Source → Pattern Engine → Generator → Injector → Modified Contract → Echidna
```

| Module | Responsibility |
| --- | --- |
| `patterns.py` | Pluggable pattern rules — each pattern detects a variable category and emits invariant function bodies |
| `generator.py` | Orchestrates all patterns, deduplicates output, extracts `echidna_*` function names for metadata tracking |
| `injector.py` | Safely inserts generated invariants inside the last `contract` body (after opening brace) |

#### Invariant Categories

| Category | Pattern Class | Trigger | Generated Property |
| --- | --- | --- | --- |
| **Balance Safety** | `UintNonNegativePattern` | `uint` state variables | `echidna_<var>_non_negative()` — always true by Solidity semantics; violation indicates storage corruption |
| **Access Control** | `OwnerNotZeroPattern` | `address` vars with "owner" in name | `echidna_<var>_not_zero()` — ensures ownership is never invalidated to zero-address |
| **Boolean Sanity** | `BoolSanityPattern` | `bool` state variables | `echidna_<var>_valid()` — detects storage-slot corruption pushing a bool outside `{0, 1}` |
| **Contract Balance** | `ContractBalancePattern` | Always fires | `echidna_contract_balance_non_negative()` — flags potential balance accounting bugs |

#### Injection Strategy

Invariants are injected **inside** the last `contract` body — not appended after the closing brace — to produce syntactically valid Solidity:

```solidity
contract MyToken {
    uint256 public totalSupply;
    address public owner;

    // === AUTO-GENERATED ECHIDNA INVARIANTS ===

    function echidna_totalSupply_non_negative() public view returns (bool) {
        return totalSupply >= 0;
    }

    function echidna_owner_not_zero() public view returns (bool) {
        return owner != address(0);
    }

    // ... original contract body ...
}
```

#### Adding New Invariant Categories

Adding a new invariant category requires only:

1. Subclass `InvariantPattern` in `patterns.py`
2. Implement `match(source_code) -> list[str]`
3. Register the pattern in `InvariantGenerator.__init__`

The pattern engine is intentionally regex-based — an AST-based upgrade path (via Slither's IR) is planned for future iterations.

#### Metadata Tracking

Generated invariant names are propagated through the pipeline as `invariant_metadata` in the `AnalyzerResult.raw_output`. The normaliser uses this to tag auto-generated property failures with `auto-invariant` in findings metadata, distinguishing them from user-written properties.

### Execution Model

- Slither and Mythril run via isolated Python virtual environments (`venv-slither/`, `venv-mythril/`)
- Echidna runs via Docker container with full network and filesystem isolation
- The heuristic analyzer runs in-process (no external dependencies)
- The orchestrator executes analyzers **sequentially** (Slither → Mythril → Echidna → Heuristic)
- Each analyzer is executed with:
  - Strict timeout enforcement (Slither: 120s, Mythril: 60s default, Echidna: 120s default)
  - Isolated runtime environment (no shared dependencies with Django)
  - Independent failure handling — a failure in one analyzer does not terminate the pipeline
- **Graceful degradation:** Slither is required (failure = scan fails); Mythril, Echidna, and Heuristic failures are logged as warnings and the scan continues with partial results
- Progress is tracked at each stage: 10% → 40% → 60% → 80% → 100%

### Risk Scoring Engine

The `RiskScorer` (`scanner/services/risk_scorer.py`) computes a deterministic, explainable, tool-agnostic aggregate risk score from normalised findings.

**Per-finding score:**

$$\text{Score}_i = W_{\text{severity}} \times W_{\text{tool}} \times \frac{\text{confidence}}{100}$$

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
