"""Mythril symbolic-execution service — runs Mythril in its own isolated venv."""

import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path

# Paths to the isolated venv and the runner script.
_BASE_DIR = Path(__file__).resolve().parent.parent.parent  # finsec-guardian-api/
_MYTHRIL_PYTHON = _BASE_DIR / "venv-mythril" / "bin" / "python"
_MYTHRIL_RUNNER = Path(__file__).resolve().parent / "_mythril_runner_script.py"

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Severity / SWC mappings
# ---------------------------------------------------------------------------

# Mythril reports issues with a numeric SWC ID and a named severity.
_SEVERITY_MAP: dict[str, str] = {
    "High": "high",
    "Medium": "medium",
    "Low": "low",
    "Informational": "info",
    "Unknown": "info",
}

# SWC ID → human-readable category label used for FindingCategory.name
_SWC_LABELS: dict[str, str] = {
    "SWC-100": "Function Default Visibility",
    "SWC-101": "Integer Overflow and Underflow",
    "SWC-102": "Outdated Compiler Version",
    "SWC-103": "Floating Pragma",
    "SWC-104": "Unchecked Call Return Value",
    "SWC-105": "Unprotected Ether Withdrawal",
    "SWC-106": "Unprotected SELFDESTRUCT Instruction",
    "SWC-107": "Reentrancy",
    "SWC-108": "State Variable Default Visibility",
    "SWC-109": "Uninitialized Storage Pointer",
    "SWC-110": "Assert Violation",
    "SWC-111": "Use of Deprecated Solidity Functions",
    "SWC-112": "Delegatecall to Untrusted Callee",
    "SWC-113": "DoS with Failed Call",
    "SWC-114": "Transaction Order Dependence",
    "SWC-115": "Authorization through tx.origin",
    "SWC-116": "Block values as a Proxy for Time",
    "SWC-117": "Signature Malleability",
    "SWC-118": "Incorrect Constructor Name",
    "SWC-119": "Shadowing State Variables",
    "SWC-120": "Weak Sources of Randomness",
    "SWC-121": "Missing Protection against Signature Replay Attacks",
    "SWC-122": "Lack of Proper Signature Verification",
    "SWC-123": "Requirement Violation",
    "SWC-124": "Write to Arbitrary Storage Location",
    "SWC-125": "Incorrect Inheritance Order",
    "SWC-126": "Insufficient Gas Griefing",
    "SWC-127": "Arbitrary Jump with Function Type Variable",
    "SWC-128": "DoS With Block Gas Limit",
    "SWC-129": "Typographical Error",
    "SWC-130": "Right-To-Left-Override Control Character Usage",
    "SWC-131": "Presence of Unused Variables",
    "SWC-132": "Unexpected Ether Balance",
    "SWC-133": "Hash Collisions With Multiple Variable Length Arguments",
    "SWC-134": "Message call with hardcoded gas amount",
    "SWC-135": "Code With No Effects",
    "SWC-136": "Unencrypted Private Data On-Chain",
}


class MythrilError(Exception):
    """Raised when a Mythril analysis cannot be completed."""


class MythrilService:
    """
    Service wrapper around the Mythril symbolic-execution engine.

    All public methods return a result dict identical in shape to
    ``SlitherService``'s return value so that callers can merge the two lists:

        {
            "success": bool,
            "findings": list[dict],   # normalised Finding-compatible dicts
            "error": str | None,
        }

    Each finding's ``metadata["tool"]`` is set to ``"mythril"`` so that the
    UI and serialisers can display the originating engine.
    """

    # Maximum wall-clock seconds to allow Mythril to run per contract.
    # Mythril's symbolic execution can run indefinitely; cap it early.
    DEFAULT_TIMEOUT: int = 60  # seconds

    def run_analysis(
        self,
        source_code: str,
        contract_name: str | None = None,
        timeout: int | None = None,
    ) -> dict:
        """
        Analyse a Solidity source string with Mythril.

        Writes the source to a temporary ``.sol`` file, invokes Mythril via
        the isolated ``venv-mythril`` subprocess, then cleans up.

        Args:
            source_code:   Raw Solidity source.
            contract_name: Optional label for log messages.
            timeout:       Seconds before Mythril is aborted (default 60).

        Returns:
            Result dict (see class docstring).

        Raises:
            MythrilError: if the venv-mythril runner is missing.
        """
        if not _MYTHRIL_PYTHON.exists():
            raise MythrilError(
                f"venv-mythril not found at {_MYTHRIL_PYTHON}. "
                "Run: python3 -m venv venv-mythril && venv-mythril/bin/pip install mythril"
            )

        timeout = timeout or self.DEFAULT_TIMEOUT

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".sol",
            prefix="finsec_mythril_",
            delete=False,
            encoding="utf-8",
        ) as tmp:
            tmp.write(source_code)
            tmp_path = tmp.name

        try:
            return self._run_mythril(tmp_path, contract_name or "Contract", timeout)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_mythril(self, sol_file: str, contract_name: str, timeout: int) -> dict:
        logger.info(
            "Running Mythril on %s (contract=%s, timeout=%ds)",
            sol_file,
            contract_name,
            timeout,
        )

        try:
            proc = subprocess.run(
                [str(_MYTHRIL_PYTHON), str(_MYTHRIL_RUNNER), sol_file, str(timeout)],
                capture_output=True,
                text=True,
                timeout=timeout + 30,  # outer OS timeout slightly above Mythril's own
            )
        except subprocess.TimeoutExpired:
            logger.warning("Mythril subprocess timed out for %s", sol_file)
            return {"success": False, "findings": [], "error": "Mythril timed out"}
        except Exception as exc:
            logger.warning("Mythril subprocess failed: %s", exc)
            return {"success": False, "findings": [], "error": str(exc)}

        if not proc.stdout.strip():
            err = proc.stderr.strip() or "Mythril produced no output"
            logger.warning("Mythril empty output for %s: %s", sol_file, err)
            return {"success": False, "findings": [], "error": err}

        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            logger.warning("Mythril JSON parse error: %s", exc)
            return {"success": False, "findings": [], "error": f"Invalid JSON: {exc}"}

        if not data.get("success"):
            return {"success": False, "findings": [], "error": data.get("error", "Unknown error")}

        findings = self._parse_issues(data.get("issues", []))
        logger.info("Mythril found %d issue(s)", len(findings))
        return {"success": True, "findings": findings, "error": None}

    def _parse_issues(self, issues: list[dict]) -> list[dict]:
        """Convert Mythril issue dicts (from runner JSON) to normalised finding dicts."""
        findings: list[dict] = []

        for issue in issues:
            raw_swc = issue.get("swc_id", "")
            swc_id = f"SWC-{raw_swc}" if raw_swc and not str(raw_swc).startswith("SWC") else (raw_swc or "")
            title = _SWC_LABELS.get(swc_id, issue.get("title") or "Mythril Finding")
            severity = _SEVERITY_MAP.get(issue.get("severity", "Medium"), "medium")

            line_number = issue.get("lineno")

            findings.append(
                {
                    "swc_id": swc_id,
                    "title": title,
                    "severity": severity,
                    "description": issue.get("description_long") or issue.get("description_short") or "",
                    "recommendation": self._recommendation_for(swc_id),
                    "confidence": 70,
                    "line_number": line_number,
                    "line_start": line_number,
                    "line_end": line_number,
                    "column": None,
                    "code_snippet": issue.get("code", ""),
                    "tags": [swc_id, "mythril"] if swc_id else ["mythril"],
                    "reference_url": (
                        f"https://swcregistry.io/docs/{swc_id}" if swc_id else ""
                    ),
                    "metadata": {
                        "tool": "mythril",
                        "swc_id": swc_id,
                        "function": issue.get("function", ""),
                        "address": issue.get("address"),
                    },
                }
            )

        return findings

    @staticmethod
    def _recommendation_for(swc_id: str) -> str:
        """Return a brief remediation hint for well-known SWC IDs."""
        _REMEDIATION: dict[str, str] = {
            "SWC-107": (
                "Apply the checks-effects-interactions pattern. Update state variables "
                "before making any external calls."
            ),
            "SWC-101": (
                "Use Solidity 0.8.x (built-in overflow checks) or OpenZeppelin SafeMath "
                "for earlier versions."
            ),
            "SWC-115": (
                "Replace tx.origin with msg.sender for authorization checks."
            ),
            "SWC-112": (
                "Avoid delegatecall to untrusted addresses. If required, whitelist "
                "permitted callee addresses."
            ),
            "SWC-105": (
                "Restrict Ether withdrawal functions with proper access control "
                "(e.g., onlyOwner modifier)."
            ),
            "SWC-106": (
                "Guard SELFDESTRUCT with strict access control or remove it entirely "
                "if not required."
            ),
            "SWC-120": (
                "Do not use block.timestamp, blockhash, or block.difficulty as entropy "
                "sources. Use a verifiable randomness oracle (e.g., Chainlink VRF)."
            ),
        }
        return _REMEDIATION.get(swc_id, "Review the SWC registry entry and apply the recommended mitigation.")
