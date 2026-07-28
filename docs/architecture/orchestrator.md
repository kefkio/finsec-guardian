# Backend — Orchestrator

**Status:** Current  
**Last Updated:** April 2026  
**Audience:** Developers, Researchers

---

## Table of Contents

1. [Overview](#overview)
2. [Class Design](#class-design)
3. [Pipeline Stages](#pipeline-stages)
4. [Ad-Hoc Scan (`run_scan`)](#ad-hoc-scan-run_scan)
5. [Job-Based Scan (`run_scan_job`)](#job-based-scan-run_scan_job)
6. [Address-Only Scan](#address-only-scan)
7. [Etherscan Layer Integration](#etherscan-layer-integration)
8. [On-Chain Enrichment](#on-chain-enrichment)
9. [Graceful Degradation](#graceful-degradation)
10. [Configuration](#configuration)

---

## Overview

The `ScanOrchestrator` is the **single entry-point** for running a complete analysis pipeline. It coordinates five analysis engines (Slither, Mythril, Echidna, Heuristic, Etherscan), normalises their output into a unified schema, computes a composite risk score, and persists the results.

**Related documents:**
- [Analyzers](analyzers.md) — individual engine details
- [Scan Pipeline](scan-pipeline.md) — end-to-end lifecycle walk-through
- [Risk Scoring](risk-scoring.md) — how the composite score is calculated
- [Data Model](data-model.md) — ScanJob and Finding persistence

**Source:** `scanner/services/orchestrator.py`

---

## Class Design

```python
class ScanOrchestrator:
    def __init__(self):
        self.slither    = SlitherAnalyzer()
        self.mythril    = MythrilAnalyzer()
        self.echidna    = EchidnaAnalyzer()
        self.heuristic  = HeuristicAnalyzer()
        self.normalizer = FindingNormalizer()
        self.persistence = ScanPersistence()
        self.risk_scorer = RiskScorer()
```

All components are instantiated eagerly **except** the Etherscan layer, which is lazy-loaded via `_get_etherscan_components()` only when a `contract_address` is provided. This avoids importing network dependencies (and touching settings) for source-only scans.

---

## Pipeline Stages

The pipeline runs in a fixed order. Each stage maps to a numbered layer:

| Stage | Layer | Component | Timeout | Degradation |
|-------|-------|-----------|---------|-------------|
| 1 | L1 — Static Analysis | `SlitherAnalyzer` | 120 s | **Required** — failure aborts the scan |
| 2 | L2 — Symbolic Execution | `MythrilAnalyzer` | 60 s | Optional — skip on error |
| 3 | L3 — Property Fuzzing | `EchidnaAnalyzer` | 120 s | Optional — skip on error |
| 4 | L4 — Heuristic Analysis | `HeuristicAnalyzer` | < 1 s | Always runs (in-process) |
| 5 | L5 — On-Chain Intelligence | `EtherscanFetcher → Analyzer → Reputation` | 30 s | Optional — skip if no address or API key |
| 6 | L6 — Normalisation | `FindingNormalizer` | < 100 ms | Always runs |
| 7 | L7 — Risk Scoring | `RiskScorer` | < 10 ms | Always runs |
| 8 | L8 — Persistence | `ScanPersistence` | < 50 ms | Always runs (job-based only) |

---

## Ad-Hoc Scan (`run_scan`)

Used by the `trigger_scan` API endpoint (`POST /api/scanner/scans/trigger/`). Returns results directly without creating a database record.

```python
def run_scan(
    self,
    source_code: str,
    contract_name: str | None = None,
    mythril_timeout: int = 60,
    echidna_timeout: int | None = None,
    contract_address: str | None = None,
) -> dict
```

**Return shape:**

```python
{
    "success": bool,
    "findings": list[dict],         # Merged, normalised findings
    "slither_findings": list,       # Per-engine breakdown
    "mythril_findings": list,
    "echidna_findings": list,
    "heuristic_findings": list,
    "mythril_available": bool,
    "echidna_available": bool,
    "etherscan_available": bool,
    "raw_output": dict,
    "error": str | None,
    "stderr": str,
    "risk_assessment": dict,
    "onchain_data": dict | None,
}
```

---

## Job-Based Scan (`run_scan_job`)

Used for persisted `ScanJob` records. Called from `slither_runner.run_slither_analysis()` after job creation.

```python
def run_scan_job(self, job_id: int) -> None
```

**Lifecycle:**

1. Load `ScanJob` from database
2. Mark status → `analyzing` (progress 10%)
3. Run Slither → normalise → tag → progress 40%
4. Run Mythril (optional) → normalise → tag → progress 60%
5. Run Echidna (optional) → normalise → tag
6. Run Heuristic → normalise → tag → progress 75%
7. Run Etherscan layer (optional, when `contract_address` set) → progress 85%
8. Enrich static findings with on-chain context
9. Persist all findings via `ScanPersistence.persist_findings()`
10. Compute risk score via `RiskScorer.compute()`
11. Mark status → `complete` (progress 100%) with metadata + risk_assessment

---

## Address-Only Scan

When the user provides only a contract address (no source code), the pipeline bypasses all source-code analysis and runs only the Etherscan layer. This is handled in `views.py` (not the orchestrator itself):

1. `perform_create` detects `not source_code and not uploaded_file and contract_address`
2. Creates a `ScanJob` with `source_type='address'`, `status='analyzing'`
3. Calls `orchestrator._run_etherscan_layer(contract_address)` directly
4. Marks complete with on-chain data and risk assessment

The `trigger_scan` endpoint similarly detects address-only requests and returns on-chain data without persisting.

---

## Etherscan Layer Integration

The Etherscan layer is **lazy-loaded** — components are only imported when needed:

```python
def _get_etherscan_components(self):
    api_key = getattr(settings, "ETHERSCAN_API_KEY", "")
    if not api_key:
        return None
    # Imports happen here, not at module level
    client = EtherscanClient()
    return EtherscanFetcher(client), EtherscanAnalyzer(), ReputationScorer()
```

**`_run_etherscan_layer(contract_address)`** executes the full Etherscan pipeline:

```
EtherscanFetcher.fetch(address)
    → ContractData (source, ABI, transactions, token transfers, events)
EtherscanAnalyzer.analyze(contract_data)
    → OnChainInsights (tx stats, patterns, value flows, caller graph)
ReputationScorer.score(insights)
    → ReputationResult (score 0–100, verdict, risk_adjustment ±15)
FindingNormalizer.normalize_onchain(insights, reputation)
    → onchain_data dict (unified payload)
```

Returns `None` if any step fails — the scan continues without on-chain data.

---

## On-Chain Enrichment

When on-chain data is available alongside static findings, the normalizer enriches relevant findings:

- **Reentrancy findings** get annotated with withdraw pattern data (if abnormal withdrawals detected on-chain)
- **Access control findings** get annotated with repeated caller data (if automated/bot patterns detected)

This enrichment is performed by `FindingNormalizer.enrich_findings_with_onchain()` using a reconstructed `OnChainInsights` object from the normalised data.

---

## Graceful Degradation

| Component | Failure Behaviour |
|-----------|-------------------|
| **Slither** | Scan aborts — Slither is the primary engine (`SlitherError` propagates) |
| **Mythril** | `MythrilError` caught → `mythril_available=False`, scan continues |
| **Echidna** | `EchidnaError` caught → `echidna_available=False`, scan continues |
| **Etherscan** | Any exception caught → `onchain_data=None`, scan continues |
| **Heuristic** | Always succeeds (in-process, no external dependencies) |

Metadata stored on completion includes per-engine availability flags and error messages, enabling the frontend to display which engines contributed.

---

## Configuration

| Setting | Default | Purpose |
|---------|---------|---------|
| `MYTHRIL_TIMEOUT` | 60 s | Max seconds for Mythril subprocess |
| `ECHIDNA_TIMEOUT` | 120 s | Max seconds for Echidna Docker execution |
| `ETHERSCAN_API_KEY` | `""` | Etherscan API key (empty disables the layer) |
| `ETHERSCAN_BASE_URL` | mainnet | Override for testnets/alt chains |
| `ETHERSCAN_TIMEOUT` | 30 s | HTTP timeout per Etherscan request |