# Backend — Analysis Engines

**Status:** Current  
**Last Updated:** April 2026  
**Audience:** Developers, Researchers

---

## Table of Contents

1. [Overview](#overview)
2. [Analyzer Abstraction](#analyzer-abstraction)
3. [Slither (Static Analysis)](#slither-static-analysis)
4. [Mythril (Symbolic Execution)](#mythril-symbolic-execution)
5. [Echidna (Property-Based Fuzzing)](#echidna-property-based-fuzzing)
6. [Heuristic (Regex-Based Rules)](#heuristic-regex-based-rules)
7. [Etherscan (On-Chain Intelligence)](#etherscan-on-chain-intelligence)
8. [Engine Comparison](#engine-comparison)
9. [Error Handling](#error-handling)

---

## Overview

FinSec Guardian integrates **five** analysis methodologies, each targeting a different class of vulnerabilities. The first four operate on source code; the fifth (Etherscan) operates on live blockchain data.

**Related documents:**
- [Orchestrator](orchestrator.md) — pipeline coordination
- [Scan Pipeline](scan-pipeline.md) — end-to-end lifecycle
- [Risk Scoring](risk-scoring.md) — how engine outputs feed into risk

---

## Analyzer Abstraction

All source-code analyzers implement the `AnalyzerResult` dataclass contract:

```python
@dataclass
class AnalyzerResult:
    tool: str         # "slither" | "mythril" | "echidna" | "heuristic"
    success: bool
    raw_output: dict  # Tool-specific JSON output
    error: str = ""
    stderr: str = ""
```

The `FindingNormalizer` consumes `AnalyzerResult` instances and produces canonical finding dicts, dispatching normalisation based on `result.tool`.

---

## Slither (Static Analysis)

**Module:** `scanner/services/analyzers/slither.py`

### Approach
- Runs Slither as a Python subprocess with `--json` output
- Analyzes Solidity AST for 80+ vulnerability detection patterns
- Fastest engine (typically < 5 s)

### Input/Output

| | Description |
|------|-------------|
| **Input** | Source code written to temp file, contract name |
| **Output** | `AnalyzerResult(tool="slither", raw_output={"detectors": [...]})` |
| **Timeout** | 120 s (configurable via `SLITHER_TIMEOUT`) |

### Detector Categories

| Category | Example Detectors | Typical Severity |
|----------|------------------|-----------------|
| Reentrancy | `reentrancy-eth`, `reentrancy-no-eth` | High |
| Access Control | `arbitrary-send-eth`, `suicidal`, `unprotected-upgrade` | High–Critical |
| Deprecated | `solc-version`, `deprecated-standards` | Info |
| Low-Level | `low-level-calls`, `unchecked-lowlevel` | Medium |
| Gas Optimization | `constable-states`, `external-function` | Info |

### Normalisation

Slither detectors are mapped via `_SLITHER_SEVERITY`:
- `High` → `high`
- `Medium` → `medium`
- `Low` → `low`
- `Informational` / `Optimization` → `info`

Confidence mapping via `_SLITHER_CONFIDENCE`:
- `High` → 90, `Medium` → 65, `Low` → 40

Line numbers extracted from `elements[].source_mapping.lines`.

---

## Mythril (Symbolic Execution)

**Module:** `scanner/services/analyzers/mythril.py`

### Approach
- Compiles contract to EVM bytecode
- Performs symbolic execution to explore all feasible code paths
- Detects vulnerabilities requiring specific execution sequences

### Input/Output

| | Description |
|------|-------------|
| **Input** | Source code, contract name, timeout |
| **Output** | `AnalyzerResult(tool="mythril", raw_output={"issues": [...]})` |
| **Timeout** | 60 s (configurable via `MYTHRIL_TIMEOUT`) |

### Issue Types

| SWC ID | Name | Severity |
|--------|------|----------|
| SWC-101 | Integer Overflow and Underflow | High |
| SWC-104 | Unchecked Call Return Value | Medium |
| SWC-105 | Unprotected Ether Withdrawal | High |
| SWC-106 | Unprotected SELFDESTRUCT | Critical |
| SWC-107 | Reentrancy | High |
| SWC-112 | Delegatecall to Untrusted Callee | High |
| SWC-114 | Transaction Order Dependence | Medium |
| SWC-115 | Authorization through tx.origin | Medium |

### Normalisation

Mythril issues mapped via `_MYTHRIL_SEVERITY`:
- `High` → `high`, `Medium` → `medium`, `Low` → `low`, `Informational` → `info`

SWC IDs enriched with human-readable labels from `_SWC_LABELS` (36 entries).

Remediation from `_MYTHRIL_REMEDIATION` (7 SWC-specific recommendations).

---

## Echidna (Property-Based Fuzzing)

**Module:** `scanner/services/analyzers/echidna.py`

### Approach
- Runs inside Docker container for security isolation
- Fuzzes contract with random inputs to find invariant violations
- Invariants can be auto-generated (see [Invariants](invariants.md)) or manual

### Security Hardening

| Docker Flag | Purpose |
|-------------|---------|
| `--network none` | No network access |
| `--read-only` | Immutable container filesystem |
| `--memory 1g` | Hard memory limit |
| `--tmpfs /tmp:rw,noexec,nosuid,size=256m` | Writable scratch space |
| Timeout: 120 s | Maximum execution time |

### Input/Output

| | Description |
|------|-------------|
| **Input** | Source code, contract name, timeout, Docker image |
| **Output** | `AnalyzerResult(tool="echidna", raw_output={"tests": [...], "raw_text": "...", "invariant_metadata": {...}})` |
| **Timeout** | 120 s (configurable via `ECHIDNA_TIMEOUT`) |

### Normalisation

- Failed property → `high` severity finding (confidence 95)
- Includes counterexample and call sequence in metadata
- Auto-generated invariants tagged with `auto-invariant` in metadata
- Passing properties → `info` note

### Tool Weight

Echidna findings receive a **1.5× exploit boost** in the risk scorer because a failed property represents a concrete exploit path, not just a potential vulnerability.

---

## Heuristic (Regex-Based Rules)

**Module:** `scanner/services/analyzers/heuristic.py`

### Approach
- In-process regex pattern matching on raw source code
- No subprocess or Docker overhead
- Catches logic flaws that formal tools may miss
- Always runs (no optional dependency)

### Input/Output

| | Description |
|------|-------------|
| **Input** | Source code, contract name |
| **Output** | `AnalyzerResult(tool="heuristic", raw_output={"findings": [...]})` |
| **Timeout** | N/A (< 1 s) |

### Rule Examples

| Rule | Pattern | Severity |
|------|---------|----------|
| Unchecked arithmetic | Arithmetic without require/assert guard | Medium |
| Dangerous delegatecall | `.delegatecall()` to untrusted address | Critical |
| Uninitialized state | Variable declared without initialisation | High |
| tx.origin auth | `tx.origin` used in require/if | Medium |

### Normalisation

Heuristic findings are pre-normalised — the analyzer outputs findings already in the canonical dict format. The normalizer performs passthrough.

---

## Etherscan (On-Chain Intelligence)

**Module:** `scanner/services/etherscan/` (client, fetcher, analyzer, reputation)

This is a **separate layer** (not mixed with the source-code analyzers). See [Design Decisions](../design-decisions.md) for rationale.

### Architecture

```
EtherscanClient → EtherscanFetcher → EtherscanAnalyzer → ReputationScorer
   (API calls)    (ContractData)      (OnChainInsights)   (ReputationResult)
```

### EtherscanClient

Low-level REST API wrapper.

| Method | Etherscan Endpoint | Returns |
|--------|-------------------|---------|
| `get_source_code(addr)` | `getsourcecode` | Verified source, ABI, compiler version |
| `get_abi(addr)` | `getabi` | Contract ABI |
| `get_transactions(addr)` | `txlist` | Normal transactions |
| `get_token_transfers(addr)` | `tokentx` | ERC-20 token transfers |
| `get_logs(addr)` | `getLogs` | Event logs |

**Rate limiting:** 0.22 s between requests (enforced by `_rate_limit()`).

**Address validation:** `^0x[0-9a-fA-F]{40}$` regex check before any API call.

### EtherscanFetcher

Aggregates all API calls into a single `ContractData` dataclass. Each API call is wrapped in try/except — failures append to `ContractData.warnings` without aborting.

### EtherscanAnalyzer

Derives `OnChainInsights` from `ContractData`:

| Insight | Computation |
|---------|-------------|
| `tx_count` | Total normal transactions |
| `unique_callers` | Distinct `from` addresses |
| `unique_receivers` | Distinct `to` addresses |
| `failure_rate` | `failed_tx_count / tx_count` |
| `total_value_eth` | Sum of all transaction values (Wei → ETH) |
| `high_value_flows` | Transactions ≥ 10 ETH |
| `repeated_callers` | Addresses with ≥ 10 calls |
| `top_methods` | Most-called function signatures |
| `contract_age_days` | Days since first transaction |
| `suspicious_patterns` | See [Suspicious Pattern Detection](#suspicious-pattern-detection) |

#### Suspicious Pattern Detection

| Pattern | Condition |
|---------|-----------|
| High failure rate | > 30% failed transactions |
| Repeated callers | ≥ 50 calls from a single address |
| Abnormal withdrawals | > 20 withdraw-type function calls |
| Large outflows | ≥ 100 ETH total value |
| High exposure | > 500 unique callers |

### ReputationScorer

Computes a reputation score from 0–100 using 7 weighted factors:

| Factor | Weight | Scoring | Best | Worst |
|--------|--------|---------|------|-------|
| Contract age | 15% | ≥365d→100 ... <7d→5 | 15.0 | 0.75 |
| Transaction volume | 10% | ≥10k→100 ... <10→20 | 10.0 | 2.0 |
| Failure rate | 20% | ≤1%→100 ... >40%→0 | 20.0 | 0.0 |
| Suspicious patterns | 25% | 0→100 ... ≥5→0 | 25.0 | 0.0 |
| High-value exposure | 15% | ≤1%→100 ... >30%→10 | 15.0 | 1.5 |
| Caller diversity | 10% | ≥1k→100 ... <5→20 | 10.0 | 2.0 |
| Verification | 5% | Verified→100, Not→0 | 5.0 | 0.0 |

**Verdicts:** HIGH REPUTATION (≥80), MODERATE (≥60), LOW (≥40), POOR (≥20), VERY POOR (<20)

**Risk adjustment:** `(50 − reputation_score) × 0.30`

This value is clamped to ±15 and applied to the risk score. High-reputation contracts reduce risk; low-reputation contracts increase it.

---

## Engine Comparison

| Dimension | Slither | Mythril | Echidna | Heuristic | Etherscan |
|-----------|---------|---------|---------|-----------|-----------|
| **Analysis type** | Static AST | Symbolic EVM | Fuzz testing | Regex rules | On-chain behavioral |
| **Execution model** | Subprocess | Subprocess | Docker container | In-process | HTTP API |
| **Typical latency** | < 5 s | 5–60 s | 10–120 s | < 1 s | 2–30 s |
| **Isolation** | Process | Process | Network+memory+fs | None needed | N/A |
| **Timeout** | 120 s | 60 s | 120 s | None | 30 s per request |
| **Optional** | No (core) | Yes | Yes | No (core) | Yes |
| **Tool weight** | 0.9 | 1.0 | 1.2 (×1.5 boost) | 0.85 | N/A (reputation) |
| **Output format** | JSON detectors | JSON issues | JSON tests | Pre-normalised findings | OnChainInsights + ReputationResult |
| **Key strength** | Speed, breadth | Depth, path coverage | Concrete exploits | Custom rules | Operational context |

---

## Error Handling

Each engine is wrapped in individual try/except blocks in the orchestrator:

```python
# Mythril (example)
mythril_findings, mythril_available, mythril_error = [], True, None
try:
    mythril_result = self.mythril.analyze(...)
    mythril_findings = self.normalizer.normalize(mythril_result)
    self.normalizer.tag_findings(mythril_findings, "mythril")
except MythrilError as exc:
    mythril_available, mythril_error = False, str(exc)
except Exception as exc:
    mythril_error = str(exc)
```

**Principle:** A single engine failure never aborts the scan. The response includes `*_available` flags so the frontend displays which engines contributed to results.
