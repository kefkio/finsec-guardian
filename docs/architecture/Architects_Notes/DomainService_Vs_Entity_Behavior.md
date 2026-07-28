# Architect's Notes #10

## Domain Services vs Entity Behaviour

### Topic

Should a Finding calculate its own fingerprint, or should a FingerprintService do it?

---

### The Problem

Every security finding needs a stable identifier that allows us to:

- Detect duplicate findings
- Merge results from multiple analyzers
- Track findings across rescans
- Compare findings over time

This identifier is called a **Fingerprint**.

The architectural question is:

**Who is responsible for creating it?**

### Mental Model

                   Finding
                      │
          "I need a fingerprint"
                      │
                      ▼
            FingerprintService
                      │
                      ▼
             Fingerprint (VO)
                      │
                      ▼
                Returned to Finding

Notice that Finding owns the fingerprint, but it does not know how to build it.

This is a very important distinction.

### Two Competing Designs

#### Option A — Entity Creates Fingerprint

Finding
    │
    ├── title
    ├── severity
    ├── location
    └── calculate_fingerprint()
Advantages
High cohesion
Easy API
Object owns more behaviour
Disadvantages

Finding now becomes responsible for:

Hashing
Normalisation
Fingerprint algorithms
Deduplication strategy

These are technical concerns, not business rules.

Option B — FingerprintService (Chosen)
Finding
      │
      ▼
FingerprintService
      │
      ▼
Fingerprint

Advantages
Single Responsibility Principle
Easier to test
Algorithm can evolve independently
Supports multiple fingerprint strategies
Cleaner domain entity

Disadvantages
Slightly more indirection
Requires dependency injection from the application layer
Our Decision

✅ We selected Option B.

Fingerprint generation belongs to a Domain Service.

The resulting fingerprint is represented as a Value Object.

Why?

A fingerprint is not part of the intrinsic identity of a Finding.

It is derived from information contained within the Finding.

The distinction is subtle but extremely important.

Think of it this way:

Finding
│
├── title
├── severity
├── location
└── analyzer

From those attributes we compute

SHA256(...)

The SHA256 hash is derived.

It is not part of the business concept of a Finding.

Design Principles Applied
1. Single Responsibility Principle (SRP)

A class should have one reason to change.

Finding changes when:
Business rules change
Validation changes
Lifecycle changes
FingerprintService changes when:
Hashing algorithm changes
Normalisation rules change
Deduplication strategy changes

Different reasons.

Different classes.

2. High Cohesion

Finding remains focused on security findings.

It does not become a cryptographic utility.

3. Separation of Concerns

Business rules stay inside entities.

Technical algorithms stay inside services.

4. Open/Closed Principle

Suppose Version 2 introduces:

SHA3

instead of

SHA256

Only one class changes:

FingerprintService

The Finding entity remains untouched.

The Fingerprint Value Object

The service returns a Value Object.

Fingerprint

↓

Immutable

↓

Comparable

↓

Hashable

↓

Serializable

This separates:

What a fingerprint is
How a fingerprint is produced
Relationship Diagram
                 Finding
                     │
          has-a Fingerprint
                     │
                     ▼
               Fingerprint
                     ▲
                     │
          created by
                     │
                     ▼
         FingerprintService
What the Entity Owns

The Finding entity owns:

Identity
Validation
Lifecycle
Business behaviour
Severity
Confidence
Risk
Source location
Fingerprint (as data)
What the Entity Does NOT Own

Finding should never know:

SHA256
SHA3
MD5
Hashing libraries
Canonicalisation rules
Deduplication algorithms

Those belong elsewhere.

Analogy

Think of a passport.

A person has:

Name
Date of birth
Nationality

The passport office generates the passport number.

The passport number belongs to the person,

but the person does not generate it.

Finding and Fingerprint follow exactly the same relationship.

Common Mistake

❌ Putting hashing logic inside the entity.

class Finding:

    def calculate_fingerprint(self):
        ...

Why this is problematic:

The entity now has two responsibilities:

Representing a security finding.
Implementing fingerprint generation algorithms.

This violates the Single Responsibility Principle.

Interview Perspective

Question: Why didn't you let the Finding entity generate its own fingerprint?

Answer:

A fingerprint is a derived representation of a Finding rather than part of its intrinsic business identity. The entity owns the fingerprint as data, but the algorithm for generating it is a technical concern that may evolve independently. Encapsulating that logic in a Domain Service adheres to the Single Responsibility Principle, keeps the entity focused on business rules, and allows fingerprinting strategies to evolve without modifying the core domain model.

Key Takeaways
Finding represents the business concept.
Fingerprint represents an immutable identifier.
FingerprintService encapsulates the algorithm.
We separated representation from generation.
This design follows SRP, high cohesion, and clean architecture principles.
Lessons Learned

This discussion illustrates one of the most valuable architectural heuristics we've encountered so far:

If a behavior exists to preserve an entity's business invariants, it usually belongs on the entity. If a behavior exists to transform, derive, calculate, or generate information using technical algorithms or strategies that may evolve independently, it is often better modeled as a Domain Service.

I think this principle will guide many of our future design decisions—not just for fingerprinting, but also for risk scoring, report generation, AI-assisted analysis, and any other computation-heavy parts of FinSec Guardian.