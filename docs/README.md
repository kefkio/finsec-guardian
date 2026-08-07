# FinSec Guardian — Technical Documentation

This directory collects the project documentation for the current FinSec Guardian build. The material is intentionally concise and focused on the architecture, workflow, and developer entry points that matter most right now.

## What this build covers

FinSec Guardian combines a React frontend, a Django REST API, and a domain analysis layer for correlated findings and attack-path discovery. The platform is designed to support multi-engine smart-contract analysis, deterministic risk scoring, and structured reporting.

## Documentation map

### System overview

| Document | Purpose |
| --- | --- |
| [system-architecture.md](system-architecture.md) | High-level component model and deployment view |
| [data-flow.md](data-flow.md) | Request and processing flow across the stack |
| [design-decisions.md](design-decisions.md) | Key architectural decisions and rationale |
| [threat-model.md](threat-model.md) | Threat model and mitigation focus areas |

### Backend

| Document | Purpose |
| --- | --- |
| [backend/overview.md](backend/overview.md) | Backend structure and service organisation |
| [backend/architecture.md](backend/architecture.md) | Core services, models, and API responsibilities |
| [backend/analyzers.md](backend/analyzers.md) | Details on the supported analysis engines |
| [backend/orchestrator.md](backend/orchestrator.md) | Scan orchestration and execution flow |
| [backend/scan-pipeline.md](backend/scan-pipeline.md) | Source-code and address-based scan lifecycle |
| [backend/risk-scoring.md](backend/risk-scoring.md) | Risk scoring model and interpretation |
| [backend/invariants.md](backend/invariants.md) | Echidna invariant generation and injection |

### Frontend

| Document | Purpose |
| --- | --- |
| [frontend/overview.md](frontend/overview.md) | Frontend structure and user-facing workflows |
| [frontend/ui-system.md](frontend/ui-system.md) | UI patterns and styling system |
| [frontend/security-architecture.md](frontend/security-architecture.md) | Frontend security controls and guidance |

## Current focus areas

The current documentation is aligned with the active implementation:

- Multi-engine scanning and normalisation
- Risk scoring and reporting
- Correlation-based attack-path discovery in the domain layer
- Secure-by-design application structure and deployment concerns

## Suggested reading order

1. Start with [system-architecture.md](system-architecture.md)
2. Review [backend/architecture.md](backend/architecture.md) for the implementation shape
3. Use [backend/scan-pipeline.md](backend/scan-pipeline.md) for workflow details
4. Refer to [frontend/overview.md](frontend/overview.md) for the UI side of the platform

## Notes

This documentation set is intended to stay practical and maintainable. If a section becomes overly detailed or duplicates another document, it should be folded into the nearest relevant guide rather than expanded further.
