# Ports

Ports define the domain's external dependencies without pinning the domain to a specific infrastructure implementation.
They are the contract interfaces through which the domain interacts with persistence and external services.

## Current Port Interfaces

The `scanner/domain/ports` package currently includes placeholder and repository interfaces such as:

- `ScanRepository`
  - Persist and retrieve scan jobs by ID, hash, status, user, and other query methods.

- `FindingRepository`
- `ReportRepository`
- `ContractRepository`
- `Analyzer`

The remaining port files are intentionally empty placeholders that signal domain boundary responsibilities.

## Port Responsibilities

Ports are responsible for:

- defining abstract methods used by domain or application code
- avoiding domain dependencies on Django ORM, databases, or HTTP
- allowing infrastructure adapters to implement persistence, messaging, or external analysis engines

## Implementation Pattern

- The domain depends only on port interfaces.
- Infrastructure implements those interfaces.
- Application layer composes domain services and port implementations.

This keeps the scanner domain isolated and testable.
