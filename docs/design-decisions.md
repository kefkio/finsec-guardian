# Design Decisions

**Status:** Current  
**Last Updated:** April 2026  
**Audience:** Architects, Researchers

---

## Table of Contents

1. [Multi-Engine Pipeline](#multi-engine-pipeline)
2. [Etherscan as a Separate Layer](#etherscan-as-a-separate-layer)
3. [Exponential Saturation Risk Model](#exponential-saturation-risk-model)
4. [Finding Normalisation Strategy](#finding-normalisation-strategy)
5. [Echidna Docker Isolation](#echidna-docker-isolation)
6. [Lazy-Load Etherscan Components](#lazy-load-etherscan-components)
7. [Graceful Degradation Per Engine](#graceful-degradation-per-engine)
8. [JWT Over Session Authentication](#jwt-over-session-authentication)
9. [SHA-256 Hash Chain for Records](#sha-256-hash-chain-for-records)
10. [Frontend State Strategy](#frontend-state-strategy)

---

## Multi-Engine Pipeline

**Decision:** Integrate four heterogeneous analysis engines (Slither, Mythril, Echidna, Heuristic) into a single orchestrated pipeline rather than running them independently.

**Rationale:**
- Each engine has complementary strengths: Slither (fast pattern detection), Mythril (deep path exploration), Echidna (property-based fuzzing), Heuristic (custom rules)
- A single pipeline enables cross-engine finding deduplication, unified risk scoring, and consistent output format
- Users get a single risk score rather than four conflicting reports

**Trade-offs:**
- Increased latency (sequential dependency on slowest engine)
- Higher infrastructure complexity
- Need for robust per-engine error isolation

**Mitigation:** Each engine wraps in try/catch with `available` flags; the pipeline always completes even if individual engines fail.

---

## Etherscan as a Separate Layer

**Decision:** The Etherscan on-chain intelligence service is implemented as an independent Layer 5 (`scanner/services/etherscan/`), not mixed into the static/symbolic/fuzz analyzers.

**Rationale:**
- On-chain data is fundamentally different from source-code analysis — it's runtime behavioral data, not vulnerability detection
- Separation of concerns: analyzers detect code-level issues; Etherscan provides operational context
- The Etherscan layer has its own data pipeline: Client → Fetcher → Analyzer → ReputationScorer
- It can be disabled independently (no `ETHERSCAN_API_KEY` → layer skipped)
- Rate limiting and API-key management are confined to the service boundary

**Architecture:**
```
scanner/services/etherscan/
├── __init__.py
├── client.py      # API wrapper, rate limiting, error handling
├── fetcher.py     # ContractData aggregator (graceful degradation)
├── analyzer.py    # OnChainInsights derivation (behavioral analysis)
└── reputation.py  # ReputationScorer (0–100 score, risk adjustment)
```

**Integration points:**
1. Orchestrator calls `_run_etherscan_layer()` after all analyzers complete
2. Normalizer enriches existing findings with on-chain context
3. RiskScorer receives `onchain_data` for reputation adjustment
4. Frontend renders `OnChainIntelligence` panel when data is present

---

## Exponential Saturation Risk Model

**Decision:** Use exponential saturation $R = 100 \times (1 - e^{-kS})$ with $k = 0.08$ instead of linear summation.

**Rationale:**
- Linear summation produces unbounded scores — 100 low-severity findings could score higher than 1 critical
- Exponential saturation naturally caps at 100 and gives diminishing returns for redundant findings
- The scaling factor $k = 0.08$ was empirically tuned so that:
  - 1 critical finding ≈ 55 risk score
  - 3 critical findings ≈ 90 risk score
  - 10 low findings ≈ 15 risk score

**Additional mechanisms:**
- **Critical floor:** Any `critical` severity finding forces minimum score of 80
- **Diversity bonus:** Unique finding titles add 0.5 each (capped at 5.0) to penalise broad vulnerability surfaces
- **On-chain adjustment:** Reputation score shifts risk ±15 max, with suspicious pattern penalty up to +10

---

## Finding Normalisation Strategy

**Decision:** All analyzer outputs are transformed into a single canonical finding shape via `FindingNormalizer`.

**Rationale:**
- Each tool has radically different output formats (Slither detectors, Mythril issues, Echidna test results)
- The frontend and risk scorer must not know which tool produced a finding
- Normalisation enables cross-tool deduplication and unified severity comparison

**Canonical shape:**
```
{ swc_id, title, severity, description, recommendation, confidence,
  line_number, line_start, line_end, column, code_snippet,
  tags, reference_url, metadata }
```

**Tool-specific mappings:** `_SLITHER_SEVERITY`, `_MYTHRIL_SEVERITY`, `_SWC_LABELS`, `_SLITHER_RECOMMENDATIONS`, `_MYTHRIL_REMEDIATION` — all defined as module-level constants in `normalizer.py`.

---

## Echidna Docker Isolation

**Decision:** Run Echidna in a Docker container with strict security constraints rather than as a native subprocess.

**Rationale:**
- Echidna fuzzes contract code and may trigger unexpected behaviour
- Docker provides process isolation, network isolation, and memory limits
- Prevents fuzzing from affecting the host system

**Docker flags:**
| Flag | Purpose |
|------|---------|
| `--network none` | No network access from fuzzer |
| `--read-only` | Immutable container filesystem |
| `--memory 1g` | Hard memory cap |
| `--tmpfs /tmp:rw,noexec,nosuid,size=256m` | Writable scratch space |
| Timeout: 120 s | Maximum execution time |

**Alternatives considered:**
- Native Echidna binary: lower latency but no isolation
- Firecracker microVM: better isolation but excessive complexity
- gVisor sandbox: good compromise but less mature for this use case

---

## Lazy-Load Etherscan Components

**Decision:** The Etherscan service modules are imported lazily (`_get_etherscan_components()`) rather than at module-load time.

**Rationale:**
- If `ETHERSCAN_API_KEY` is not set, importing the modules is wasted work
- Lazy loading means the main orchestrator module doesn't fail to import if Etherscan dependencies are missing
- The try/except in `_get_etherscan_components()` catches `EtherscanError` from the client constructor

```python
def _get_etherscan_components(self):
    api_key = getattr(settings, "ETHERSCAN_API_KEY", "")
    if not api_key:
        return None  # Skip entirely
    from .etherscan.client import EtherscanClient, EtherscanError
    from .etherscan.fetcher import EtherscanFetcher
    from .etherscan.analyzer import EtherscanAnalyzer
    from .etherscan.reputation import ReputationScorer
    try:
        client = EtherscanClient()
        return EtherscanFetcher(client), EtherscanAnalyzer(), ReputationScorer()
    except EtherscanError:
        return None
```

---

## Graceful Degradation Per Engine

**Decision:** Every analysis engine (Mythril, Echidna, Etherscan) is wrapped in individual try/except blocks; failures mark the engine as unavailable without aborting the scan.

**Rationale:**
- Mythril is resource-intensive and may timeout on complex contracts
- Echidna requires Docker and may not be available in all environments
- Etherscan depends on an external API that may be rate-limited or down
- Users should still receive results from the engines that succeed

**Implementation:** Each engine sets an `*_available` boolean and `*_error` string; the orchestrator response includes these flags so the frontend can display which engines contributed to results.

---

## JWT Over Session Authentication

**Decision:** Use JWT (access + refresh tokens) via SimpleJWT instead of Django's default session-based authentication.

**Rationale:**
- The frontend is a decoupled SPA — there's no shared cookie domain with the API
- JWT enables stateless authentication (no server-side session store)
- Refresh tokens provide seamless silent re-authentication
- The frontend stores tokens in `localStorage` for persistence across browser sessions

**Security trade-offs:**
- localStorage is vulnerable to XSS → mitigated by CSP headers and input sanitisation
- No CSRF protection needed (no cookies sent automatically)
- Token revocation requires a deny-list (not yet implemented; planned enhancement)

---

## SHA-256 Hash Chain for Records

**Decision:** `TamperRecord` entries form a cryptographic hash chain: $H_i = \text{SHA256}(H_{i-1} \| \text{content}_i)$.

**Rationale:**
- Provides tamper evidence for audit records without requiring a blockchain
- Any modification to a record breaks the chain from that point forward
- Verification is $O(n)$ and requires no external dependencies
- Supports compliance requirements for immutable audit trails

**Implementation:**
- `TamperRecordViewSet` is append-only (`http_method_names = ['get', 'post', 'head', 'options']`)
- `perform_create()` computes the hash from previous record's hash + new content
- `verify()` action walks the full chain and flags any breaks

---

## Frontend State Strategy

**Decision:** Use TanStack Query v5 for server state and React Context for UI state — no Redux or global store.

**Rationale:**
- TanStack Query handles caching, background refetching, and cache invalidation automatically
- Most application state is server-derived (scans, findings, threats, audit events)
- UI state (theme, sidebar collapse, mobile detection) is minimal and well-served by Context
- Avoids the boilerplate and complexity of Redux/Zustand for a domain where server state dominates

**Key patterns:**
- **Cascading `enabled` flags:** Dependent queries fire only when prerequisites are loaded
- **Stale time tuning:** Scan metadata (30 s), findings/statistics (60 s)
- **Lazy on-chain fetch:** On-chain data query only enabled when `scan.contract_address` exists
