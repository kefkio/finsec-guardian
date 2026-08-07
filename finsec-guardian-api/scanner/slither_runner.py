"""
Task adapter for smart-contract analysis.

This module provides a single entry point, ``run_slither_analysis``,
used by the API layer.

Supported call patterns
-----------------------

Synchronous:

    result = run_slither_analysis(source_code)

Asynchronous:

    run_slither_analysis.delay(job_id)

When Celery is available, the task is registered as a shared task.
Otherwise a lightweight thread-backed fallback is provided so the API
remains unchanged.
"""

from __future__ import annotations

import logging
import threading

logger = logging.getLogger(__name__)


def _run_analysis_impl(source_code_or_job_id):
    """
    Execute a smart-contract scan.

    Parameters
    ----------
    source_code_or_job_id:
        Either

        * Solidity source code (str)
        * ScanJob primary key (int)

    Returns
    -------
    dict
        Raw analyzer output for synchronous scans.
    """
    from scanner.services.orchestrator import ScanOrchestrator
    from scanner.services.analyzers.slither import SlitherError

    orchestrator = ScanOrchestrator()

    # -------------------------------------------------------------
    # Background ScanJob execution
    # -------------------------------------------------------------
    if isinstance(source_code_or_job_id, int) or (
        isinstance(source_code_or_job_id, str)
        and source_code_or_job_id.isdigit()
    ):
        job_id = int(source_code_or_job_id)

        try:
            orchestrator.run_scan_job(job_id)
            return {
                "success": True,
                "job_id": job_id,
                "status": "queued",
            }
        except Exception as exc:  # noqa: BLE001
            logger.exception("Background scan job %s failed", job_id)
            return {
                "success": False,
                "job_id": job_id,
                "error": str(exc),
            }

    # -------------------------------------------------------------
    # Direct source-code analysis
    # -------------------------------------------------------------
    try:
        result = orchestrator.run_scan(source_code_or_job_id)

        return result.get("raw_output", {})

    except SlitherError as exc:
        logger.exception("Slither analysis failed")

        return {
            "success": False,
            "error": str(exc),
        }

    except Exception as exc:
        logger.exception("Analysis pipeline failed")

        return {
            "success": False,
            "error": str(exc),
        }


# ----------------------------------------------------------------------
# Celery integration
# ----------------------------------------------------------------------

try:
    from celery import shared_task

    @shared_task(
        name="scanner.run_slither_analysis",
        bind=False,
    )
    def run_slither_analysis(source_code_or_job_id):
        """Celery task entry point."""
        return _run_analysis_impl(source_code_or_job_id)

    logger.debug("run_slither_analysis registered as Celery task.")

except ImportError:

    class _ThreadBackedTask:
        """
        Minimal Celery-compatible fallback.

        Exposes:

            run_slither_analysis(...)
            run_slither_analysis.delay(...)
        """

        def __call__(self, source_code_or_job_id):
            return _run_analysis_impl(source_code_or_job_id)

        def delay(self, *args, **kwargs):
            thread = threading.Thread(
                target=_run_analysis_impl,
                args=args,
                kwargs=kwargs,
                daemon=True,
            )

            thread.start()

            logger.debug(
                "Background analysis started in thread %s",
                thread.ident,
            )

            return thread

    run_slither_analysis = _ThreadBackedTask()

    logger.debug(
        "Celery unavailable. Using thread-backed task implementation."
    )