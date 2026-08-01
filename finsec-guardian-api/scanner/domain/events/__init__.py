"""
Domain events emitted by the scanner domain.

Domain events represent business-significant occurrences within the
scanner domain. They are immutable records of facts that have already
happened and may be consumed by the application layer to trigger
notifications, persistence, logging, or other side effects.

The domain layer raises events but does not dispatch or handle them.
"""

from .finding_discovered import FindingDiscovered
from .scan_completed import ScanCompleted
from .scan_failed import ScanFailed
from .scan_started import ScanStarted

__all__ = [
    "FindingDiscovered",
    "ScanCompleted",
    "ScanFailed",
    "ScanStarted",
]