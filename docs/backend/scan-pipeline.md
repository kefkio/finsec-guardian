# Backend — Scan Pipeline

**Status:** Current  
**Last Updated:** April 2026  
**Audience:** Developers, Researchers

---

## Table of Contents

1. [Overview](#overview)
2. [Entry Points](#entry-points)
3. [Source-Code Scan Flow](#source-code-scan-flow)
4. [Address-Only Scan Flow](#address-only-scan-flow)
5. [File Processing Stage](#file-processing-stage)
6. [Compilation Stage](#compilation-stage)
7. [Analysis Stage](#analysis-stage)
8. [Normalisation Stage](#normalisation-stage)
9. [Risk Scoring Stage](#risk-scoring-stage)
10. [Persistence Stage](#persistence-stage)
11. [Error Handling](#error-handling)

---

## Overview

The scan pipeline is the end-to-end lifecycle of a contract analysis: from user input to persisted results. It supports two distinct flows — **source-code scans** (full multi-engine analysis) and **address-only scans** (Etherscan on-chain intelligence only).

**Related documents:**
- [Orchestrator](orchestrator.md) — `ScanOrchestrator` class internals
- [Analyzers](analyzers.md) — individual engine details
- [Risk Scoring](risk-scoring.md) — composite score computation
- [Data Flow](../data-flow.md) — request-level data transformations

---

## Entry Points

| Endpoint | Method | Handler | Creates ScanJob? |
|----------|--------|---------|------------------|
| `POST /api/scanner/scans/` | DRF create | `ScanJobViewSet.perform_create()` | Yes |
| `POST /api/scanner/scans/trigger/` | Custom action | `ScanJobViewSet.trigger_scan()` | No |

Both endpoints accept `source_code`, `contract_name`, `contract_address`, and `uploaded_file`. The backend auto-detects whether this is a source-code or address-only scan.

---

## Source-Code Scan Flow

```
User submits source_code (+ optional contract_address)
    │
    ▼
┌─────────────────────────────────┐
│  File Processing                │
│  SolidityFileProcessingService  │
│  ├─ _normalize_source()         │  Trim, validate non-empty, size check
│  ├─ resolve_solc_version()      │  Pragma extraction or user override
│  └─ compile()                   │  Solc compilation → ABI + bytecode
└────────────┬────────────────────┘
             │ ProcessedContractSource
             ▼
┌─────────────────────────────────┐
│  ScanJob Creation               │
│  ├─ source_code_hash (SHA-256)  │
│  ├─ syntax_valid flag           │
│  ├─ compiled_abi, bytecode      │
│  ├─ status = 'pending'          │
│  └─ AuditEvent logged           │
└────────────┬────────────────────┘
             │ (if syntax_valid)
             ▼
┌─────────────────────────────────┐
│  ScanOrchestrator.run_scan_job()│
│  ├─ Slither  (required)        │  120 s timeout
│  ├─ Mythril  (optional)        │   60 s timeout
│  ├─ Echidna  (optional)        │  120 s timeout, Docker
│  ├─ Heuristic (always)         │  In-process regex
│  └─ Etherscan (if address)     │  HTTP API, 30 s
└────────────┬────────────────────┘
             │ Normalised findings[]
             ▼
┌─────────────────────────────────┐
│  FindingNormalizer              │
│  ├─ normalize(result)           │  Per-tool dispatch
│  ├─ tag_findings(tool)          │  Stamp metadata.tool
│  ├─ normalize_onchain()         │  Etherscan data → dict
│  └─ enrich_findings_with_onchain│  Annotate static findings
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  RiskScorer.compute()           │
│  ├─ Weighted per-finding scores │
│  ├─ Diversity bonus             │
│  ├─ Exponential saturation      │
│  ├─ Critical floor (80)         │
│  └─ On-chain adjustment (±15)   │
└────────────┬────────────────────┘
             │ risk_assessment dict
             ▼
┌─────────────────────────────────┐
│  ScanPersistence                │
│  ├─ persist_findings()          │  Idempotent get_or_create
│  └─ mark_complete()             │  Status, metadata, risk
└─────────────────────────────────┘
```

---

## Address-Only Scan Flow

When no source code or uploaded file is provided, the pipeline short-circuits:

```
User submits contract_address only
    │
    ▼
┌──────────────────────────────────┐
│  Address-Only Detection          │
│  (in views.py perform_create)    │
│  not source_code                 │
│  and not uploaded_file           │
│  and contract_address present    │
└────────────┬─────────────────────┘
             ▼
┌──────────────────────────────────┐
│  ScanJob Creation                │
│  source_type = 'address'         │
│  status = 'analyzing'            │
│  AuditEvent logged               │
└────────────┬─────────────────────┘
             ▼
┌──────────────────────────────────┐
│  orchestrator._run_etherscan_layer()│
│  ├─ EtherscanFetcher.fetch()     │
│  ├─ EtherscanAnalyzer.analyze()  │
│  ├─ ReputationScorer.score()     │
│  └─ normalize_onchain()          │
└────────────┬─────────────────────┘
             ▼
┌──────────────────────────────────┐
│  RiskScorer.compute([], onchain) │
│  (empty findings, on-chain only) │
└────────────┬─────────────────────┘
             ▼
┌──────────────────────────────────┐
│  ScanPersistence.mark_complete() │
│  metadata.onchain_data stored    │
│  metadata.scan_mode = 'address_only' │
└──────────────────────────────────┘
```

---

## File Processing Stage

`SolidityFileProcessingService` handles two input types:

| Method | Input | Output |
|--------|-------|--------|
| `process_source_code()` | Raw text string | `ProcessedContractSource` |
| `process_uploaded_file()` | `UploadedFile` (.sol) | `ProcessedContractSource` |

Both call `_normalize_source()` which:
- Rejects empty input with `FileProcessingError`
- Enforces 1 MB size limit
- Strips trailing whitespace, appends newline

Then `_build_processed_source()`:
- Resolves Solidity version (pragma extraction or user override)
- Compiles via `SolidityCompiler`
- Infers contract name from source
- Extracts ABI and bytecode on success
- Returns a `ProcessedContractSource` dataclass

---

## Compilation Stage

`SolidityCompiler` (in `compiler.py`) handles:

- **Version resolution:** Parses `pragma solidity ^X.Y.Z` directives, falls back to user-specified or default version
- **Compilation:** Invokes `solc` JSON-I/O, producing ABI + bytecode
- **Contract extraction:** `extract_primary_contract()` selects the most likely target contract from multi-contract outputs
- **Name inference:** `infer_contract_name()` extracts the first `contract <Name>` from source

Compilation failure sets `syntax_valid=False` and the scan job is marked `failed` immediately.

---

## Analysis Stage

Four engines run sequentially within the orchestrator:

1. **Slither** — `slither.analyze(source_code, contract_name)` returns `AnalyzerResult` with `raw_output.detectors[]`
2. **Mythril** — `mythril.analyze(source_code, contract_name, timeout)` returns `AnalyzerResult` with `raw_output.issues[]`
3. **Echidna** — `echidna.analyze(source_code, contract_name, timeout)` returns `AnalyzerResult` with `raw_output.tests[]` + `raw_output.invariant_metadata`
4. **Heuristic** — `heuristic.analyze(source_code, contract_name)` returns `AnalyzerResult` with `raw_output.findings[]`

Each engine's output passes through `FindingNormalizer.normalize()` for format unification and `tag_findings()` for tool attribution.

---

## Normalisation Stage

`FindingNormalizer` dispatches on `result.tool`:

| Tool | Raw Format | Normalised Output |
|------|-----------|-------------------|
| `slither` | `detectors[]` with impact/confidence/elements | Canonical finding dicts with SWC ID, severity, line numbers |
| `mythril` | `issues[]` with swc_id/severity/lineno | Canonical finding dicts with remediation from `_MYTHRIL_REMEDIATION` |
| `echidna` | `tests[]` with status/reproducer | Failed properties → high-severity findings; all pass → info note |
| `heuristic` | Pre-normalised `findings[]` | Passed through as-is |

**Canonical finding shape:**

```python
{
    "swc_id": str,          # SWC-107, SWC-101, etc.
    "title": str,           # Human-readable vulnerability name
    "severity": str,        # critical | high | medium | low | info
    "description": str,     # Detailed explanation
    "recommendation": str,  # Remediation guidance
    "confidence": int,      # 0–100
    "line_number": int,     # Source location
    "line_start": int,
    "line_end": int,
    "column": int,
    "code_snippet": str,
    "tags": list[str],      # e.g., ["slither", "reentrancy-eth"]
    "reference_url": str,   # SWC registry link
    "metadata": dict,       # Tool-specific context
}
```

Path sanitisation (`_sanitize_paths()`) strips `/tmp/` paths from descriptions to prevent information leakage.

---

## Risk Scoring Stage

See [Risk Scoring](risk-scoring.md) for the full algorithm. Summary:

- Per-finding: `W_severity × W_tool × (confidence / 100)`
- Diversity bonus for unique issue types
- Exponential saturation: `Risk = 100 × (1 − e^(-0.08 × S))`
- Critical floor: any critical finding → minimum score 80
- On-chain adjustment: reputation `risk_adjustment` clamped to ±15

---

## Persistence Stage

`ScanPersistence` manages the database lifecycle:

| Method | Purpose |
|--------|---------|
| `mark_analyzing(job)` | Set status → `analyzing`, record start time |
| `update_progress(job, pct)` | Update progress percentage |
| `persist_findings(job, findings)` | Idempotent `get_or_create` for each finding + category |
| `mark_complete(job, metadata, risk)` | Set status → `complete`, merge metadata, store risk |
| `mark_failed(job, error)` | Set status → `failed`, store error in metadata |

Finding persistence uses `get_or_create` keyed on `(scan, swc_id, line_number, title)` to ensure idempotency on re-runs.

---

## Error Handling

| Stage | Error Type | Behaviour |
|-------|-----------|-----------|
| File Processing | `FileProcessingError` | 400 response, no job created |
| Compilation | Syntax error | Job created with `status='failed'`, `syntax_valid=False` |
| Slither | `SlitherError` | Job marked `failed`, scan aborts |
| Mythril | `MythrilError` / generic | Logged, `mythril_available=False`, scan continues |
| Echidna | `EchidnaError` / generic | Logged, `echidna_available=False`, scan continues |
| Etherscan | Any exception | Logged, `onchain_data=None`, scan continues |
| Persistence | DB error | Propagates (500 response) |