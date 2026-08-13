"""Compatibility re-export for scanner persistence models.

Django imports the app's model module from ``scanner.models``. This shim
keeps existing imports working while the concrete ORM definitions live
under the persistence package.
"""

from .infrastructure.persistence.models import (
    Finding,
    FindingCategory,
    ScanJob,
    ScanReport,
    SolidityVersion,
    SuppressionBaseline,
)

from .infrastructure.persistence.models_v2 import (
    FindingRecord,
    ScanRecord,
)

__all__ = [
    "Finding",
    "FindingCategory",
    "FindingRecord",
    "ScanJob",
    "ScanRecord",
    "ScanReport",
    "SolidityVersion",
    "SuppressionBaseline",
]
