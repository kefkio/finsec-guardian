"""
Compatibility shim consumed by views.py.

Provides ``run_slither_analysis`` with two call patterns:

    # Sync (trigger_scan action) — called with raw source code string:
    result_dict = run_slither_analysis(source_code)

    # Async (perform_create / quick_scan) — called with a ScanJob PK:
    run_slither_analysis.delay(job_id)

When Celery is available the task is registered as a shared_task so that
``run_slither_analysis.delay(...)`` dispatches to a worker.
When Celery is NOT available a lightweight thread-based fallback is used so
that the call signature stays identical.
"""

import logging
import threading

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Try to register as a Celery task; fall back to a threading shim.
# ---------------------------------------------------------------------------

def _run_analysis_impl(source_code_or_job_id):
    """
    Dispatch logic shared by both the Celery task and the thread fallback.

    - int / str-that-is-a-number: treated as a ScanJob PK → full lifecycle.
    - str (Solidity source):       sync analysis, returns raw Slither JSON dict.
    """
    from scanner.services import SlitherService, SlitherError  # noqa: PLC0415

    service = SlitherService()

    # Background job path: called with a ScanJob PK.
    if isinstance(source_code_or_job_id, int) or (
        isinstance(source_code_or_job_id, str)
        and source_code_or_job_id.isdigit()
    ):
        job_id = int(source_code_or_job_id)
        service.analyze_scan_job(job_id)
        return {}

    # Sync path: called with raw Solidity source code.
    try:
        result = service.run_analysis(source_code_or_job_id)
        return result.get("raw_output", {})
    except SlitherError as exc:
        logger.error("Slither error: %s", exc)
        return {"error": str(exc)}


try:
    from celery import shared_task  # type: ignore[import-untyped]

    @shared_task(name="scanner.run_slither_analysis", bind=False)
    def run_slither_analysis(source_code_or_job_id):
        """Celery task: run Slither analysis (sync or job-based)."""
        return _run_analysis_impl(source_code_or_job_id)

    logger.debug("run_slither_analysis registered as a Celery shared_task.")

except ImportError:
    # -----------------------------------------------------------------
    # Celery not installed — provide a callable with a `.delay()` method
    # that dispatches to a daemon thread so callers don't block.
    # -----------------------------------------------------------------

    class _ThreadBackedTask:
        """Minimal Celery-task look-alike backed by threading.Thread."""

        def __call__(self, source_code_or_job_id):
            return _run_analysis_impl(source_code_or_job_id)

        def delay(self, *args, **kwargs):
            """Fire-and-forget: run in a background daemon thread."""
            t = threading.Thread(
                target=_run_analysis_impl,
                args=args,
                kwargs=kwargs,
                daemon=True,
            )
            t.start()
            logger.debug(
                "run_slither_analysis dispatched to background thread (tid=%s).",
                t.ident,
            )
            return t  # return the Thread so callers can .join() if needed

    run_slither_analysis = _ThreadBackedTask()

    logger.debug(
        "Celery not found — run_slither_analysis uses thread-based fallback."
    )
