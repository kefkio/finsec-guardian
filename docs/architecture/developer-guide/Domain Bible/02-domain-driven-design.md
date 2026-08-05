# Domain-Driven Design

## Long-Term Domain Architecture

The scanner domain is intentionally organized around business concepts rather than persistence or framework concerns.

```
Domain
│
├── Entities
│      Finding
│      Scan
│      SmartContract
│
├── Value Objects
│      SourceLocation
│      RiskSummary
│      VulnerabilitySignature
│      CorrelationGroup
│      CorrelationResult
│      AttackPath
│      Recommendation
│
├── Services
│      FingerprintService
│      DeduplicationService
│      FindingCorrelationService
│      AttackPathService
│      ThreatModelService
│      RiskAssessmentService
│      RecommendationService
│      ScanDecisionService
│      ScanStatisticsService
│
├── Ports
│
├── Exceptions
│
└── Enums
```

### Purpose

The domain layer owns the business knowledge of FinSec Guardian. It answers questions such as:

- What is a security finding?
- What constitutes a scan?
- How is risk expressed?
- What invariants must always hold?

It should not depend on Django, ORM models, REST APIs, HTTP, or infrastructure details.

### Package Structure

The current `scanner/domain` package is structured to keep the domain pure and explicit:

- `entities/` – rich objects with identity and lifecycle behavior.
- `value_objects/` – immutable semantic facts defined by value.
- `services/` – stateless domain operations that do not belong to a single entity.
- `ports/` – abstract domain-facing interfaces to external systems.
- `exceptions/` – domain validation and invariant failures.
- `enums/` – domain-specific classification and policy values.

### Design Principles

- Entities own business invariants and lifecycle behavior.
- Value objects represent facts and are compared by value.
- Services encapsulate operations that cross entity boundaries or derive domain results.
- Ports define the boundaries between the domain and infrastructure.
- The domain is the most stable layer; infrastructure should adapt to it.
