# Value Objects

Value objects in the scanner domain are immutable, self-validating objects that represent domain facts.
They are defined entirely by their values rather than by identity.

## Core Value Objects

- `SourceLocation`
  - Represents the physical source file location of a finding.
  - Validates file path, line numbers, optional columns, and ranges.
  - Provides helpers such as `display()`, `is_range`, and `contains()`.

- `VulnerabilitySignature`
  - Represents the deterministic semantic identity of a vulnerability.
  - Encapsulates a normalized hash string and validates formatting.
  - Enables duplicate detection, historical matching, and correlation.

- `RiskSummary`
  - An immutable aggregate of scan risk posture.
  - Captures overall risk level, severity counts, weighted score, confidence, and deployability.
  - Validates that counts are consistent with total findings and risk rules.

- `CorrelationGroup`
  - Represents a group of findings that are believed to belong to the same attack path or correlation cluster.
  - Supports validation of grouping invariants.

- `CorrelationResult`
  - Represents the result of a pairwise correlation assessment.
  - Includes a score and explanation reasons for the relationship.

## Future Value Objects

The long-term architecture also anticipates additional value objects such as:

- `AttackPath` – a domain model of a likely exploit sequence through a contract.
- `Recommendation` – a structured remediation guidance object separated from the raw finding description.

## Implementation Notes

Value objects in this project are typically implemented with:

- `@dataclass(frozen=True, slots=True)`
- value-based equality
- strict validation in `__post_init__`

This keeps the domain model stable and prevents invalid or mutable state from leaking into business logic.
