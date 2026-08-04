# Enterprise Finding Design

Finding (Entity)
│
├── Identity
│     id
│
├── Metadata
│     title
│     description
│     recommendation
│
├── Classification
│     severity
│     confidence
│     risk_level
│     analyzer
│
├── Location
│     location
│
├── Identity of Vulnerability
│     signature
│     fingerprint
│
├── Lifecycle
│     discovered_at
│
└── Domain Behaviour
      summary()
      matches()
      same_signature()
      same_location()
      same_analyzer()
      is_critical
      requires_immediate_attention

      Step 1 — Define the Domain Responsibilities

A Finding should be responsible for only one thing:

Representing a single security vulnerability discovered during analysis.

Everything else should revolve around that responsibility.

It should know:

what it is
where it is
how severe it is
how confident the analyzer is
how to compare itself with another finding
how to describe itself

It should not know:

how it is stored
how reports are generated
how the scanner works
how Django saves it

Those belong elsewhere.

Step 2 — Final Enterprise Model

I recommend the following model.

Finding
│
├── Identity
│      id
│
├── Classification
│      severity
│      confidence
│      risk_level
│      analyzer
│
├── Description
│      title
│      description
│      recommendation
│
├── Source
│      location
│
├── Identification
│      signature
│      fingerprint
│
├── Audit
│      discovered_at
│
└── Behaviour
       matches()
       summary()
       same_signature()
       same_location()
       same_analyzer()

This is almost identical to what you'll find in mature enterprise SAST platforms.

Step 3 — Recommended Fields
title: str

description: str

recommendation: str

severity: Severity

confidence: Confidence

risk_level: RiskLevel

analyzer: AnalyzerType

location: SourceLocation

signature: VulnerabilitySignature

fingerprint: str

discovered_at: datetime

Notice there is no reference to Scan.

That is intentional.

The aggregate relationship is:

Scan
 ├── Finding
 ├── Finding
 ├── Finding

The child should not maintain a hard reference back to its parent unless you have a compelling domain reason. The Scan aggregate owns the collection and enforces its invariants.

Step 4 — Constructor Validation

The constructor should perform only invariant validation:

✓ title not blank

✓ description not blank

✓ recommendation not blank

✓ title <= 200 characters

✓ severity valid

✓ confidence valid

✓ analyzer valid

✓ risk level valid

✓ location valid

✓ signature valid

✓ fingerprint not empty

No database logic.

No repositories.

No services.

Step 5 — Derived Properties

These make the entity expressive.

is_critical

is_high

is_medium

is_low

is_informational

is_high_risk

requires_immediate_attention

Then your application code becomes much cleaner:

if finding.requires_immediate_attention:
    ...

instead of

if (
    finding.severity == Severity.CRITICAL
    or finding.severity == Severity.HIGH
):
    ...
Step 6 — Domain Behaviour

The entity should own comparison logic.

summary()

matches()

same_signature()

same_location()

same_analyzer()

For example:

finding1.matches(finding2)

is much clearer than comparing multiple attributes externally.

Step 7 — Ordering

Since your enums already define priorities, Finding can be naturally sortable.

A sensible ordering is:

Severity
Risk Level
Confidence
Source Location

That allows:

sorted(findings)

to automatically produce the most critical issues first.

Step 8 — Sprint Breakdown

We'll build finding.py in manageable phases:

Sprint 14.1 — Core Entity

Dataclass definition
Fields
Constructor
Basic validation

Sprint 14.2 — Validation

Private validation helpers
Business invariants
Fingerprint and signature validation

Sprint 14.3 — Domain Behaviour

summary()
matches()
same_signature()
same_location()
same_analyzer()

Sprint 14.4 — Derived Properties

Severity helpers
Risk helpers
Convenience properties

Sprint 14.5 — Enterprise Polish

Natural ordering
Rich documentation
Unit-test readiness
Final review