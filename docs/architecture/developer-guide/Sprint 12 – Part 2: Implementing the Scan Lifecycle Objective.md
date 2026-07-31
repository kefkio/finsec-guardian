# Sprint 12 – Part 2: Implementing the Scan Lifecycle

## Objective

In this sprint, the `Scan` aggregate transitions from being a simple data structure into a rich domain object by introducing business behavior.

One of the fundamental design principles of this project is:

> **Aggregates should expose business behavior, not setters.**

Instead of allowing external code to manipulate the aggregate directly:

```python
scan.status = ScanStatus.RUNNING
```

the aggregate should expose an explicit business operation:

```python
scan.start()
```

The aggregate itself is responsible for deciding whether the requested operation is valid.

---

# Scan Lifecycle

The lifecycle of a scan is represented by the following state machine.

```text
                CREATED
                    │
                    ▼
                RUNNING
               /       \
              /         \
             ▼           ▼
      COMPLETED       FAILED
```

Each transition represents an explicit business rule.

---

# Business Rules

## Rule 1 – A Scan Can Only Start Once

A scan may only transition from the **Created** state to the **Running** state.

```text
CREATED
    │
    ▼
RUNNING

RUNNING
    │
    ▼
❌ start()
```

Attempting to start an already running or completed scan must result in a `DomainValidationError`.

---

## Rule 2 – Only a Running Scan Can Complete

A scan may only transition to **Completed** while it is currently running.

```text
RUNNING
    │
    ▼
COMPLETED
```

Any attempt to complete a scan in another state violates the aggregate's business rules.

---

## Rule 3 – Only a Running Scan Can Fail

A scan may only transition to **Failed** while it is currently running.

```text
RUNNING
    │
    ▼
FAILED
```

Failure is a terminal state and cannot occur before execution begins.

---

## Rule 4 – Start Time Is Recorded Automatically

The aggregate is responsible for recording when execution begins.

Consumers of the aggregate should never manually assign the start timestamp.

---

## Rule 5 – Completion Time Is Recorded Automatically

Likewise, the aggregate records the completion timestamp whenever the scan either completes successfully or fails.

This guarantees consistent audit information across the system.

---

# Version 1 Lifecycle Methods

The following methods implement the lifecycle behavior of the aggregate.

```python
def start(self) -> None:
    """
    Starts the scan.
    """
    if self.status is not ScanStatus.CREATED:
        raise DomainValidationError(
            "Only a created scan can be started."
        )

    self.status = ScanStatus.RUNNING
    self.started_at = timezone.now()


def complete(self) -> None:
    """
    Marks the scan as completed.
    """
    if self.status is not ScanStatus.RUNNING:
        raise DomainValidationError(
            "Only a running scan can be completed."
        )

    self.status = ScanStatus.COMPLETED
    self.completed_at = timezone.now()


def fail(self) -> None:
    """
    Marks the scan as failed.
    """
    if self.status is not ScanStatus.RUNNING:
        raise DomainValidationError(
            "Only a running scan can fail."
        )

    self.status = ScanStatus.FAILED
    self.completed_at = timezone.now()
```

---

# Why Business Methods Are Better Than Public Setters

Suppose external code changes the status directly.

```python
scan.status = ScanStatus.COMPLETED
```

Although the status changes, nothing guarantees that:

* the completion timestamp is recorded,
* lifecycle rules are enforced,
* aggregate invariants remain valid.

The aggregate may therefore enter an inconsistent state.

By contrast:

```python
scan.complete()
```

ensures that every required business rule is executed consistently.

The aggregate—not the caller—maintains its own integrity.

---

# Convenience Properties

Instead of scattering enum comparisons throughout the application:

```python
if scan.status == ScanStatus.RUNNING:
```

the aggregate should expose intention-revealing properties.

```python
@property
def is_running(self) -> bool:
    """
    Returns True if the scan is currently running.
    """
    return self.status is ScanStatus.RUNNING


@property
def is_completed(self) -> bool:
    """
    Returns True if the scan completed successfully.
    """
    return self.status is ScanStatus.COMPLETED


@property
def is_failed(self) -> bool:
    """
    Returns True if the scan has failed.
    """
    return self.status is ScanStatus.FAILED


@property
def has_started(self) -> bool:
    """
    Returns True if execution has begun.
    """
    return self.started_at is not None


@property
def has_completed(self) -> bool:
    """
    Returns True if the scan has finished.
    """
    return self.completed_at is not None
```

These properties make client code more expressive.

Instead of:

```python
if scan.status == ScanStatus.RUNNING:
```

developers can simply write:

```python
if scan.is_running:
```

The code now communicates business intent rather than implementation details.

---

# Time Handling

The aggregate should use timezone-aware timestamps.

Rather than:

```python
datetime.now()
```

the implementation should use Django's timezone utilities:

```python
from django.utils import timezone
```

and record timestamps using:

```python
self.started_at = timezone.now()
self.completed_at = timezone.now()
```

### Why This Matters

Using `timezone.now()` provides several advantages:

* timezone-aware datetime objects,
* compatibility with Django's `USE_TZ` configuration,
* easier testing through mocking,
* avoidance of naive-versus-aware datetime comparison errors,
* consistent audit timestamps across the application.

For a security and compliance-focused platform such as FinSec Guardian, timezone-aware timestamps should be considered the standard.

---

# Architect's Note #50 – State Transitions Belong to the Aggregate

An aggregate should never expose unrestricted mutation of its internal state. Instead, it should provide business operations that encapsulate valid state transitions and enforce all associated invariants.

Methods such as `start()`, `complete()`, and `fail()` ensure that lifecycle rules, timestamps, and validation are applied consistently, preventing callers from leaving the aggregate in an invalid state.

This approach produces a rich domain model in which behavior and state evolve together, making the code easier to understand, easier to test, and more resilient to future change.
