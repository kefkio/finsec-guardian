from unittest.mock import patch

from scanner import slither_runner


def test_run_analysis_impl_uses_orchestrator_for_job_ids():
    class FakeOrchestrator:
        def __init__(self):
            self.job_ids = []

        def run_scan_job(self, job_id):
            self.job_ids.append(job_id)
            return {"success": True, "job_id": job_id}

    fake_orchestrator = FakeOrchestrator()

    with patch("scanner.services.orchestrator.ScanOrchestrator", return_value=fake_orchestrator):
        result = slither_runner._run_analysis_impl(42)

    assert result["success"] is True
    assert result["job_id"] == 42
    assert result["status"] == "queued"
    assert fake_orchestrator.job_ids == [42]
