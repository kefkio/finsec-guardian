Architect's Note #43 – Canonical Representations Are Domain Concepts

Canonical representations are often mistaken for implementation details. In reality, they frequently become first-class business concepts because other parts of the system depend on them. In FinSec Guardian, fingerprint generation, deduplication, and historical vulnerability tracking all rely on a stable representation of source code rather than its original formatting.

By modelling NormalizedCode as a dedicated Value Object instead of a plain string, we make this dependency explicit within the domain model. The object communicates intent, enforces invariants, and provides a stable abstraction that remains valid even if the underlying normalization algorithm evolves.

What Comes Next

Once NormalizedCode is implemented, we've completed another major piece of the domain.

The next component is the first service that actually transforms one Value Object into another:

CodeContext
      │
      ▼
CodeNormalizer
      │
      ▼
NormalizedCode

That will be our first true Domain Service in the semantic pipeline, and it marks the transition from modelling data to modelling business processes. I think it's the perfect next sprint because all the foundational concepts it depends on will already be in place.