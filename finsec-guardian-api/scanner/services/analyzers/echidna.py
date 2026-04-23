"""Echidna property-based fuzzing analyzer (Docker-based).

Runs the Echidna fuzzer directly via ``docker run`` — no intermediate runner
script, no Haskell toolchain, and no PATH pollution on the host.

Docker invocation uses ``--format json`` so output is structured JSON rather
than free-form text, eliminating fragile stdout parsing.

Security hardening:
  • ``--network none``  — no external communication
  • ``--read-only``     — immutable root filesystem
  • ``--tmpfs /tmp``    — writable scratch (noexec, nosuid)
  • ``--memory 1g``     — memory cap
  • ``--cpus 2``        — CPU cap
  • ``--user uid:gid``  — runs as the current non-root user
  • bind-mount is read-only
"""

import json
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings

from .base import AnalyzerResult
from scanner.services.invariants import InvariantGenerator, InvariantInjector

logger = logging.getLogger(__name__)

_DEFAULT_DOCKER_IMAGE = "ghcr.io/crytic/echidna/echidna:v2.2.5"


class EchidnaError(Exception):
    """Raised when an Echidna analysis cannot be completed."""


class EchidnaAnalyzer:
    """Runs Echidna fuzzer inside Docker and returns raw test results.

    The Docker image is resolved from:
        1. ``settings.ECHIDNA_DOCKER_IMAGE``
        2. Built-in default: ghcr.io/crytic/echidna/echidna:v2.2.5

    Pre-requisites:
        • Docker Engine installed and the current user in the ``docker`` group.
        • Image pulled: ``bash setup_echidna.sh``
    """

    DEFAULT_TIMEOUT: int = 120

    def __init__(self) -> None:
        self.generator = InvariantGenerator()
        self.injector = InvariantInjector()

    def _resolve_docker_image(self) -> str:
        return getattr(settings, "ECHIDNA_DOCKER_IMAGE", _DEFAULT_DOCKER_IMAGE)

    @staticmethod
    def _assert_docker_available() -> None:
        """Raise ``EchidnaError`` early if Docker is not on PATH."""
        if not shutil.which("docker"):
            raise EchidnaError(
                "Docker not found on PATH. Install Docker Engine and ensure "
                "your user is in the docker group: "
                "sudo usermod -aG docker $USER && newgrp docker"
            )

    def analyze(
        self,
        source_code: str,
        contract_name: str | None = None,
        timeout: int | None = None,
    ) -> AnalyzerResult:
        self._assert_docker_available()

        docker_image = self._resolve_docker_image()
        timeout = timeout or getattr(settings, "ECHIDNA_TIMEOUT", self.DEFAULT_TIMEOUT)

        # --- Auto-generate and inject invariants ---
        invariant_result = self.generator.generate(source_code)
        if invariant_result["count"] > 0:
            source_code = self.injector.inject(source_code, invariant_result["code"])
            logger.info(
                "Injected %d auto-generated invariants: %s",
                invariant_result["count"],
                ", ".join(invariant_result["names"]),
            )

        temp_dir = tempfile.mkdtemp(prefix="finsec_echidna_")
        sol_path = Path(temp_dir) / "Contract.sol"

        try:
            sol_path.write_text(source_code, encoding="utf-8")
            result = self._run(temp_dir, sol_path.name, docker_image, timeout)
            result.raw_output["invariant_metadata"] = {
                "count": invariant_result["count"],
                "generated_names": invariant_result["names"],
            }
            return result
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _run(
        self,
        host_dir: str,
        filename: str,
        docker_image: str,
        timeout: int,
    ) -> AnalyzerResult:
        logger.info(
            "Running Echidna on %s/%s (image=%s, timeout=%ds)",
            host_dir, filename, docker_image, timeout,
        )

        uid = os.getuid()
        gid = os.getgid()
        container_workdir = "/work"

        cmd = [
            "docker", "run", "--rm",
            "--user", f"{uid}:{gid}",
            "--network", "none",
            "--read-only",
            "--tmpfs", "/tmp:rw,noexec,nosuid",
            "--memory", "1g",
            "--cpus", "2",
            "-v", f"{host_dir}:{container_workdir}:ro",
            "-w", container_workdir,
            docker_image,
            filename,
            "--format", "json",
            "--timeout", str(timeout),
        ]

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True, text=True,
                timeout=timeout + 60,  # OS-level timeout above Echidna's own
            )
        except subprocess.TimeoutExpired:
            logger.warning("Echidna Docker container timed out for %s", filename)
            return AnalyzerResult(
                success=False, raw_output={},
                error="Echidna timed out", tool="echidna",
            )
        except FileNotFoundError:
            raise EchidnaError(
                "Docker binary not found. Install Docker Engine and run: "
                "bash setup_echidna.sh"
            )
        except Exception as exc:
            return AnalyzerResult(
                success=False, raw_output={},
                error=str(exc), tool="echidna",
            )

        stdout = proc.stdout.strip()

        # Docker-level errors (image missing, permission denied) go to stderr.
        if proc.returncode != 0 and not stdout:
            stderr_tail = (proc.stderr or "")[-1000:]
            if "permission denied" in stderr_tail.lower():
                raise EchidnaError(
                    "Docker permission denied. Add your user to the docker "
                    "group: sudo usermod -aG docker $USER && newgrp docker"
                )
            if "not found" in stderr_tail.lower() or "manifest unknown" in stderr_tail.lower():
                raise EchidnaError(
                    f"Docker image {docker_image} not found. "
                    "Run: bash setup_echidna.sh"
                )
            return AnalyzerResult(
                success=False, raw_output={},
                error=stderr_tail or "Echidna produced no output",
                tool="echidna",
            )

        if not stdout:
            if proc.returncode == 0:
                return AnalyzerResult(
                    success=True, raw_output={"tests": []}, tool="echidna",
                )
            return AnalyzerResult(
                success=False, raw_output={},
                error=proc.stderr[-1000:] if proc.stderr else "Echidna produced no output",
                tool="echidna",
            )

        try:
            report = json.loads(stdout)
        except json.JSONDecodeError:
            # Echidna occasionally emits non-JSON; capture for inspection.
            return AnalyzerResult(
                success=True,
                raw_output={"tests": [], "raw_text": stdout[:2000]},
                tool="echidna",
            )

        tests = report.get("tests", []) if isinstance(report, dict) else []
        campaign = report.get("campaign", {}) if isinstance(report, dict) else {}

        return AnalyzerResult(
            success=True,
            raw_output={
                "tests": tests,
                "campaign": campaign,
            },
            tool="echidna",
        )
