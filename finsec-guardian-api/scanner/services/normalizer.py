"""Normalizer — converts raw analyzer output into the unified finding format."""

from __future__ import annotations

import re

from .analyzers.base import AnalyzerResult

# Regex to strip temporary file-system paths from descriptions.
_TMP_PATH_RE = re.compile(r"(?:\.\./)*(?:/tmp/|tmp/)\S*\.sol\b")

# ---------------------------------------------------------------------------
# Slither severity / confidence maps
# ---------------------------------------------------------------------------
_SLITHER_SEVERITY: dict[str, str] = {
    "High": "high",
    "Medium": "medium",
    "Low": "low",
    "Informational": "info",
    "Optimization": "info",
}
_SLITHER_CONFIDENCE: dict[str, int] = {
    "High": 90,
    "Medium": 65,
    "Low": 40,
}

# ---------------------------------------------------------------------------
# Mythril severity / SWC label maps
# ---------------------------------------------------------------------------
_MYTHRIL_SEVERITY: dict[str, str] = {
    "High": "high",
    "Medium": "medium",
    "Low": "low",
    "Informational": "info",
    "Unknown": "info",
}

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

_MYTHRIL_REMEDIATION: dict[str, str] = {
    "SWC-107": (
        "Apply the checks-effects-interactions pattern. Update state variables "
        "before making any external calls."
    ),
    "SWC-101": (
        "Use Solidity 0.8.x (built-in overflow checks) or OpenZeppelin SafeMath "
        "for earlier versions."
    ),
    "SWC-115": "Replace tx.origin with msg.sender for authorization checks.",
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


class FindingNormalizer:
    """Converts raw analyzer output into the unified finding dict format.

    Each finding dict has the canonical shape consumed by the persistence layer
    and the API serializers::

        {
            "swc_id", "title", "severity", "description", "recommendation",
            "confidence", "line_number", "line_start", "line_end", "column",
            "code_snippet", "tags", "reference_url", "metadata",
        }

    On-chain data (from the Etherscan layer) is normalised into a separate
    ``onchain_data`` dict that rides alongside the finding list — it is NOT
    a finding itself but an enrichment payload::

        {
            "tx_count", "unique_callers", "failure_rate",
            "high_value_flows", "suspicious_patterns",
            "contract_age_days", "reputation", …
        }
    """

    def normalize(self, result: AnalyzerResult) -> list[dict]:
        """Dispatch normalisation based on the ``result.tool`` field."""
        if result.tool == "slither":
            return self.normalize_slither(result.raw_output.get("detectors", []))
        if result.tool == "mythril":
            return self.normalize_mythril(result.raw_output.get("issues", []))
        if result.tool == "echidna":
            return self.normalize_echidna(
                result.raw_output.get("tests", []),
                result.raw_output.get("raw_text"),
                result.raw_output.get("invariant_metadata"),
            )
        # Heuristic layers already produce normalised dicts.
        return result.raw_output.get("findings", [])

    # ------------------------------------------------------------------
    # Slither
    # ------------------------------------------------------------------

    def normalize_slither(self, detectors: list[dict]) -> list[dict]:
        findings: list[dict] = []
        for det in detectors:
            impact = det.get("impact", "Informational")
            confidence_str = det.get("confidence", "Medium")
            elements: list[dict] = det.get("elements", [])

            line_number = line_start = line_end = None
            code_snippet = ""
            column = None

            if elements:
                mapping = elements[0].get("source_mapping", {})
                lines: list[int] = mapping.get("lines", [])
                if lines:
                    line_number = lines[0]
                    line_start = lines[0]
                    line_end = lines[-1]
                column = mapping.get("starting_column")
                code_snippet = elements[0].get("name", "")

            # Slither's first_markdown_element often contains a file
            # reference (e.g. /tmp/finsec_scan_xxx.sol#L12-L20) which
            # is not a useful remediation.  Build a proper recommendation
            # from the detector check type instead.
            raw_rec = det.get("first_markdown_element", "")
            recommendation = (
                self._slither_recommendation(det.get("check", ""))
                or self._sanitize_paths(raw_rec)
            )

            findings.append({
                "swc_id": det.get("swc-id", ""),
                "title": det.get("check", "Slither Finding"),
                "severity": _SLITHER_SEVERITY.get(impact, "info"),
                "description": self._sanitize_paths(det.get("description", "")),
                "recommendation": recommendation,
                "confidence": _SLITHER_CONFIDENCE.get(confidence_str, 50),
                "line_number": line_number,
                "line_start": line_start,
                "line_end": line_end,
                "column": column,
                "code_snippet": code_snippet,
                "tags": [det.get("check", "")],
                "reference_url": det.get("reference", ""),
                "metadata": {
                    "check": det.get("check", ""),
                    "detector_id": det.get("id", ""),
                    "impact": impact,
                    "confidence": confidence_str,
                },
            })
        return findings

    # ------------------------------------------------------------------
    # Mythril
    # ------------------------------------------------------------------

    def normalize_mythril(self, issues: list[dict]) -> list[dict]:
        findings: list[dict] = []
        for issue in issues:
            raw_swc = issue.get("swc_id", "")
            swc_id = (
                f"SWC-{raw_swc}"
                if raw_swc and not str(raw_swc).startswith("SWC")
                else (raw_swc or "")
            )
            title = _SWC_LABELS.get(swc_id, issue.get("title") or "Mythril Finding")
            severity = _MYTHRIL_SEVERITY.get(issue.get("severity", "Medium"), "medium")
            line_number = issue.get("lineno")

            findings.append({
                "swc_id": swc_id,
                "title": title,
                "severity": severity,
                "description": self._sanitize_paths(
                    issue.get("description_long")
                    or issue.get("description_short")
                    or ""
                ),
                "recommendation": _MYTHRIL_REMEDIATION.get(
                    swc_id,
                    "Review the SWC registry entry and apply the recommended mitigation.",
                ),
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
                    "swc_id": swc_id,
                    "function": issue.get("function", ""),
                    "address": issue.get("address"),
                },
            })
        return findings

    # ------------------------------------------------------------------
    # Echidna
    # ------------------------------------------------------------------

    def normalize_echidna(
        self, tests: list[dict], raw_text: str | None = None,
        invariant_metadata: dict | None = None,
    ) -> list[dict]:
        """Convert Echidna test results into normalised findings.

        Echidna is a fuzzer — it reports property *failures*, not static
        analysis detections.  Each failed property becomes a high-severity
        finding; passing properties are summarised as a single info finding.

        When *invariant_metadata* is provided, auto-generated invariant
        failures are tagged with ``auto-invariant`` for downstream
        differentiation from user-written properties.
        """
        import json as _json  # noqa: PLC0415 (avoid top-level for tiny helper)

        findings: list[dict] = []

        auto_names: set[str] = set()
        if invariant_metadata:
            auto_names = set(invariant_metadata.get("generated_names", []))

        for test in tests:
            status = test.get("status", "")
            if status != "failed":
                continue
            name = test.get("name", "unknown")
            is_auto = name in auto_names
            reproducer = test.get("reproducer", [])

            tags = ["echidna", "fuzz", name]
            if is_auto:
                tags.append("auto-invariant")

            findings.append({
                "swc_id": "",
                "title": f"Property Failure: {name}",
                "severity": "high",
                "description": (
                    f"Echidna falsified the property `{name}`. "
                    f"Reproducer: {_json.dumps(reproducer)}"
                ),
                "recommendation": (
                    "Review the failing property. Ensure invariants hold "
                    "for all reachable states and input sequences."
                ),
                "confidence": 85,
                "line_number": None,
                "line_start": None,
                "line_end": None,
                "column": None,
                "code_snippet": "",
                "tags": tags,
                "reference_url": "",
                "metadata": {
                    "tool": "echidna",
                    "property": name,
                    "reproducer": reproducer,
                    "auto_generated": is_auto,
                },
            })

        # If no failures, emit an info note so the scan still shows Echidna ran.
        if not findings:
            msg = "All Echidna properties passed (no failures found)."
            if raw_text:
                # Clean up Docker/tool error messages — don't expose them
                # in the user-facing report.
                if "could not be found" in raw_text or "docker" in raw_text.lower():
                    msg = "Echidna analysis was not available in this environment."
                else:
                    msg = raw_text[:500]

            inv_note = ""
            if invariant_metadata and invariant_metadata.get("count", 0) > 0:
                inv_note = (
                    f" ({invariant_metadata['count']} auto-generated "
                    f"invariants tested)"
                )

            findings.append({
                "swc_id": "",
                "title": "Echidna Result",
                "severity": "info",
                "description": msg + inv_note,
                "recommendation": "",
                "confidence": 100,
                "line_number": None,
                "line_start": None,
                "line_end": None,
                "column": None,
                "code_snippet": "",
                "tags": ["echidna", "fuzz"],
                "reference_url": "",
                "metadata": {
                    "tool": "echidna",
                    "invariant_metadata": invariant_metadata,
                },
            })

        return findings

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _sanitize_paths(text: str) -> str:
        """Strip temporary file-system paths from finding descriptions."""
        return _TMP_PATH_RE.sub("<source>", text) if text else text

    # Slither detector check → human-readable remediation text.
    _SLITHER_RECOMMENDATIONS: dict[str, str] = {
        "reentrancy-eth": (
            "Apply the checks-effects-interactions pattern: update all state "
            "variables before making external calls. Consider using "
            "OpenZeppelin's ReentrancyGuard."
        ),
        "reentrancy-no-eth": (
            "Update state variables before making external calls, even when "
            "no Ether is transferred."
        ),
        "arbitrary-send-eth": (
            "Restrict Ether-sending functions with access control (e.g., "
            "onlyOwner). Never allow arbitrary users to drain contract funds."
        ),
        "suicidal": (
            "Guard selfdestruct with strict access control or remove it."
        ),
        "unprotected-upgrade": (
            "Restrict upgrade functions to authorized roles only."
        ),
        "controlled-delegatecall": (
            "Avoid delegatecall to user-supplied addresses. Whitelist "
            "permitted targets."
        ),
        "solc-version": (
            "Pin the Solidity compiler to a specific recent version "
            "(e.g., 0.8.20) to avoid known bugs in older releases."
        ),
        "low-level-calls": (
            "Prefer Solidity's transfer() or use call() with explicit "
            "return-value checks and gas limits."
        ),
        "calls-loop": (
            "Avoid external calls inside loops; use pull-payment patterns."
        ),
        "tx-origin": (
            "Replace tx.origin with msg.sender for authorization checks."
        ),
        "unchecked-lowlevel": (
            "Always check the return value of low-level calls."
        ),
    }

    @classmethod
    def _slither_recommendation(cls, check: str) -> str:
        """Return a human-readable recommendation for a Slither detector."""
        return cls._SLITHER_RECOMMENDATIONS.get(check, "")

    # ------------------------------------------------------------------
    # On-chain data normalisation (Etherscan layer)
    # ------------------------------------------------------------------

    @staticmethod
    def normalize_onchain(insights, reputation_result=None) -> dict:
        """Convert ``OnChainInsights`` + ``ReputationResult`` into the
        unified ``onchain_data`` dict that rides alongside findings.

        This is intentionally *not* a finding — it is a separate enrichment
        payload attached to the scan result.
        """
        from .etherscan.analyzer import OnChainInsights  # noqa: PLC0415
        from .etherscan.reputation import ReputationResult  # noqa: PLC0415

        if not isinstance(insights, OnChainInsights):
            return {}

        data: dict = {
            "address": insights.address,
            "tx_count": insights.tx_count,
            "unique_callers": insights.unique_callers,
            "unique_receivers": insights.unique_receivers,
            "failed_tx_count": insights.failed_tx_count,
            "failure_rate": insights.failure_rate,
            "total_value_eth": insights.total_value_eth,
            "high_value_tx_count": insights.high_value_tx_count,
            "high_value_flows": insights.high_value_flows[:10],
            "repeated_callers": dict(list(insights.repeated_callers.items())[:10]),
            "suspicious_patterns": insights.suspicious_patterns,
            "top_methods": [
                {"method_id": m, "count": c} for m, c in insights.top_methods
            ],
            "token_transfer_count": insights.token_transfer_count,
            "unique_tokens": insights.unique_tokens,
            "event_log_count": insights.event_log_count,
            "contract_age_days": insights.contract_age_days,
            "first_tx_timestamp": insights.first_tx_timestamp,
            "last_tx_timestamp": insights.last_tx_timestamp,
            "warnings": insights.warnings,
        }

        if isinstance(reputation_result, ReputationResult):
            data["reputation"] = {
                "score": reputation_result.reputation_score,
                "verdict": reputation_result.verdict,
                "factors": reputation_result.factors,
                "risk_adjustment": reputation_result.risk_adjustment,
            }

        return data

    @staticmethod
    def enrich_findings_with_onchain(
        findings: list[dict], insights,
    ) -> list[dict]:
        """Annotate existing findings with on-chain context when relevant.

        For example, a reentrancy finding gets a note about abnormal
        withdraw patterns if the on-chain data supports it.
        """
        from .etherscan.analyzer import OnChainInsights  # noqa: PLC0415

        if not isinstance(insights, OnChainInsights) or not insights.suspicious_patterns:
            return findings

        # Build a lookup of relevant enrichment strings.
        withdraw_pattern = next(
            (p for p in insights.suspicious_patterns if "withdraw" in p.lower()),
            None,
        )
        repeated_pattern = next(
            (p for p in insights.suspicious_patterns if "repeated" in p.lower()
             or "automated" in p.lower()),
            None,
        )

        for f in findings:
            title_lower = (f.get("title") or "").lower()
            desc = f.get("description", "")

            # Enrich reentrancy findings with withdraw data
            if "reentrancy" in title_lower and withdraw_pattern:
                f["description"] = (
                    f"{desc}\n\n**On-chain context:** {withdraw_pattern}"
                )
                f.setdefault("tags", []).append("onchain-enriched")

            # Enrich access-control findings with caller pattern data
            if ("access" in title_lower or "unprotected" in title_lower) and repeated_pattern:
                f["description"] = (
                    f"{desc}\n\n**On-chain context:** {repeated_pattern}"
                )
                f.setdefault("tags", []).append("onchain-enriched")

        return findings

    @staticmethod
    def tag_findings(findings: list[dict], tool: str) -> list[dict]:
        """Stamp every finding with ``metadata["tool"]`` and a tag."""
        for f in findings:
            f.setdefault("metadata", {})["tool"] = tool
            if tool not in f.get("tags", []):
                f.setdefault("tags", []).append(tool)
        return findings
