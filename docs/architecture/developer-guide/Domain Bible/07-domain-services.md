# Domain Services

Domain services contain stateless operations that belong to the domain but do not naturally fit on a single entity.
They encapsulate business transformations, calculations, and matching logic.

## Current Services

- `FingerprintService`
  - Generates deterministic vulnerability fingerprints.
  - Encodes analyzer metadata, normalized paths, titles, and line numbers.
  - Versioned so future fingerprint algorithms can evolve safely.

- `DeduplicationService`
  - Detects duplicate findings by `VulnerabilitySignature`.
  - Removes duplicates, groups them, and merges semantically equivalent findings.
  - Keeps deduplication logic separate from entity persistence.

- `FindingCorrelationService`
  - Calculates semantic similarity between findings.
  - Scores relationships based on contract, file, analyzer, severity, and proximity.
  - Produces a `CorrelationResult` that explains why findings are related.

- `RiskAssessmentService`
  - Aggregates a collection of findings into risk posture metrics.
  - Computes severity distributions, overall risk, blocking status, weighted scores, and summaries.
  - Produces `RiskSummary` value objects for reporting.

## Planned Services

The long-term domain architecture anticipates additional services to support higher-level decisioning:

- `AttackPathService`
- `ThreatModelService`
- `RecommendationService`
- `ScanDecisionService`
- `ScanStatisticsService`

These services will be responsible for deriving attack scenarios, threat context, remediation guidance, and scan-level decisions without introducing persistence concerns into the domain.

## Service Principles

Domain services should be:

- stateless
- explicitly named for the operation they perform
- focused on domain logic rather than infrastructure
- callable from application orchestration code without introducing side effects
