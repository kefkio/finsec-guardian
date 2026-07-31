Architect's Note #42 – A Value Object Represents the Result, Not the Process

A common design mistake is to allow a Value Object to understand or reproduce the process that created it. This couples state with transformation and violates the Single Responsibility Principle. NormalizedCode should therefore represent only the result of normalization. It stores the canonical representation and enforces the invariants of that representation, but it has no knowledge of how normalization was performed.

This distinction allows normalization algorithms to evolve independently—from simple whitespace canonicalization to AST-based semantic normalization—without changing the meaning or responsibilities of the NormalizedCode value object.

My Recommendation

Let's finish NormalizedCode completely before touching CodeNormalizer.

Why?

Because once we know exactly what the output object looks like, implementing the service becomes a straightforward transformation:

CodeContext
      │
      ▼
CodeNormalizer
      │
      ▼
NormalizedCode

That follows the design principle we've used throughout this project: define the domain concepts first, then implement the services that transform them. I think it has served us well so far, and it will keep the semantic pipeline just as clean as the rest of the domain model.