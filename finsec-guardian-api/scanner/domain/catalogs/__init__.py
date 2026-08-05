"""
Catalogs package containing immutable domain knowledge bases.

Catalogs expose canonical domain reference data used by
domain services while remaining free of infrastructure,
database, or framework dependencies.
"""

from scanner.domain.catalogs.recommendation_catalog import (
    RECOMMENDATION_CATALOG,
)

__all__ = (
    "RECOMMENDATION_CATALOG",
)