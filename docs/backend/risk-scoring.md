# Backend — Risk Scoring

**Status:** Current  
**Last Updated:** April 2026  
**Audience:** Developers, Researchers

---

## Table of Contents

1. [Overview](#overview)
2. [Design Properties](#design-properties)
3. [Scoring Formula](#scoring-formula)
4. [Severity Weights](#severity-weights)
5. [Tool Reliability Multipliers](#tool-reliability-multipliers)
6. [Diversity Bonus](#diversity-bonus)
7. [Exponential Saturation](#exponential-saturation)
8. [Critical Floor](#critical-floor)
9. [On-Chain Reputation Adjustment](#on-chain-reputation-adjustment)
10. [Verdict Classification](#verdict-classification)
11. [Output Schema](#output-schema)
12. [Examples](#examples)

---

## Overview

The `RiskScorer` converts a set of normalised findings into a single composite risk score (0–100) with an accompanying human-readable verdict. The algorithm is deterministic, tool-agnostic, and explainable — the same findings always produce the same score, regardless of engine ordering.

**Related documents:**
- [Orchestrator](orchestrator.md) — where `RiskScorer.compute()` is called
- [Scan Pipeline](scan-pipeline.md) — pipeline stage context
- [Analyzers](analyzers.md) — how findings are produced

**Source:** `scanner/services/risk_scorer.py`

---

## Design Properties

| Property | Description |
|----------|-------------|
| **Deterministic** | Same findings → same score. No randomness, no state |
| **Tool-agnostic** | Works identically for Slither, Mythril, Echidna, and Heuristic findings |
| **Explainable** | Every weight, threshold, and bonus is a named class constant |
| **Bounded** | Output is always in [0, 100] via exponential saturation |
| **Monotonic** | More findings → higher score (never decreases by adding a finding) |

---

## Scoring Formula

Each finding contributes a weighted score:

$$S_i = W_{\text{severity}} \times W_{\text{tool}} \times \frac{\text{confidence}}{100}$$

For Echidna findings (runtime-verified exploits), an additional boost is applied:

$$S_i^{\text{echidna}} = S_i \times 1.5$$

The raw aggregate is the sum of all individual scores plus a diversity bonus:

$$S_{\text{total}} = \left(\sum_{i=1}^{n} S_i\right) + D$$

The final risk score uses exponential saturation to map the unbounded aggregate to [0, 100]:

$$\text{Risk} = 100 \times \left(1 - e^{-k \cdot S_{\text{total}}}\right)$$

where $k = 0.08$ controls curve steepness.

---

## Severity Weights

Base weights on a 10-point scale:

| Severity | Weight | Rationale |
|----------|--------|-----------|
| **Critical** | 10 | Exploitable, direct fund loss |
| **High** | 7 | Exploitable with conditions |
| **Medium** | 4 | Potential issue, limited impact |
| **Low** | 2 | Best practice violation |
| **Info** | 1 | Informational, no direct risk |

---

## Tool Reliability Multipliers

Each engine's findings are weighted by the precision characteristics of the analysis methodology:

| Tool | Weight | Justification |
|------|--------|---------------|
| **Echidna** | 1.2 | Runtime-verified exploits (highest evidence quality) |
| **Mythril** | 1.0 | Symbolic execution with strong formal reasoning |
| **Slither** | 0.9 | Pattern-based static analysis (slightly lower precision) |
| **Heuristic** | 0.85 | Regex-based logic flaw detection (moderate precision) |

**Echidna exploit boost:** Echidna findings represent actual counterexamples that falsified a property. They receive an additional `1.5×` multiplier on top of the tool weight:

$$W_{\text{echidna\_total}} = 1.2 \times 1.5 = 1.8$$

---

## Diversity Bonus

More unique vulnerability types (distinct titles) indicate a wider attack surface:

$$D = \min\left(N_{\text{unique}} \times 0.5, \; 5.0\right)$$

- Each unique finding title contributes 0.5 points
- Capped at 5.0 to prevent domination by trivially diverse outputs

---

## Exponential Saturation

The raw aggregate $S_{\text{total}}$ is unbounded. The exponential saturation function maps it into [0, 100]:

$$\text{Risk} = 100 \times \left(1 - e^{-0.08 \times S}\right)$$

**Curve properties:**
- $S = 0 \Rightarrow \text{Risk} = 0$
- $S = 10 \Rightarrow \text{Risk} \approx 55$
- $S = 30 \Rightarrow \text{Risk} \approx 91$
- $S = 50 \Rightarrow \text{Risk} \approx 98$

The curve saturates quickly — a few high-severity findings push the score past 70. This prevents low-severity finding accumulation from dominating over critical issues.

---

## Critical Floor

A single critical-severity finding guarantees a minimum risk score:

$$\text{if any finding has severity} = \text{critical}: \quad \text{Risk} \geq 80$$

This ensures that no amount of confidence weighting or tool discounting can hide a critical vulnerability.

---

## On-Chain Reputation Adjustment

When Etherscan on-chain data is available, the reputation layer's `risk_adjustment` is folded into the score:

$$\text{Risk}_{\text{adjusted}} = \text{clamp}\left(\text{Risk} + \text{adjustment}, \; 0, \; 100\right)$$

- **Adjustment range:** clamped to ±15 to prevent on-chain data from dominating the score
- **Positive adjustment:** poor on-chain reputation (high failure rate, suspicious patterns) raises the score
- **Negative adjustment:** healthy on-chain activity (high tx diversity, low failure rate) reduces the score

**Suspicious pattern penalty:** Each detected suspicious pattern adds 3.0 to the score (capped at 10.0 total):

$$\text{pattern\_penalty} = \min\left(|\text{suspicious\_patterns}| \times 3.0, \; 10.0\right)$$

---

## Verdict Classification

The final numeric score maps to a human-readable verdict:

| Threshold | Verdict |
|-----------|---------|
| ≥ 85 | `CRITICAL RISK` |
| ≥ 70 | `HIGH RISK` |
| ≥ 50 | `MEDIUM RISK` |
| ≥ 25 | `LOW RISK` |
| < 25 | `MINIMAL RISK` |

The frontend maps these to letter grades: A (Minimal) → F (Critical).

---

## Output Schema

```python
{
    "risk_score": int,           # 0–100
    "verdict": str,              # "CRITICAL RISK" | "HIGH RISK" | ...
    "confidence": int,           # Average confidence across all findings
    "breakdown": {               # Severity distribution
        "critical": int,
        "high": int,
        "medium": int,
        "low": int,
        "info": int,
    },
    "tool_contributions": {      # Per-tool weighted score sums
        "slither": float,
        "mythril": float,
        "echidna": float,
        "heuristic": float,
    },
    "total_findings": int,
    "diversity_bonus": float,    # 0.0–5.0
    "onchain_adjustment": float, # Only present when on-chain data available
}
```

When no findings are present, the scorer returns:

```python
{
    "risk_score": 0,
    "verdict": "MINIMAL RISK",
    "confidence": 0,
    "breakdown": {},
    "tool_contributions": {},
    "total_findings": 0,
    "diversity_bonus": 0.0,
}
```

---

## Examples

### Example 1: Single reentrancy finding (Slither, high severity)

```
S = 7 (high) × 0.9 (slither) × 0.90 (confidence) = 5.67
D = 1 × 0.5 = 0.5
Total = 6.17
Risk = 100 × (1 − e^(-0.08 × 6.17)) = 100 × 0.39 ≈ 39
Verdict: LOW RISK
```

### Example 2: Echidna-verified reentrancy + Slither access control

```
S_echidna = 7 × 1.2 × (85/100) × 1.5 = 10.71
S_slither = 7 × 0.9 × (90/100) = 5.67
D = 2 × 0.5 = 1.0
Total = 17.38
Risk = 100 × (1 − e^(-0.08 × 17.38)) ≈ 75
Verdict: HIGH RISK
```

### Example 3: Critical finding from Mythril

```
S_mythril = 10 × 1.0 × (70/100) = 7.0
D = 1 × 0.5 = 0.5
Total = 7.5
Risk = 100 × (1 − e^(-0.08 × 7.5)) ≈ 45
Critical floor applied: Risk = max(45, 80) = 80
Verdict: HIGH RISK
```