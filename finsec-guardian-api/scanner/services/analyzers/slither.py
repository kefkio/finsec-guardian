"""Slither static-analysis analyzer — runs Slither in its own isolated venv."""

import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path

from .base import AnalyzerResult

logger = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # finsec-guardian-api/
_SLITHER_PYTHON = _BASE_DIR / "venv-slither" / "bin" / "python"
_SLITHER_RUNNER = Path(__file__).resolve().parent.parent / "_slither_runner_script.py"


class SlitherError(Exception):
    """Raised when Slither analysis cannot be completed."""


class SlitherAnalyzer:
    """Runs Slither and returns raw detector output."""

    def analyze(self, source_code: str, contract_name: str | None = None) -> AnalyzerResult:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".sol", prefix="finsec_scan_",
            delete=False, encoding="utf-8",
        ) as tmp:
            tmp.write(source_code)
            tmp_path = tmp.name

        try:
            return self._run(tmp_path, contract_name)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _run(self, sol_file: str, contract_name: str | None) -> AnalyzerResult:
        logger.info(
            "Running Slither on %s (contract=%s) via venv-slither",
            sol_file, contract_name or "unknown",
        )

        if not _SLITHER_PYTHON.exists():
            raise SlitherError(
                f"venv-slither not found at {_SLITHER_PYTHON}. "
                "Run: python3 -m venv venv-slither && venv-slither/bin/pip install -e slither/"
            )

        try:
            proc = subprocess.run(
                [str(_SLITHER_PYTHON), str(_SLITHER_RUNNER), sol_file],
                capture_output=True, text=True, timeout=120,
            )
        except subprocess.TimeoutExpired as exc:
            raise SlitherError("Slither analysis timed out after 120 seconds") from exc
        except Exception as exc:
            raise SlitherError(f"Failed to launch Slither subprocess: {exc}") from exc

        stdout = proc.stdout.strip()
        try:
            data = json.loads(stdout.splitlines()[-1]) if stdout else {}
        except (json.JSONDecodeError, IndexError) as exc:
            raise SlitherError(
                f"Slither runner produced invalid JSON: {exc}\nstdout={stdout[:500]}"
            ) from exc

        if not data.get("success"):
            raise SlitherError(
                f"Slither analysis failed: {data.get('error', 'unknown error')}"
            )

        return AnalyzerResult(
            success=True,
            raw_output={"detectors": data.get("detectors", [])},
            stderr=proc.stderr[:2000] if proc.stderr else "",
            tool="slither",
        )
