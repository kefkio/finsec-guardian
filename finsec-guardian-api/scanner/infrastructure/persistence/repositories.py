"""Repository interfaces and adapters for scanner persistence."""

from __future__ import annotations

from typing import Any


class ScanJobRepository:
    """Thin repository wrapper around ScanJob persistence."""

    def get_by_id(self, job_id: int) -> Any:
        from .models import ScanJob

        return ScanJob.objects.get(pk=job_id)


class FindingRepository:
    """Thin repository wrapper around Finding persistence."""

    def create(self, **kwargs: Any) -> Any:
        from .models import Finding

        return Finding.objects.create(**kwargs)
