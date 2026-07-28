Architect's Note #39 – Let the Package Structure Reflect the Domain

A well-organized package structure should communicate the architecture of the system without requiring developers to read implementation details. Each top-level package represents a distinct category of domain concepts:

Entities model concepts with identity.
Value Objects model immutable descriptive concepts.
Services perform domain transformations.
Strategies encapsulate interchangeable algorithms.
Ports define the domain's external dependencies.
Exceptions enforce and communicate domain invariants.

When the package structure mirrors the ubiquitous language of the domain, new contributors can understand the architecture by navigating the project tree alone. This reduces cognitive load and reinforces the separation of responsibilities established by Domain-Driven Design and Clean Architecture.