"""
Slither static analysis service.

Wraps the Slither CLI (subprocess mode) to analyse Solidity source code and
returns normalised findings compatible with the Finding model.

Usage (sync):
    from scanner.services import SlitherService
    service = SlitherService()
    result = service.run_analysis(source_code, contract_name="MyContract")

Usage (background job):
    service.analyze_scan_job(job_id)   # updates DB in-place
"""

import json
import logging
import os
import subprocess
import tempfile

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# Configurable via Django settings
SLITHER_TIMEOUT: int = getattr(settings, "SLITHER_TIMEOUT", 120)
SLITHER_BINARY: str = getattr(settings, "SLITHER_BINARY", "slither")

# Map Slither impact levels → internal severity values
_SEVERITY_MAP: dict[str, str] = {
    "High": "high",
    "Medium": "medium",
    "Low": "low",
    "Informational": "info",
    "Optimization": "info",
}

# Map Slither confidence labels → 0-100 integer
_CONFIDENCE_MAP: dict[str, int] = {
    "High": 90,
    "Medium": 65,
    "Low": 40,
}


class SlitherError(Exception):
    """Raised when Slither analysis cannot be completed."""


class SlitherService:
    """
    Service wrapper around the Slither smart-contract static analyser.

    All public methods return a result dict:
        {
            "success": bool,
            "findings": list[dict],   # normalised Finding-compatible dicts
            "raw_output": dict,       # full Slither JSON (may be empty)
            "error": str | None,
            "stderr": str,
        }
    """

    def __init__(self, binary: str | None = None, timeout: int | None = None) -> None:
        self.binary = binary or SLITHER_BINARY
        self.timeout = timeout or SLITHER_TIMEOUT

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_analysis(self, source_code: str, contract_name: str | None = None) -> dict:
        """
        Analyse a Solidity source string with Slither.

        Writes the code to a temporary file, runs Slither, then cleans up.

        Args:
            source_code:   Raw Solidity source (.sol content).
            contract_name: Optional label used only for log messages.

        Returns:
            Result dict (see class docstring).

        Raises:
            SlitherError: if the binary is missing or the analysis times out.
        """
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".sol",
            prefix="finsec_scan_",
            delete=False,
            encoding="utf-8",
        ) as tmp:
            tmp.write(source_code)
            tmp_path = tmp.name

        try:
            return self._run_subprocess(tmp_path, contract_name)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def analyze_scan_job(self, job_id: int) -> None:
        """
        Full lifecycle analysis for a persisted ScanJob:

        1. Mark job as 'analyzing'.
        2. Run Slither on the stored source code.
        3. Persist each detector result as a Finding (idempotent via get_or_create).
        4. Update summary counts and mark job 'complete' (or 'failed').

        Designed to be called from a background task (thread, Celery, etc.).

        Args:
            job_id: Primary key of the ScanJob to analyse.
        """
        # Late imports to avoid circular dependencies at module load time.
        from scanner.models import FindingCategory, ScanJob  # noqa: PLC0415

        try:
            job = ScanJob.objects.get(id=job_id)
        except ScanJob.DoesNotExist:
            logger.error("analyze_scan_job: ScanJob %s not found", job_id)
            return

        job.status = "analyzing"
        job.started_at = timezone.now()
        job.progress_percentage = 10
        job.save(update_fields=["status", "started_at", "progress_percentage"])

        try:
            result = self.run_analysis(job.source_code, job.contract_name)
        except SlitherError as exc:
            logger.error("Slither failed for ScanJob %s: %s", job_id, exc)
            job.status = "failed"
            job.metadata = {**job.metadata, "slither_error": str(exc)}
            job.progress_percentage = 0
            job.save(update_fields=["status", "metadata", "progress_percentage"])
            return

        job.progress_percentage = 70
        job.save(update_fields=["progress_percentage"])

        self._persist_findings(job, result["findings"])

        job.update_finding_counts()
        job.status = "complete"
        job.completed_at = timezone.now()
        job.progress_percentage = 100
        job.metadata = {**job.metadata, "slither_stderr": result.get("stderr", "")[:2000]}
        job.save(update_fields=["status", "completed_at", "progress_percentage", "metadata"])

        logger.info(
            "ScanJob %s complete: %d finding(s) detected.",
            job_id,
            job.total_findings,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_subprocess(self, sol_file: str, contract_name: str | None) -> dict:
        """Run the slither binary as a subprocess and return a result dict."""
        cmd = [
            self.binary,
            sol_file,
            "--json", "-",            # write JSON results to stdout
            "--no-fail-pedantic",     # don't exit(1) on pedantic-only output
        ]

        logger.info(
            "Running Slither on %s (contract=%s, timeout=%ss)",
            sol_file,
            contract_name or "unknown",
            self.timeout,
        )

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except FileNotFoundError:
            raise SlitherError(
                f"Slither binary not found at '{self.binary}'. "
                "Install it with: pip install slither-analyzer"
            )
        except subprocess.TimeoutExpired:
            raise SlitherError(
                f"Slither analysis timed out after {self.timeout} seconds."
            )

        raw_stdout = proc.stdout.strip()

        if not raw_stdout:
            # Empty output is non-fatal — treat as zero findings.
            logger.warning(
                "Slither produced no JSON output (exit=%s). stderr: %s",
                proc.returncode,
                proc.stderr[:500],
            )
            return {
                "success": True,
                "findings": [],
                "raw_output": {},
                "error": None,
                "stderr": proc.stderr,
            }

        try:
            slither_json: dict = json.loads(raw_stdout)
        except json.JSONDecodeError as exc:
            raise SlitherError(f"Failed to parse Slither JSON output: {exc}") from exc

        findings = self._parse_detectors(slither_json)

        return {
            "success": True,
            "findings": findings,
            "raw_output": slither_json,
            "error": None,
            "stderr": proc.stderr,
        }

    def _parse_detectors(self, slither_json: dict) -> list[dict]:
        """
        Normalise the ``results.detectors`` list from Slither JSON output
        into internal Finding-compatible dicts.
        """
        detectors: list[dict] = slither_json.get("results", {}).get("detectors", [])
        findings: list[dict] = []

        for detector in detectors:
            impact = detector.get("impact", "Informational")
            severity = _SEVERITY_MAP.get(impact, "info")
            confidence_str = detector.get("confidence", "Medium")

            # Extract primary source location from the first element.
            elements: list[dict] = detector.get("elements", [])
            line_number = line_start = line_end = None
            code_snippet = ""

            if elements:
                mapping = elements[0].get("source_mapping", {})
                lines: list[int] = mapping.get("lines", [])
                if lines:
                    line_number = lines[0]
                    line_start = lines[0]
                    line_end = lines[-1]
                code_snippet = elements[0].get("name", "")

            findings.append(
                {
                    "swc_id": detector.get("swc-id", ""),
                    "title": detector.get("check", "Slither Finding"),
                    "severity": severity,
                    "description": detector.get("description", ""),
                    "recommendation": detector.get("first_markdown_element", ""),
                    "confidence": _CONFIDENCE_MAP.get(confidence_str, 50),
                    "line_number": line_number,
                    "line_start": line_start,
                    "line_end": line_end,
                    "code_snippet": code_snippet,
                    "tags": [detector.get("check", "")],
                    "metadata": {
                        "impact": impact,
                        "confidence": confidence_str,
                    },
                }
            )

        return findings

    @staticmethod
    def _persist_findings(job, findings: list[dict]) -> None:
        """
        Upsert each finding into the database.
        Uses get_or_create so re-running a scan is idempotent.
        """
        from scanner.models import Finding, FindingCategory  # noqa: PLC0415

        for data in findings:
            category = None
            swc_id = data.get("swc_id", "")

            if swc_id:
                category, _ = FindingCategory.objects.get_or_create(
                    swc_id=swc_id,
                    defaults={"name": data["title"]},
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
                    "tags": data.get("tags", []),
                    "metadata": data.get("metadata", {}),
                },
            )
