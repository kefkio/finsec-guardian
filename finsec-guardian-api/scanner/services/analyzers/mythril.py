"""Mythril symbolic-execution analyzer — runs Mythril in its own isolated venv."""

import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path

from .base import AnalyzerResult

logger = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # finsec-guardian-api/
_MYTHRIL_PYTHON = _BASE_DIR / "venv-mythril" / "bin" / "python"
_MYTHRIL_RUNNER = Path(__file__).resolve().parent.parent / "_mythril_runner_script.py"


class MythrilError(Exception):
    """Raised when a Mythril analysis cannot be completed."""


class MythrilAnalyzer:
    """Runs Mythril and returns raw issue output."""

    DEFAULT_TIMEOUT: int = 60

    def analyze(
        self,
        source_code: str,
        contract_name: str | None = None,
        timeout: int | None = None,
    ) -> AnalyzerResult:
        if not _MYTHRIL_PYTHON.exists():
            raise MythrilError(
                f"venv-mythril not found at {_MYTHRIL_PYTHON}. "
                "Run: python3 -m venv venv-mythril && venv-mythril/bin/pip install mythril"
            )

        timeout = timeout or self.DEFAULT_TIMEOUT

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".sol", prefix="finsec_mythril_",
            delete=False, encoding="utf-8",
        ) as tmp:
            tmp.write(source_code)
            tmp_path = tmp.name

        try:
            return self._run(tmp_path, contract_name or "Contract", timeout)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _run(self, sol_file: str, contract_name: str, timeout: int) -> AnalyzerResult:
        logger.info(
            "Running Mythril on %s (contract=%s, timeout=%ds)",
            sol_file, contract_name, timeout,
        )

        try:
            proc = subprocess.run(
                [str(_MYTHRIL_PYTHON), str(_MYTHRIL_RUNNER), sol_file, str(timeout)],
                capture_output=True, text=True, timeout=timeout + 30,
            )
        except subprocess.TimeoutExpired:
            logger.warning("Mythril subprocess timed out for %s", sol_file)
            return AnalyzerResult(
                success=False, raw_output={},
                error="Mythril timed out", tool="mythril",
            )
        except Exception as exc:
            logger.warning("Mythril subprocess failed: %s", exc)
            return AnalyzerResult(
                success=False, raw_output={},
                error=str(exc), tool="mythril",
            )

        if not proc.stdout.strip():
            err = proc.stderr.strip() or "Mythril produced no output"
            logger.warning("Mythril empty output for %s: %s", sol_file, err)
            return AnalyzerResult(
                success=False, raw_output={}, error=err, tool="mythril",
            )

        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            logger.warning("Mythril JSON parse error: %s", exc)
            return AnalyzerResult(
                success=False, raw_output={},
                error=f"Invalid JSON: {exc}", tool="mythril",
            )

        if not data.get("success"):
            return AnalyzerResult(
                success=False, raw_output={},
                error=data.get("error", "Unknown error"), tool="mythril",
            )

        return AnalyzerResult(
            success=True,
            raw_output={"issues": data.get("issues", [])},
            tool="mythril",
        )
