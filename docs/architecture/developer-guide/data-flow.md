# Data Flow & Pipeline Orchestration

**Status:** Current  
**Last Updated:** April 2026  
**Audience:** Developers, Architects

---

## Table of Contents

1. [Overview](#overview)
2. [Request Lifecycle](#request-lifecycle)
3. [Scan Pipeline Data Flow](#scan-pipeline-data-flow)
4. [Analyzer Data Contracts](#analyzer-data-contracts)
5. [Normalisation Flow](#normalisation-flow)
6. [On-Chain Intelligence Flow](#on-chain-intelligence-flow)
7. [Risk Scoring Flow](#risk-scoring-flow)
8. [Persistence Flow](#persistence-flow)
9. [Frontend Data Consumption](#frontend-data-consumption)

---

## Overview

Data flows through FinSec Guardian in an **unidirectional pipeline**. Each stage transforms data into a more refined form, from raw Solidity source to scored, enriched findings.

**Related documents:**
- [System Architecture](system-architecture.md) — component model and layer definitions
- [Backend Orchestrator](backend/orchestrator.md) — pipeline coordination logic
- [Risk Scoring](backend/risk-scoring.md) — score computation details

---

## Request Lifecycle

### Scan Creation (POST `/api/scanner/scans/`)

```
Frontend (ScanJobSerializer)
    │
    ↓ JSON: { source_code, contract_name?, contract_address?, uploaded_file? }
    │
    ↓ [DRF Validation]
    │  - source_code XOR uploaded_file required
    │  - contract_address: max 42 chars, optional
    │
    ↓ [perform_create()]
    │  1. SolidityFileProcessingService.process() → extracts source, contract name
    │  2. SolidityCompiler.resolve_solc_version() → detect pragma
    │  3. SolidityCompiler.compile() → ABI + bytecode
    │  4. ScanJob.save() → SHA-256 hash of source, status='pending'
    │  5. AuditEvent.create(event_type='SCAN_CREATED')
    │  6. ScanOrchestrator.run_scan_job(job.id) → full pipeline
    │
    ↓ [Response]
    │  201 Created: ScanJobSerializer(job)
```

### Trigger Scan (POST `/api/scanner/scans/trigger/`)

```
Frontend
    │
    ↓ JSON: { source_code, contract_name?, contract_address? }
    │
    ↓ [trigger_scan view]
    │  1. ScanOrchestrator.run_scan() → synchronous pipeline
    │  2. Returns dict: { findings, risk_assessment, onchain_data, ... }
    │
    ↓ [Response]
    │  200 OK: { success, findings[], risk_assessment{}, onchain_data{} }
```

---

## Scan Pipeline Data Flow

End-to-end transformation from source code to persisted results:

```
Source Code (str)
    │
    ├─→ [SlitherAnalyzer.analyze()]
    │   Input:  source_code, contract_name
    │   Output: AnalyzerResult { tool="slither", raw_output={detectors: [...]} }
    │   ↓ normalize() → [finding_dict, ...]
    │   ↓ tag_findings("slither")
    │
    ├─→ [MythrilAnalyzer.analyze()]
    │   Input:  source_code, contract_name, timeout=60
    │   Output: AnalyzerResult { tool="mythril", raw_output={issues: [...]} }
    │   ↓ normalize() → [finding_dict, ...]
    │   ↓ tag_findings("mythril")
    │   ⚠ Optional: MythrilError → mythril_available=False
    │
    ├─→ [EchidnaAnalyzer.analyze()]
    │   Input:  source_code, contract_name, timeout=120
    │   Output: AnalyzerResult { tool="echidna", raw_output={tests: [...]} }
    │   ↓ normalize() → [finding_dict, ...]
    │   ↓ tag_findings("echidna")
    │   ⚠ Optional: EchidnaError → echidna_available=False
    │
    └─→ [HeuristicAnalyzer.analyze()]
        Input:  source_code, contract_name
        Output: AnalyzerResult { tool="heuristic", raw_output={findings: [...]} }
        ↓ normalize() → [finding_dict, ...]
        ↓ tag_findings("heuristic")

    ↓ [Merge all_findings]
    │  all_findings = slither + mythril + echidna + heuristic

    ↓ [Etherscan Layer] (if contract_address matches ^0x[0-9a-fA-F]{40}$)
    │  See "On-Chain Intelligence Flow" below

    ↓ [RiskScorer.compute(all_findings, onchain_data)]
    │  Output: { risk_score: 0–100, verdict, breakdown, tool_contributions }

    ↓ [Persistence]
    │  persist_findings(job, all_findings) → Finding records
    │  mark_complete(job, metadata, risk_assessment)
```

---

## Analyzer Data Contracts

### AnalyzerResult Dataclass

```python
@dataclass
class AnalyzerResult:
    tool: str           # "slither" | "mythril" | "echidna" | "heuristic"
    success: bool
    raw_output: dict    # Tool-specific JSON
    error: str = ""
    stderr: str = ""
```

### Normalised Finding Dict

Every finding from every tool is normalized to this canonical shape:

```python
{
    "swc_id": "SWC-107",                    # SWC registry ID (blank for heuristic)
    "title": "Reentrancy in withdraw()",     # Human-readable title
    "severity": "high",                      # critical | high | medium | low | info
    "description": "...",                    # Detailed explanation
    "recommendation": "...",                 # Remediation guidance
    "confidence": 90,                        # 0–100
    "line_number": 42,                       # Primary source line
    "line_start": 40,                        # Range start (optional)
    "line_end": 48,                          # Range end (optional)
    "column": 8,                             # Column offset (optional)
    "code_snippet": "function withdraw()...",# Relevant source
    "tags": ["slither", "reentrancy"],       # Tool + category tags
    "reference_url": "https://swcregistry.io/docs/SWC-107",
    "metadata": {
        "tool": "slither",                   # Source analyzer
        "check": "reentrancy-eth",           # Tool-specific detector name
        "onchain_note": "..."                # Added by enrich_findings_with_onchain
    }
}
```

---

## Normalisation Flow

```
AnalyzerResult
    │
    ↓ FindingNormalizer.normalize(result)
    │  Dispatches by result.tool:
    │    "slither"   → normalize_slither(detectors)
    │    "mythril"   → normalize_mythril(issues)
    │    "echidna"   → normalize_echidna(tests, raw_text, invariant_metadata)
    │    "heuristic" → passthrough → result.raw_output["findings"]
    │
    ↓ FindingNormalizer.tag_findings(findings, tool)
    │  Stamps: metadata["tool"] = tool, tags += [tool]
    │
    ↓ [Optional] FindingNormalizer.enrich_findings_with_onchain(findings, insights)
    │  For reentrancy findings: append withdraw pattern notes
    │  For access-control findings: append repeated caller notes
    │  Tag: "onchain-enriched"
```

### Tool-Specific Normalisation

| Tool | Input Format | Key Mappings |
|------|-------------|-------------|
| **Slither** | `detectors[]` with `impact`, `confidence`, `elements[].source_mapping` | Impact → severity via `_SLITHER_SEVERITY` map; `High→high`, `Medium→medium`, etc. |
| **Mythril** | `issues[]` with `severity`, `swcID`, `address`, `description` | Severity → `_MYTHRIL_SEVERITY` map; SWC ID → `_SWC_LABELS` for title enrichment |
| **Echidna** | `tests[]` with `name`, `result` (bool), counterexamples | Failed assertions → `high` severity, confidence 95; includes reproducer sequences |
| **Heuristic** | Pre-normalised `findings[]` | Direct passthrough (already in canonical format) |

---

## On-Chain Intelligence Flow

Activated when `contract_address` is a valid Ethereum address (`^0x[0-9a-fA-F]{40}$`) and `ETHERSCAN_API_KEY` is configured.

```
contract_address (str)
    │
    ↓ [EtherscanClient]
    │  HTTP GET → Etherscan REST API
    │  Rate-limited: 0.22s between requests
    │  5 API calls: get_source_code, get_abi, get_transactions, get_token_transfers, get_logs
    │
    ↓ [EtherscanFetcher.fetch()]
    │  Output: ContractData {
    │    address, contract_name, source_code, abi,
    │    compiler_version, is_verified,
    │    transactions[], token_transfers[], event_logs[],
    │    warnings[]
    │  }
    │  Each API call degrades gracefully → warnings[]
    │
    ↓ [EtherscanAnalyzer.analyze()]
    │  Derives: OnChainInsights {
    │    tx_count, unique_callers, unique_receivers,
    │    failed_tx_count, failure_rate,
    │    total_value_eth, high_value_tx_count,
    │    high_value_flows[], repeated_callers{},
    │    suspicious_patterns[], top_methods[],
    │    token_transfer_count, unique_tokens,
    │    event_log_count, contract_age_days,
    │    first_tx_timestamp, last_tx_timestamp
    │  }
    │
    ↓ [ReputationScorer.score()]
    │  Input: OnChainInsights
    │  Output: ReputationResult {
    │    reputation_score: 0–100,
    │    verdict: "HIGH REPUTATION" | ... | "VERY POOR REPUTATION",
    │    factors: { contract_age: 80, tx_volume: 60, ... },
    │    risk_adjustment: float (±15 max)
    │  }
    │
    ↓ [FindingNormalizer.normalize_onchain()]
    │  Merges insights + reputation into unified onchain_data dict
    │
    ↓ [FindingNormalizer.enrich_findings_with_onchain()]
    │  Annotates reentrancy/access-control findings with on-chain context
    │
    ↓ [RiskScorer.compute(..., onchain_data)]
    │  Applies reputation risk_adjustment (±15) and suspicious pattern penalty (up to +10)
```

### Suspicious Pattern Detection

| Pattern | Condition | Impact on Reputation |
|---------|-----------|---------------------|
| High failure rate | > 30% failed txs | Score factor = 0 (weight 20%) |
| Repeated callers | ≥ 50 calls from single address | Flagged as potential bot/exploit |
| Abnormal withdrawals | > 20 withdraw-type calls | Suspicious outflow pattern |
| Large outflows | ≥ 100 ETH total value | High-value exposure concern |
| High exposure | > 500 unique callers | Large attack surface |

---

## Risk Scoring Flow

```
all_findings[] + onchain_data{}
    │
    ↓ [Per-finding score]
    │  score_i = SEVERITY_WEIGHT × TOOL_WEIGHT × (confidence / 100)
    │
    │  SEVERITY_WEIGHTS: critical=10, high=7, medium=4, low=2, info=1
    │  TOOL_WEIGHTS: slither=0.9, mythril=1.0, echidna=1.2, heuristic=0.85
    │  Echidna findings get 1.5× exploit boost
    │
    ↓ [Diversity bonus]
    │  unique_titles × 0.5, capped at 5.0
    │
    ↓ [Exponential saturation]
    │  risk_score = 100 × (1 − e^{−0.08 × total_score})
    │
    ↓ [Critical floor]
    │  If any finding is severity=critical: risk_score = max(risk_score, 80)
    │
    ↓ [On-chain adjustment] (if onchain_data present)
    │  reputation_adjustment = clamp(risk_adjustment, -15, +15)
    │  suspicious_penalty = min(pattern_count × 3, 10)
    │  risk_score += reputation_adjustment + suspicious_penalty
    │  risk_score = clamp(0, 100)
    │
    ↓ [Verdict classification]
    │  ≥ 85 → "CRITICAL RISK"
    │  ≥ 70 → "HIGH RISK"
    │  ≥ 50 → "MEDIUM RISK"
    │  ≥ 25 → "LOW RISK"
    │  < 25 → "MINIMAL RISK"
```

**Details:** [Risk Scoring](backend/risk-scoring.md)

---

## Persistence Flow

### ScanJob Lifecycle (run_scan_job)

```
job.status transitions:
    pending → analyzing (mark_analyzing)
                ↓
            Slither: update_progress(40%)
                ↓
            Mythril: update_progress(60%)
                ↓
            Echidna + Heuristic: update_progress(75%)
                ↓
            Etherscan: update_progress(85%)
                ↓
            persist_findings(job, all_findings)
                ↓
            mark_complete(job, metadata, risk_assessment)
                ↓
    analyzing → complete (or failed on critical error)
```

### Finding Persistence

```
all_findings[] (normalised dicts)
    │
    ↓ ScanPersistence.persist_findings(job, findings)
    │  For each finding_dict:
    │    1. Resolve FindingCategory by swc_id (get_or_create)
    │    2. Finding.objects.create(scan=job, **finding_dict)
    │  job.update_finding_counts() → updates severity counters
```

---

## Frontend Data Consumption

### TanStack Query Strategy

| Query Key | Endpoint | Stale Time | Enabled Condition |
|-----------|----------|-----------|-------------------|
| `["scans"]` | `GET /api/scanner/scans/` | 30 s | Always |
| `["scan", id]` | `GET /api/scanner/scans/{id}/` | 30 s | `!!id` |
| `["scan-findings", id]` | `GET /api/scanner/scans/{id}/findings/` | 60 s | `!!scan` |
| `["scan-statistics", id]` | `GET /api/scanner/scans/{id}/statistics/` | 60 s | `!!scan` |
| `["scan-risk", id]` | `GET /api/scanner/scans/{id}/risk/` | 60 s | `!!scan && status=complete` |
| `["scan-onchain", id]` | `GET /api/scanner/scans/{id}/` | 60 s | `!!scan && !!scan.contract_address` |

### Cascading Lazy-Fetch Pattern

```
ScanDetail page mounts
    ↓
useQuery(["scan", id])  ← fetches scan metadata first
    ↓ scan loaded
useQuery(["scan-findings", id], { enabled: !!scan })
useQuery(["scan-statistics", id], { enabled: !!scan })
useQuery(["scan-risk", id], { enabled: !!scan && scan.status === 'complete' })
useQuery(["scan-onchain", id], { enabled: !!scan && !!scan.contract_address })
```

Each query fires only after its prerequisite data is available, avoiding unnecessary network requests and providing progressive UI rendering.
