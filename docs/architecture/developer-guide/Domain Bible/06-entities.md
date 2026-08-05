# Entities

Entities model the core business concepts of the scanner domain.
They are identity-bearing objects whose lifecycle and invariants matter.

## Core Entities

- `Finding`
  - Represents a vulnerability discovered during analysis.
  - Has identity separate from its attributes.
  - Maintains lifecycle state such as `NEW`, `CONFIRMED`, `SUPPRESSED`, and `RESOLVED`.
  - Enforces business rules around severity, risk level, status transitions, and merge behavior.

- `Scan`
  - Represents a single execution of the FinSec Guardian analysis engine.
  - Acts as the aggregate root for scan-related artifacts.
  - Owns relationships to `Finding`, `SmartContract`, and report entities.
  - Enforces scan lifecycle transitions and ownership invariants.

- `SmartContract`
  - Represents the contract under analysis.
  - Encapsulates contract metadata, source references, and verification state.

## Additional Entities

The domain also contains supporting entities such as `Report` and `Risk`.
These entities collaborate with the core objects to represent the full scan result.

## Entity Characteristics

Entities in this domain typically use:

- `@dataclass(eq=False, slots=True)`
- identity semantics rather than field equality
- explicit lifecycle methods and validation
- domain invariants enforced at construction and during operations

This ensures the domain remains consistent even as underlying data changes.
