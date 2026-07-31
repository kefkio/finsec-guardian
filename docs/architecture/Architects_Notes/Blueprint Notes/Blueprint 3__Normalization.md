# Normalization Blueprint

**Project:** FinSec Guardian  
**Module:** Scanner Domain  
**Sprint:** Source Code Fingerprinting Framework  
**Version:** 1.0

---

# 1. Overview

The normalization subsystem is responsible for transforming raw smart contract source code into a deterministic canonical representation prior to fingerprint generation.

The primary objective is to ensure that semantically equivalent source code produces identical fingerprints despite superficial differences such as:

- comments
- whitespace
- line endings
- unicode encoding
- tab formatting

Normalization is therefore the foundation of duplicate vulnerability detection within FinSec Guardian.

Unlike many existing implementations that rely on regular expressions, this project adopts a deterministic finite-state lexical normalization approach to preserve source integrity while removing non-semantic variation.

---

# 2. Objectives

The normalization subsystem has five primary objectives.

## 2.1 Deterministic Output

The same logical source code must always normalize into exactly the same canonical representation.

```
Input A
↓

Normalization

↓

Canonical Source X
```

```
Input B
↓

Normalization

↓

Canonical Source X
```

If two snippets are semantically identical after normalization, they must produce identical fingerprints.

---

## 2.2 Preserve Program Semantics

Normalization must never alter executable behaviour.

Examples include preserving:

- string literals
- character literals
- escape sequences
- hexadecimal literals
- URIs

For example:

```solidity
string memory uri = "ipfs://Qm...";
```

must remain unchanged.

---

## 2.3 Remove Non-Semantic Noise

Normalization removes differences that do not affect execution.

Examples include:

- comments
- CRLF vs LF
- Unicode normalization
- excessive blank lines
- tab width differences

---

## 2.4 Language Independence

The framework separates generic normalization from language-specific normalization.

Generic operations include:

- Unicode normalization
- line-ending normalization
- tab expansion
- blank-line collapsing

Language-specific operations include:

- comment removal
- string preservation
- lexical scanning
- whitespace normalization outside literals

---

## 2.5 Extensibility

The architecture allows new languages to be supported without modifying the existing normalization pipeline.

Future implementations may include:

- Solidity
- Vyper
- Rust (Solana)
- Move
- Cairo

---

# 3. Architecture

```
                 +------------------------------+
                 | NormalizationOptions         |
                 +------------------------------+
                               │
                               ▼
                 +------------------------------+
                 | BaseNormalizer               |
                 +------------------------------+
                               │
                 delegates
                               ▼
                 +------------------------------+
                 | SolidityNormalizer           |
                 +------------------------------+
                               │
                               ▼
                 +------------------------------+
                 | NormalizationResult          |
                 +------------------------------+
                               │
                               ▼
                    FingerprintService
```

The BaseNormalizer owns the normalization pipeline.

Concrete language normalizers implement the lexical normalization algorithm.

---

# 4. Domain Components

## 4.1 NormalizationOptions

NormalizationOptions is an immutable Value Object that defines how normalization should be performed.

Responsibilities include:

- normalization configuration
- runtime validation
- predefined normalization presets

Example presets:

- fingerprinting()
- preserve_formatting()
- raw()

This object contains no normalization logic.

---

## 4.2 NormalizationResult

NormalizationResult is an immutable Value Object representing the output of normalization.

It contains:

- normalized source code
- number of removed comments

The object guarantees that downstream services always receive a valid canonical representation.

---

## 4.3 BaseNormalizer

BaseNormalizer coordinates the normalization pipeline.

Responsibilities include:

- input validation
- Unicode normalization
- line-ending normalization
- tab expansion
- blank-line collapsing

It delegates all language-aware processing to subclasses.

---

## 4.4 SolidityNormalizer

SolidityNormalizer performs lexical normalization using a deterministic finite-state scanner.

Responsibilities include:

- comment removal
- preserving string literals
- preserving escape sequences
- preserving URIs
- whitespace normalization outside literals

Unlike BaseNormalizer, this class understands Solidity syntax.

---

# 5. Normalization Pipeline

The normalization pipeline executes in a fixed deterministic order.

```
Validate Source

↓

Unicode NFC

↓

Normalize Line Endings

↓

Expand Tabs

↓

Language Normalization

↓

Collapse Blank Lines

↓

NormalizationResult
```

This order is intentional.

Each stage prepares the source for the next stage while maintaining deterministic output.

---

# 6. Why Not Regular Expressions?

Many source-code normalization implementations rely on regular expressions to remove comments.

For example:

```
r"//.*?$"
```

appears to remove line comments.

However, this approach fails in common blockchain scenarios.

Example:

```solidity
string memory uri = "ipfs://QmHash";
```

Regex incorrectly interprets

```
//
```

inside the string as a comment.

The resulting source becomes corrupted.

Similar failures occur with:

- URLs
- JSON metadata
- escaped quotation marks
- nested lexical constructs

Regular expressions cannot maintain lexical state.

---

# 7. Finite-State Lexical Normalization

To overcome these limitations, this project adopts a deterministic finite-state lexical scanner.

Instead of searching for patterns, the scanner processes one character at a time while tracking its current lexical state.

Example states include:

- NORMAL
- STRING
- CHARACTER
- LINE_COMMENT
- BLOCK_COMMENT
- ESCAPE

Each state defines:

- valid transitions
- emitted characters
- ignored characters

Because the scanner always knows its current lexical state, comment delimiters inside strings are never misinterpreted.

---

# 8. Design Principles

The normalization subsystem follows the following software engineering principles.

## Single Responsibility Principle

Each class has exactly one responsibility.

Examples:

NormalizationOptions

→ configuration

NormalizationResult

→ normalization output

BaseNormalizer

→ pipeline orchestration

SolidityNormalizer

→ lexical normalization

---

## Open/Closed Principle

The framework is open for extension but closed for modification.

Adding a Rust normalizer does not require changes to BaseNormalizer.

---

## Immutability

NormalizationOptions and NormalizationResult are immutable Value Objects.

This guarantees deterministic behaviour throughout the normalization pipeline.

---

## Determinism

The normalization process is deterministic.

Identical logical input always produces identical canonical output.

---

## Separation of Concerns

Generic normalization is separated from language-aware normalization.

This improves maintainability and simplifies testing.

---

# 9. Current Scope

The normalization subsystem performs lexical normalization only.

It deliberately does not implement:

- parsing
- semantic analysis
- AST construction
- compiler optimizations
- control-flow analysis

These concerns belong to later stages of the scanning pipeline.

---

# 10. Current Implementation Status

## Completed

✓ NormalizationOptions

✓ NormalizationResult

✓ BaseNormalizer

---

## In Progress

SolidityNormalizer

---

## Planned

FingerprintService

---

# 11. Expected Benefits

The proposed architecture provides several advantages.

- Deterministic fingerprint generation
- Improved duplicate detection
- Elimination of regex-based parsing errors
- Clean separation between generic and language-specific logic
- Easier testing
- Easier extension to additional blockchain languages

---

# 12. Conclusion

The normalization subsystem establishes the canonical representation upon which the remainder of the fingerprinting framework depends.

By combining immutable configuration objects, a language-independent normalization pipeline, and deterministic finite-state lexical scanning, the design provides a robust foundation for accurate vulnerability fingerprint generation while remaining extensible to future blockchain programming languages.