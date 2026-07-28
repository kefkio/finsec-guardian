Finding Entity Blueprint v1.0
1. Purpose

The Finding entity represents a single security issue identified during the analysis of a smart contract.

It is the central business object within the Scanning bounded context. Every analyzer (Slither, Mythril, Echidna, heuristic rules, or future AI analyzers) ultimately produces one or more Finding entities.

A Finding encapsulates not only the vulnerability's details but also the business rules governing its validity, classification, and lifecycle.

2. Responsibilities

The Finding entity is responsible for:

Representing one security issue.
Protecting its own invariants.
Knowing its severity and confidence.
Knowing where it exists within the source code.
Providing business-oriented behaviours (e.g., is_actionable, summary, matches).
Participating in deduplication through its fingerprint.
Remaining persistence-agnostic.

It is not responsible for:

Running security analyzers.
Computing fingerprints.
Saving itself to the database.
Formatting reports.
Calling external APIs.

Those responsibilities belong to domain services, repositories, or the application layer.

3. Domain Invariants

A valid Finding must satisfy the following rules:

Required fields
Title must not be empty.
Description must not be empty.
Recommendation must not be empty.
Classification
Severity must be a valid Severity.
Confidence must be a valid Confidence.
Risk level must be a valid RiskLevel.
Analyzer must be a valid AnalyzerType.
Source
Must have a valid SourceLocation.
Consistency
Critical severity implies critical risk.
Fingerprint must be present before persistence.
Title length must not exceed 200 characters.
4. State
Identity
UUID

Inherited from Entity.

Business Information
title

description

recommendation
Classification
Severity

Confidence

RiskLevel

AnalyzerType
Location
SourceLocation
Tracking

Later versions will introduce

fingerprint

status

created_at

updated_at

resolved_at

suppressed
5. Behaviour

Current behaviours

summary()

is_critical

is_high_risk

is_actionable

has_precise_location

matches()

same_location()

same_analyzer()

Future behaviours

acknowledge()

resolve()

reopen()

suppress()

unsuppress()

change_severity()

merge()

clone()

Notice something important:

Every behaviour answers a business question.

The entity is not a bag of data.

6. Collaborators
                    Finding
                       │
       ┌───────────────┼────────────────┐
       │               │                │
       ▼               ▼                ▼

 SourceLocation    FingerprintService   Report

       │               │                │
       ▼               ▼                ▼

 Severity        Scan Entity       RiskScorer

The arrows indicate collaboration, not ownership.

7. Dependencies

Finding depends only on:

Entity

Enums

Value Objects

Domain Exceptions

It must never depend on:

Django

ORM Models

HTTP

Celery

REST Framework

PostgreSQL

Slither

Mythril APIs

This keeps the domain layer pure and portable.

8. Future Evolution

We already know where this entity is heading.

Version 1
Validation
Behaviour
Fingerprint
Version 2
Lifecycle
Version 3
Historical tracking
Version 4
Suppression workflow
Version 5
AI-assisted remediation
Version 6
SARIF interoperability

Planning this evolution now helps us avoid designs that will block future capabilities.

9. Architect's Notes
Why is Finding an Entity?

A finding has a lifecycle. It can be created, persisted, acknowledged, resolved, reopened, suppressed, and tracked across scans. These characteristics make it an entity rather than a value object.

Why is SourceLocation a Value Object?

A source location has no independent identity. Two locations with identical file positions are equivalent, making it a natural value object.

Why is fingerprint generation delegated?

Fingerprinting is derived behaviour that may evolve over time. By delegating it to a FingerprintService, the entity remains focused on business rules while allowing hashing algorithms and normalization strategies to evolve independently.

10. Tests

This blueprint immediately drives our test plan.

Construction
Valid finding is created successfully.
Empty title is rejected.
Empty description is rejected.
Empty recommendation is rejected.
Enums
Invalid severity is rejected.
Invalid confidence is rejected.
Invalid analyzer is rejected.
Behaviour
is_critical behaves correctly.
summary() returns the expected format.
same_location() compares locations correctly.
matches() compares fingerprints correctly.
Business Rules
Critical severity requires critical risk.
Fingerprint must exist before persistence.

This gives us a direct mapping from design to implementation and verification.