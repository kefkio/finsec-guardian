# Backend — Invariant Generation & Injection

**Status:** Current  
**Last Updated:** April 2026  
**Audience:** Developers, Researchers

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [InvariantGenerator](#invariantgenerator)
4. [InvariantInjector](#invariantinjector)
5. [Pattern Library](#pattern-library)
6. [Adding New Patterns](#adding-new-patterns)
7. [Integration with Echidna](#integration-with-echidna)

---

## Overview

The invariant system **automatically generates** Echidna-compatible property functions from Solidity source code and **injects** them into the contract body for fuzz testing. This enables property-based fuzzing without requiring the user to write invariants manually.

The system is regex-based — an AST-based upgrade path is planned for future iterations.

**Related documents:**
- [Analyzers](analyzers.md) — Echidna engine details
- [Orchestrator](orchestrator.md) — where invariants feed into the pipeline
- [Scan Pipeline](scan-pipeline.md) — end-to-end lifecycle

**Source:** `scanner/services/invariants/` (package with `generator.py`, `injector.py`, `patterns.py`)

---

## Architecture

```
┌───────────────────────┐
│  InvariantGenerator    │
│  ├─ patterns[]         │  List of InvariantPattern instances
│  └─ generate(source)   │  → { code, count, names }
└───────────┬───────────┘
            │ invariant function bodies
            ▼
┌───────────────────────┐
│  InvariantInjector     │
│  └─ inject(source,     │
│           invariants)  │  → Modified Solidity source
└───────────┬───────────┘
            │ Augmented contract source
            ▼
┌───────────────────────┐
│  EchidnaAnalyzer       │
│  └─ analyze(source)    │  Runs Echidna with injected invariants
└───────────────────────┘
```

---

## InvariantGenerator

The generator applies all registered pattern rules against the source code and returns structured output:

```python
class InvariantGenerator:
    def __init__(self, patterns=None):
        self.patterns = patterns or [
            UintNonNegativePattern(),
            OwnerNotZeroPattern(),
            BoolSanityPattern(),
            ContractBalancePattern(),
        ]

    def generate(self, source_code: str) -> dict:
        # Returns:
        # {
        #   "code":  str   — joined Solidity function bodies
        #   "count": int   — number of unique invariants
        #   "names": list  — echidna_* function names
        # }
```

**Key behaviours:**
- Invariants are deduplicated while preserving deterministic order
- Function names are extracted via regex: `function (echidna_\w+)`
- The `names` list is passed downstream as `invariant_metadata.generated_names` so the normalizer can tag auto-generated failures

---

## InvariantInjector

The injector places generated invariant code inside the **last** `contract` declaration in the source:

```python
class InvariantInjector:
    def inject(self, source_code: str, invariant_code: str) -> str:
        # 1. Find all `contract <Name> ... {` patterns
        # 2. Insert invariants after the opening brace of the LAST match
        # 3. Fallback: append at EOF if no contract keyword found
```

**Insertion strategy:**
- Invariants are placed immediately after the opening `{` of the last contract
- A comment header `// === AUTO-GENERATED ECHIDNA INVARIANTS ===` marks the boundary
- Solidity resolves state-variable references contract-wide, so declaration order does not affect correctness

---

## Pattern Library

Four invariant patterns are registered by default:

### UintNonNegativePattern

**Detects:** `uint` / `uint256` state variables  
**Generates:** `echidna_<var>_non_negative()` — asserts `var >= 0`

Always true by Solidity semantics. A violation indicates compiler-level corruption or unexpected storage-slot collision.

```solidity
function echidna_balance_non_negative() public view returns (bool) {
    return balance >= 0;
}
```

### OwnerNotZeroPattern

**Detects:** `address` variables containing "owner" in the name  
**Generates:** `echidna_<var>_not_zero()` — asserts `var != address(0)`

Detects ownership invalidation — the zero-address owner effectively disables all `onlyOwner`-guarded functions.

```solidity
function echidna_owner_not_zero() public view returns (bool) {
    return owner != address(0);
}
```

### BoolSanityPattern

**Detects:** `bool` state variables  
**Generates:** `echidna_<var>_valid()` — asserts `var == true || var == false`

A violation indicates storage corruption or unexpected state mutation that pushed a bool slot outside `{0, 1}`.

```solidity
function echidna_paused_valid() public view returns (bool) {
    return paused == true || paused == false;
}
```

### ContractBalancePattern

**Detects:** Always emitted (not source-dependent)  
**Generates:** `echidna_contract_balance_non_negative()` — asserts `address(this).balance >= 0`

Always true at the EVM level, but a violation under Echidna's symbolic model flags potential accounting bugs.

```solidity
function echidna_contract_balance_non_negative() public view returns (bool) {
    return address(this).balance >= 0;
}
```

---

## Adding New Patterns

1. Subclass `InvariantPattern` in `patterns.py`:

```python
class NewPattern(InvariantPattern):
    def match(self, source_code: str) -> list[str]:
        # Return list of Solidity function body strings
        return [...]
```

2. Register in `InvariantGenerator.__init__`:

```python
self.patterns = patterns or [
    ...,
    NewPattern(),
]
```

**Guidelines:**
- Filter out Solidity keywords from regex matches using `_SOLIDITY_KEYWORDS`
- Use the `_MODIFIERS` non-capturing group to skip visibility/mutability modifiers
- Function names must start with `echidna_` (Echidna convention)
- Functions must return `bool` and be marked `public view`

---

## Integration with Echidna

The Echidna analyzer uses the invariant system in its `analyze()` method:

1. `InvariantGenerator.generate(source_code)` → invariant functions + metadata
2. `InvariantInjector.inject(source_code, invariant_code)` → augmented source
3. Echidna runs against the augmented contract in a Docker container
4. Failed invariants are normalised by `FindingNormalizer.normalize_echidna()`
5. Auto-generated invariant failures are tagged with `auto-invariant` using the `generated_names` metadata

This enables differential analysis: user-written properties versus auto-generated sanity checks are distinguishable in the output.