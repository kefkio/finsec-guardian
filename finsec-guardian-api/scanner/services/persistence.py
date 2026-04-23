"""Persistence layer — handles ScanJob lifecycle and Finding creation."""

import logging

from django.utils import timezone

logger = logging.getLogger(__name__)


class ScanPersistence:
    """Manages the database lifecycle of ScanJob and Finding records."""

    @staticmethod
    def mark_analyzing(job, progress: int = 10) -> None:
        job.status = "analyzing"
        job.started_at = timezone.now()
        job.progress_percentage = progress
        job.save(update_fields=["status", "started_at", "progress_percentage"])

    @staticmethod
    def update_progress(job, progress: int) -> None:
        job.progress_percentage = progress
        job.save(update_fields=["progress_percentage"])

    @staticmethod
    def mark_complete(job, metadata: dict | None = None, risk_assessment: dict | None = None) -> None:
        job.update_finding_counts()
        job.status = "complete"
        job.completed_at = timezone.now()
        job.progress_percentage = 100
        if metadata:
            job.metadata = {**job.metadata, **metadata}

        update_fields = ["status", "completed_at", "progress_percentage", "metadata"]

        if risk_assessment:
            job.risk_score = risk_assessment.get("risk_score", 0)
            job.risk_verdict = risk_assessment.get("verdict", "")
            job.risk_assessment = risk_assessment
            update_fields += ["risk_score", "risk_verdict", "risk_assessment"]

        job.save(update_fields=update_fields)

    @staticmethod
    def mark_failed(job, error: str) -> None:
        job.status = "failed"
        job.metadata = {**job.metadata, "error": error}
        job.progress_percentage = 0
        job.save(update_fields=["status", "metadata", "progress_percentage"])

    @staticmethod
    def persist_findings(job, findings: list[dict]) -> None:
        """Upsert findings into the database (idempotent via get_or_create)."""
        from scanner.models import Finding, FindingCategory  # noqa: PLC0415

        for data in findings:
            swc_id = data.get("swc_id", "")
            category, _ = FindingCategory.objects.get_or_create(
                name=data["title"],
                defaults={"swc_id": swc_id},
            )

            Finding.objects.get_or_create(
                scan=job,
                swc_id=swc_id,
                line_number=data.get("line_number"),
                title=data["title"],
                defaults={
                    "category": category,
                    "severity": data["severity"],
                    "description": data["description"],
                    "recommendation": data.get("recommendation", ""),
                    "code_snippet": data.get("code_snippet", ""),
                    "confidence": data.get("confidence", 50),
                    "line_start": data.get("line_start"),
                    "line_end": data.get("line_end"),
                    "column": data.get("column"),
                    "reference_url": data.get("reference_url", ""),
                    "tags": data.get("tags", []),
                    "metadata": data.get("metadata", {}),
                },
            )
