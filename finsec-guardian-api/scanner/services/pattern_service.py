"""Layer 3 — Advanced Pattern & Behavioral Detection Service.

Performs source-level analysis beyond what Slither detectors cover:
    - Compound vulnerability detection (reentrancy + access control, etc.)
    - Token-specific risks: honeypot patterns, hidden mints, fee manipulation
    - Business-logic anti-patterns: timestamp dependence, tx.origin usage,
      selfdestruct exposure, unchecked delegatecall, storage collision risk
    - Dangerous function visibility / shadowing
"""

import logging
import re

logger = logging.getLogger(__name__)


class PatternDetectionService:
    """Layer 3: regex & heuristic pattern detection on Solidity source."""

    # Each detector is a (method_name, enabled) pair — easy to extend.
    _DETECTORS = [
        "_detect_honeypot_patterns",
        "_detect_hidden_mint",
        "_detect_fee_manipulation",
        "_detect_selfdestruct",
        "_detect_delegatecall",
        "_detect_tx_origin",
        "_detect_timestamp_dependence",
        "_detect_unchecked_return",
        "_detect_assembly_usage",
        "_detect_storage_collision_risk",
        "_detect_reentrancy_with_state_change",
    ]

    def run_analysis(self, source_code: str, **_kwargs) -> dict:
        findings: list[dict] = []
        lines = source_code.splitlines()

        for detector_name in self._DETECTORS:
            detector = getattr(self, detector_name, None)
            if detector:
                try:
                    findings.extend(detector(source_code, lines))
                except Exception:
                    logger.exception("Pattern detector %s failed", detector_name)
        return {"success": True, "findings": findings, "error": None}

    # -----------------------------------------------------------------
    # Detectors
    # -----------------------------------------------------------------

    def _detect_honeypot_patterns(self, source: str, lines: list[str]) -> list[dict]:
        """Detect approve() override that silently blocks transfers."""
        findings: list[dict] = []
        # approve that always reverts or returns false
        pattern = re.compile(
            r'function\s+approve\s*\([^)]*\)[^{]*\{[^}]*(?:revert|return\s+false)',
            re.DOTALL,
        )
        for m in pattern.finditer(source):
            ln = source[:m.start()].count("\n") + 1
            findings.append(self._make(
                title="Potential Honeypot: approve() Override",
                severity="high",
                description=(
                    "The approve() function appears to revert or return false "
                    "unconditionally, which would trap user funds."
                ),
                recommendation="Ensure approve() correctly updates allowances.",
                confidence=75,
                tags=["layer3", "honeypot", "token"],
                line_number=ln,
                code_snippet=self._snippet(lines, ln),
            ))
        return findings

    def _detect_hidden_mint(self, source: str, lines: list[str]) -> list[dict]:
        findings: list[dict] = []
        # _mint called outside of constructor / designated mint function
        mint_calls = list(re.finditer(r'\b_mint\s*\(', source))
        if not mint_calls:
            return findings
        for m in mint_calls:
            ln = source[:m.start()].count("\n") + 1
            # Check if inside a function that looks like a backdoor
            context_start = max(0, m.start() - 300)
            context = source[context_start:m.start()]
            if re.search(r'function\s+(?!constructor|mint)\w+', context):
                findings.append(self._make(
                    title="Hidden Mint Capability",
                    severity="high",
                    description=(
                        "_mint() is called inside a non-standard function. "
                        "This could allow the owner to inflate supply."
                    ),
                    recommendation=(
                        "Restrict minting to clearly documented functions "
                        "with proper access control and event emission."
                    ),
                    confidence=60,
                    tags=["layer3", "hidden-mint", "token"],
                    line_number=ln,
                    code_snippet=self._snippet(lines, ln),
                ))
        return findings

    def _detect_fee_manipulation(self, source: str, lines: list[str]) -> list[dict]:
        findings: list[dict] = []
        # Mutable fee / tax variable changed outside constructor
        fee_vars = re.findall(r'uint\d*\s+(?:public\s+)?(\w*(?:fee|tax|rate)\w*)', source, re.IGNORECASE)
        for var in fee_vars:
            setter_pattern = re.compile(rf'{re.escape(var)}\s*=', re.IGNORECASE)
            for m in setter_pattern.finditer(source):
                ln = source[:m.start()].count("\n") + 1
                # Skip if inside constructor
                before = source[:m.start()]
                if "constructor" in before[max(0, len(before) - 500):]:
                    continue
                findings.append(self._make(
                    title=f"Mutable Fee Variable: {var}",
                    severity="medium",
                    description=(
                        f"Variable `{var}` can be changed after deployment. "
                        "This may allow unexpected fee increases."
                    ),
                    recommendation=(
                        "Consider capping fees with a constant MAX or "
                        "making the variable immutable."
                    ),
                    confidence=65,
                    tags=["layer3", "fee-manipulation", "token"],
                    line_number=ln,
                    code_snippet=self._snippet(lines, ln),
                ))
                break  # one finding per variable is sufficient
        return findings

    def _detect_selfdestruct(self, source: str, lines: list[str]) -> list[dict]:
        findings: list[dict] = []
        for m in re.finditer(r'\bselfdestruct\s*\(', source):
            ln = source[:m.start()].count("\n") + 1
            findings.append(self._make(
                title="Use of selfdestruct",
                severity="high",
                description=(
                    "selfdestruct can permanently remove the contract and "
                    "force-send Ether. Post-Dencun (EIP-6780) its semantics "
                    "changed, but it remains dangerous."
                ),
                recommendation="Remove selfdestruct or use upgradeable proxy patterns.",
                confidence=90,
                tags=["layer3", "selfdestruct", "SWC-106"],
                swc_id="SWC-106",
                line_number=ln,
                code_snippet=self._snippet(lines, ln),
            ))
        return findings

    def _detect_delegatecall(self, source: str, lines: list[str]) -> list[dict]:
        findings: list[dict] = []
        for m in re.finditer(r'\.delegatecall\s*\(', source):
            ln = source[:m.start()].count("\n") + 1
            findings.append(self._make(
                title="Delegatecall Usage",
                severity="high",
                description=(
                    "delegatecall executes external code in the context of "
                    "the calling contract. If the target is attacker-"
                    "controlled, storage can be overwritten."
                ),
                recommendation=(
                    "Ensure delegatecall targets are immutable or properly "
                    "access-controlled."
                ),
                confidence=80,
                tags=["layer3", "delegatecall", "SWC-112"],
                swc_id="SWC-112",
                line_number=ln,
                code_snippet=self._snippet(lines, ln),
            ))
        return findings

    def _detect_tx_origin(self, source: str, lines: list[str]) -> list[dict]:
        findings: list[dict] = []
        for m in re.finditer(r'\btx\.origin\b', source):
            ln = source[:m.start()].count("\n") + 1
            findings.append(self._make(
                title="tx.origin Used for Authorization",
                severity="medium",
                description=(
                    "tx.origin returns the original sender of a transaction. "
                    "Using it for access control is vulnerable to phishing "
                    "attacks via malicious intermediary contracts."
                ),
                recommendation="Use msg.sender instead of tx.origin.",
                confidence=85,
                tags=["layer3", "tx-origin", "SWC-115"],
                swc_id="SWC-115",
                line_number=ln,
                code_snippet=self._snippet(lines, ln),
            ))
        return findings

    def _detect_timestamp_dependence(self, source: str, lines: list[str]) -> list[dict]:
        findings: list[dict] = []
        for m in re.finditer(r'\bblock\.timestamp\b', source):
            ln = source[:m.start()].count("\n") + 1
            # Check if used in a condition
            context = source[max(0, m.start() - 100):m.end() + 100]
            if re.search(r'(?:if|require|assert)\s*\(', context):
                findings.append(self._make(
                    title="Timestamp Dependence in Condition",
                    severity="low",
                    description=(
                        "block.timestamp is used in a conditional expression. "
                        "Miners can influence the timestamp by ~15 seconds."
                    ),
                    recommendation=(
                        "Avoid tight time constraints. Use block numbers when "
                        "possible or allow a tolerance window."
                    ),
                    confidence=70,
                    tags=["layer3", "timestamp", "SWC-116"],
                    swc_id="SWC-116",
                    line_number=ln,
                    code_snippet=self._snippet(lines, ln),
                ))
        return findings

    def _detect_unchecked_return(self, source: str, lines: list[str]) -> list[dict]:
        findings: list[dict] = []
        # Low-level calls without success check
        for m in re.finditer(r'\.call\s*[({]', source):
            ln = source[:m.start()].count("\n") + 1
            # Check if the return value is captured
            line_text = lines[ln - 1] if ln <= len(lines) else ""
            if "=" not in line_text and "require" not in line_text:
                findings.append(self._make(
                    title="Unchecked Low-Level Call Return Value",
                    severity="medium",
                    description=(
                        "The return value of a low-level .call() is not "
                        "checked. If the call fails, execution continues "
                        "silently."
                    ),
                    recommendation=(
                        "Capture and check the boolean return value: "
                        "`(bool success, ) = addr.call{...}(...); "
                        "require(success);`"
                    ),
                    confidence=75,
                    tags=["layer3", "unchecked-call", "SWC-104"],
                    swc_id="SWC-104",
                    line_number=ln,
                    code_snippet=self._snippet(lines, ln),
                ))
        return findings

    def _detect_assembly_usage(self, source: str, lines: list[str]) -> list[dict]:
        findings: list[dict] = []
        for m in re.finditer(r'\bassembly\s*\{', source):
            ln = source[:m.start()].count("\n") + 1
            findings.append(self._make(
                title="Inline Assembly Block",
                severity="info",
                description=(
                    "Inline assembly bypasses Solidity safety checks. While "
                    "sometimes necessary for gas optimization, it increases "
                    "audit surface."
                ),
                recommendation=(
                    "Document the purpose of assembly blocks and prefer "
                    "Solidity equivalents where possible."
                ),
                confidence=95,
                tags=["layer3", "assembly"],
                line_number=ln,
                code_snippet=self._snippet(lines, ln),
            ))
        return findings

    def _detect_storage_collision_risk(self, source: str, lines: list[str]) -> list[dict]:
        findings: list[dict] = []
        if "delegatecall" in source and "Proxy" in source:
            findings.append(self._make(
                title="Potential Storage Collision in Proxy Pattern",
                severity="high",
                description=(
                    "The contract uses delegatecall with a Proxy-style "
                    "pattern. If storage layouts differ between proxy and "
                    "implementation, state corruption can occur."
                ),
                recommendation=(
                    "Use EIP-1967 storage slots or OpenZeppelin's "
                    "TransparentUpgradeableProxy to avoid collisions."
                ),
                confidence=60,
                tags=["layer3", "storage-collision", "proxy"],
            ))
        return findings

    def _detect_reentrancy_with_state_change(self, source: str, lines: list[str]) -> list[dict]:
        """Detect external calls followed by state changes (CEI violation)."""
        findings: list[dict] = []
        # Simplified: look for .call{value: followed by state assignment
        call_pattern = re.compile(
            r'\.call\s*\{[^}]*value[^}]*\}\s*\([^)]*\).*?;\s*\n(.*?=)',
            re.DOTALL,
        )
        for m in call_pattern.finditer(source):
            ln = source[:m.start()].count("\n") + 1
            findings.append(self._make(
                title="State Change After External Call (CEI Violation)",
                severity="high",
                description=(
                    "A state variable is modified after an external call. "
                    "This violates the Checks-Effects-Interactions pattern "
                    "and may allow reentrancy."
                ),
                recommendation=(
                    "Move state changes before external calls, or use a "
                    "ReentrancyGuard."
                ),
                confidence=65,
                tags=["layer3", "reentrancy", "SWC-107"],
                swc_id="SWC-107",
                line_number=ln,
                code_snippet=self._snippet(lines, ln),
            ))
        return findings

    # -----------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------

    @staticmethod
    def _snippet(lines: list[str], line_number: int, context: int = 2) -> str:
        start = max(0, line_number - 1 - context)
        end = min(len(lines), line_number + context)
        return "\n".join(lines[start:end])

    @staticmethod
    def _make(
        title: str,
        severity: str,
        description: str,
        recommendation: str,
        confidence: int,
        tags: list[str],
        swc_id: str = "",
        line_number: int | None = None,
        code_snippet: str = "",
    ) -> dict:
        return {
            "swc_id": swc_id,
            "title": title,
            "severity": severity,
            "description": description,
            "recommendation": recommendation,
            "confidence": confidence,
            "line_number": line_number,
            "line_start": line_number,
            "line_end": line_number,
            "column": None,
            "code_snippet": code_snippet,
            "tags": tags,
            "reference_url": (
                f"https://swcregistry.io/docs/{swc_id}" if swc_id else ""
            ),
            "metadata": {"tool": "layer3-pattern", "layer": 3},
        }
