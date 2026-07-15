"""Mapping helpers between persistence entities and application/domain objects."""

from __future__ import annotations


class PersistenceMapper:
    """Placeholder mapper used to keep persistence concerns isolated."""

    @staticmethod
    def to_dict(instance) -> dict:
        return instance.__dict__.copy()
