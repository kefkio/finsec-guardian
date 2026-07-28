Absolutely. In fact, these two notes naturally belong together. Note #11 establishes **what an Entity is**, while Note #12 explains **how we correctly implement an Entity in Python using dataclasses**. Together they form a complete design document.

---

# Architect's Notes #11

# The Base Entity (`entity.py`)

## Purpose

Provide a common foundation for every Domain Entity in FinSec Guardian.

It standardizes:

* Identity
* Equality
* Hashing
* Representation

without imposing any business behavior.

This is the cornerstone of our domain model.

---

# Mental Model

Think of an Entity as a passport.

```text
Passport Number:
A12345678
```

Even if the owner changes:

* Address
* Phone Number
* Occupation
* Marital Status

it is still the same person because the passport identifies **who** they are, not **what** they currently look like.

Entities work exactly the same way.

Identity persists while state evolves.

---

# Entity vs Value Object

Suppose we have

```python
SourceLocation(
    filename="Token.sol",
    line=15,
    column=4
)
```

If the line changes from

```text
15
```

to

```text
16
```

it becomes a completely different value.

That is why `SourceLocation` is a **Value Object**.

---

Now consider

```text
Finding

ID = 8ef9...
Severity = Critical
```

Later

```text
Finding

ID = 8ef9...
Severity = High
```

The severity changed.

The identity did not.

Therefore it is still the same Finding.

---

# Responsibilities of the Base Entity

The Base Entity owns exactly four responsibilities.

```text
Identity

↓

Equality

↓

Hashing

↓

Representation
```

Nothing more.

---

# What the Base Entity Does NOT Own

The Base Entity should never know about:

* Django
* Database IDs
* HTTP
* REST APIs
* ORM models
* Serializers
* Business Rules
* Blockchain
* Smart Contracts

Its only concern is the identity semantics shared by every Entity.

---

# Why UUID?

We deliberately use

```python
UUID
```

instead of

```python
int
```

because database IDs belong to the Infrastructure Layer.

UUIDs belong to the Domain.

If tomorrow we replace PostgreSQL with Neo4j, MongoDB, or a distributed event store, the Domain remains unchanged.

---

# Equality

This is the defining characteristic of an Entity.

Two entities are equal **only** if they share the same identity.

Not because they have identical values.

Example

Finding A

```text
ID = abc123
Severity = Critical
```

Finding B

```text
ID = abc123
Severity = Low
```

Business Perspective

```text
Same Finding
```

This distinction is fundamental to Domain-Driven Design.

---

# Hashing

Entities should be hashable so they can be used inside:

* Sets
* Dictionaries
* Caches
* Repository collections

The hash must therefore depend only on

```text
UUID
```

and nothing else.

---

# Representation

When debugging

Instead of

```text
<object at 0x001A23...>
```

we should see

```text
Finding(id=4cf7...)
```

Good representations save countless hours during debugging.

---

# Should Entity be Abstract?

Yes.

```python
class Entity(ABC):
```

An Entity is a modelling concept.

You should never instantiate

```python
Entity()
```

Only concrete business objects such as:

* Finding
* Scan
* Report
* SmartContract

should exist.

---

# The Python Implementation

```python
from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(eq=False, slots=True)
class Entity(ABC):
    """
    Base class for all domain entities.

    An Entity is defined by its identity rather than by
    the values of its attributes.
    """

    id: UUID = field(default_factory=uuid4)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id})"
```

---

# Understanding `eq=False`

This is one of the most important implementation details in the entire project.

Python's dataclasses automatically generate

```python
__eq__()
```

unless instructed otherwise.

By default

```python
@dataclass
```

means

```python
@dataclass(eq=True)
```

which generates value-based equality.

That behaviour is perfect for Value Objects.

It is **incorrect** for Entities.

---

# What Would Happen Without `eq=False`?

Suppose we write

```python
@dataclass
class Finding(Entity):
    ...
```

Python generates

```python
def __eq__(self, other):
    return (
        self.id == other.id
        and self.title == other.title
        and self.severity == other.severity
        and ...
    )
```

This silently replaces the identity-based equality inherited from `Entity`.

Now imagine:

Finding A

```text
ID = abc123
Severity = High
```

Finding B

```text
ID = abc123
Severity = Low
```

Business says

```text
Same Finding
```

Generated dataclass equality says

```text
Different Objects
```

This violates the very definition of an Entity.

---

# Our Rule

Every Domain Entity should begin with

```python
@dataclass(eq=False, slots=True)
```

This preserves the identity semantics defined in `Entity`.

---

# Value Objects Follow the Opposite Rule

Value Objects are defined entirely by their values.

Therefore they should use

```python
@dataclass(
    frozen=True,
    slots=True,
    order=True,
)
```

and allow dataclass to generate equality automatically.

---

# Entity vs Value Object

| Feature   | Entity                 | Value Object                          |
| --------- | ---------------------- | ------------------------------------- |
| Identity  | UUID                   | None                                  |
| Equality  | Identity               | Values                                |
| Mutable   | Yes                    | No                                    |
| Frozen    | No                     | Yes                                   |
| Dataclass | `eq=False, slots=True` | `frozen=True, slots=True, order=True` |
| Lifecycle | Evolves                | Replaced                              |

---

# Project Standards

To keep the architecture consistent, FinSec Guardian adopts the following conventions.

| Component      | Standard                                          |
| -------------- | ------------------------------------------------- |
| Entity         | `@dataclass(eq=False, slots=True)`                |
| Value Object   | `@dataclass(frozen=True, slots=True, order=True)` |
| Enum           | `Enum` subclass                                   |
| Domain Service | Regular class                                     |
| Repository     | Abstract Port                                     |
| Mapper         | Infrastructure Layer                              |

These conventions allow a developer to understand the purpose of a class immediately from its declaration.

---

# Architecture Diagram

```text
                         Entity
                            ▲
        ┌───────────────────┼───────────────────┐
        │                   │                   │
    Finding              Scan              SmartContract
        │
        │ owns
        ▼
 SourceLocation      Severity      Confidence
(Value Objects)        (Enums)        (Enums)
```

Notice that **Entities collaborate with Value Objects and Enums**, but they remain distinct concepts with different equality semantics.

---

# Design Principles Applied

### Domain-Driven Design (DDD)

* Entities are identified by identity.
* Value Objects are identified by value.
* Business concepts remain independent of infrastructure.

---

### Single Responsibility Principle (SRP)

* `Entity` manages identity semantics.
* Business entities manage business rules.
* Value Objects manage immutable concepts.

---

### DRY (Don't Repeat Yourself)

Identity logic is implemented once in `Entity` and reused by every domain entity.

---

### Open/Closed Principle (OCP)

New entities such as `Wallet`, `Transaction`, or `AuditEntry` simply inherit from `Entity` without modifying its implementation.

---

# Key Takeaways

* An **Entity** is defined by its **identity**, not by its current state.
* Every Entity inherits from the shared `Entity` base class.
* Equality and hashing are based solely on UUID.
* Dataclass-generated equality must be disabled using `eq=False`.
* **Value Objects** and **Entities** intentionally follow opposite equality semantics.
* This design provides a consistent, extensible, and maintainable foundation for the entire FinSec Guardian domain model.

---

# Lessons Learned

One of the most subtle yet important aspects of Domain-Driven Design is recognising that **Entities and Value Objects intentionally have opposite behaviours**.

Python's dataclasses naturally favour value-based equality, which is ideal for immutable Value Objects. However, when modelling Entities, we must consciously override this default behaviour to preserve identity semantics. The `eq=False` configuration is therefore not merely a Python implementation detail—it is the mechanism that ensures our code faithfully represents the underlying domain.

By establishing this foundation now, every future entity (`Finding`, `Scan`, `Report`, `Risk`, and `SmartContract`) will inherit consistent identity semantics, making the domain model predictable, extensible, and aligned with both Clean Architecture and Domain-Driven Design principles.
