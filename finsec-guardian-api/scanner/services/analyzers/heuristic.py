"""Heuristic source-code analyzer for logic flaws.

Complements Slither/Mythril by detecting semantic patterns that static
and symbolic tools often miss:

  • Unrestricted state-mutating functions (missing access control)
  • Setter functions without ownership checks
  • Missing input validation on address parameters
  • Contract-level absence of any governance mechanism
"""

from __future__ import annotations

import re

from .base import AnalyzerResult

# ---------------------------------------------------------------------------
# Access-control patterns — if any appear in a function, we consider it guarded.
# ---------------------------------------------------------------------------
_ACCESS_CONTROL_PATTERNS = [
    r"onlyOwner",
    r"onlyRole",
    r"onlyAdmin",
    r"require\s*\(\s*msg\.sender\s*==",
    r"require\s*\(\s*owner\s*==\s*msg\.sender",
    r"require\s*\(\s*_msgSender\(\)\s*==",
    r"if\s*\(\s*msg\.sender\s*!=",
    r"_checkOwner\(",
    r"_checkRole\(",
    r"hasRole\(",
    r"onlyProxy",
    r"initializer",
]
_ACCESS_CONTROL_RE = re.compile("|".join(_ACCESS_CONTROL_PATTERNS), re.IGNORECASE)

# Mapping writes: captures  mapping_name[key_var] =
_MAPPING_WRITE_RE = re.compile(r"(\w+)\s*\[(\w+)\]\s*[+\-*]?=")

# Ether-sending patterns
_ETHER_SEND_RE = re.compile(
    r"\.transfer\s*\(|\.send\s*\(|\.call\s*\{[^}]*value\s*:",
)

# Setter-style function name
_SETTER_NAME_RE = re.compile(r"^set[A-Z_]")

# Event emission pattern
_EVENT_EMIT_RE = re.compile(r"\bemit\s+\w+")

# Event declaration pattern
_EVENT_DECL_RE = re.compile(r"\bevent\s+\w+")

# Solidity parameter extraction — "type name" pairs
_PARAM_RE = re.compile(
    r"(?:address|uint\d*|int\d*|bool|string|bytes\d*)"
    r"(?:\s+(?:memory|calldata|storage))?"
    r"\s+(\w+)"
)


class HeuristicError(Exception):
    """Raised when heuristic analysis cannot proceed."""


class HeuristicAnalyzer:
    """Regex-based source analysis for logic flaws.

    Returns an ``AnalyzerResult`` with ``tool="heuristic"`` whose
    ``raw_output["findings"]`` list is already in the normalised finding
    format (the :class:`FindingNormalizer` passes it through unchanged).
    """

    def analyze(
        self,
        source_code: str,
        contract_name: str | None = None,
        **kwargs,
    ) -> AnalyzerResult:
        findings: list[dict] = []

        functions = self._extract_functions(source_code)
        for func in functions:
            findings.extend(self._check_unguarded_state_mutation(func))
            findings.extend(self._check_missing_input_validation(func))
            findings.extend(self._check_unguarded_ether_send(func))
            findings.extend(self._check_dos_via_external_call(func))

        findings.extend(self._check_missing_ownership(source_code))
        findings.extend(self._check_missing_events(source_code, functions))

        return AnalyzerResult(
            success=True,
            raw_output={"findings": findings},
            tool="heuristic",
        )

    # ------------------------------------------------------------------
    # Function extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_functions(source_code: str) -> list[dict]:
        """Parse function signatures and bodies from Solidity source."""
        pattern = re.compile(
            r"function\s+(\w+)\s*\(([^)]*)\)\s+"
            r"((?:public|external|internal|private|view|pure|payable|"
            r"virtual|override|returns\s*\([^)]*\)|\w+\s*)*)"
            r"\s*\{",
            re.MULTILINE,
        )

        functions: list[dict] = []
        for match in pattern.finditer(source_code):
            name = match.group(1)
            params = match.group(2)
            modifiers = match.group(3)

            # Find matching closing brace.
            start = match.end()
            depth = 1
            pos = start
            while pos < len(source_code) and depth > 0:
                ch = source_code[pos]
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                pos += 1

            body = source_code[start : pos - 1]
            line_number = source_code[: match.start()].count("\n") + 1

            functions.append(
                {
                    "name": name,
                    "params": params,
                    "modifiers": modifiers,
                    "body": body,
                    "line": line_number,
                    "is_public": "public" in modifiers or "external" in modifiers,
                    "is_view": "view" in modifiers or "pure" in modifiers,
                }
            )
        return functions

    # ------------------------------------------------------------------
    # Check: unrestricted parameterised state writes
    # ------------------------------------------------------------------

    def _check_unguarded_state_mutation(self, func: dict) -> list[dict]:
        """Flag public functions that write state via parameters without ACL."""
        if not func["is_public"] or func["is_view"]:
            return []
        if func["name"] in ("constructor", "receive", "fallback"):
            return []

        # Has access control? → skip.
        full_text = func["modifiers"] + " " + func["body"]
        if _ACCESS_CONTROL_RE.search(full_text):
            return []

        # Extract parameter names.
        param_names = set(_PARAM_RE.findall(func["params"]))

        # Find mapping writes whose key is a function parameter (not msg.sender).
        writes = _MAPPING_WRITE_RE.findall(func["body"])
        param_writes = [
            (mapping, key) for mapping, key in writes if key in param_names
        ]

        if not param_writes:
            # No parameterised state writes — could still be a setter by name
            # with direct assignment (e.g., `owner = _newOwner`).
            if _SETTER_NAME_RE.match(func["name"]) and param_names:
                for pname in param_names:
                    if re.search(rf"\b\w+\s*=\s*{re.escape(pname)}\b", func["body"]):
                        param_writes.append(("state", pname))
                        break
            if not param_writes:
                return []

        visibility = "public" if "public" in func["modifiers"] else "external"
        is_setter = _SETTER_NAME_RE.match(func["name"])
        severity = "critical" if is_setter else "high"

        title = (
            f"Unrestricted setter: {func['name']}()"
            if is_setter
            else f"Missing access control: {func['name']}()"
        )

        return [
            {
                "swc_id": "SWC-105",
                "title": title,
                "severity": severity,
                "description": (
                    f"The function `{func['name']}()` is `{visibility}` and "
                    f"modifies contract state using caller-supplied parameters, "
                    f"but has no access control (e.g., onlyOwner modifier or "
                    f"msg.sender check). Any external account can call this "
                    f"function and alter contract state arbitrarily."
                ),
                "recommendation": (
                    f"Add an access control modifier (e.g., `onlyOwner`) to "
                    f"`{func['name']}()`, or add a "
                    f"`require(msg.sender == owner)` check. Consider using "
                    f"OpenZeppelin's Ownable or AccessControl."
                ),
                "confidence": 85,
                "line_number": func["line"],
                "line_start": func["line"],
                "line_end": func["line"],
                "column": None,
                "code_snippet": f"function {func['name']}({func['params']})",
                "tags": ["heuristic", "access-control", func["name"]],
                "reference_url": "https://swcregistry.io/docs/SWC-105",
                "metadata": {
                    "tool": "heuristic",
                    "check": "unguarded-state-mutation",
                    "function": func["name"],
                },
            }
        ]

    # ------------------------------------------------------------------
    # Check: missing input validation
    # ------------------------------------------------------------------

    def _check_missing_input_validation(self, func: dict) -> list[dict]:
        """Flag functions that accept address params but don't validate them."""
        if not func["is_public"] or func["is_view"]:
            return []
        if not func["params"].strip():
            return []

        # Only care about address parameters.
        addr_params = re.findall(r"address\s+(\w+)", func["params"])
        if not addr_params:
            return []

        # Check for ANY require/assert/revert/if validation in the body.
        has_validation = bool(
            re.search(r"require\s*\(|assert\s*\(|revert\b|if\s*\(", func["body"])
        )

        # Has access control? → address checks may be implicit.
        full_text = func["modifiers"] + " " + func["body"]
        if _ACCESS_CONTROL_RE.search(full_text):
            return []

        if has_validation:
            return []

        return [
            {
                "swc_id": "",
                "title": f"Missing input validation in {func['name']}()",
                "severity": "medium",
                "description": (
                    f"The function `{func['name']}()` accepts address parameters "
                    f"({', '.join(addr_params)}) but performs no input validation. "
                    f"Address parameters should be checked against `address(0)` "
                    f"to prevent accidental burns or permanent lockouts."
                ),
                "recommendation": (
                    f"Add `require({addr_params[0]} != address(0));` for each "
                    f"address parameter. Validate all inputs are within "
                    f"expected ranges before modifying state."
                ),
                "confidence": 60,
                "line_number": func["line"],
                "line_start": func["line"],
                "line_end": func["line"],
                "column": None,
                "code_snippet": "",
                "tags": ["heuristic", "input-validation", func["name"]],
                "reference_url": "",
                "metadata": {
                    "tool": "heuristic",
                    "check": "missing-input-validation",
                    "function": func["name"],
                },
            }
        ]

    # ------------------------------------------------------------------
    # Check: unguarded Ether send (e.g. emergencyWithdraw)
    # ------------------------------------------------------------------

    def _check_unguarded_ether_send(self, func: dict) -> list[dict]:
        """Flag public functions that send Ether without access control.

        Functions that transfer the *entire* contract balance to
        ``msg.sender`` without any ownership check are critical — they
        let anyone drain the contract.
        """
        if not func["is_public"] or func["is_view"]:
            return []
        if func["name"] in ("constructor", "receive", "fallback"):
            return []

        # Has access control? → skip.
        full_text = func["modifiers"] + " " + func["body"]
        if _ACCESS_CONTROL_RE.search(full_text):
            return []

        if not _ETHER_SEND_RE.search(func["body"]):
            return []

        # Sending the full balance is worse than a partial amount.
        sends_full_balance = bool(
            re.search(
                r"address\(this\)\.balance|"
                r"\.transfer\s*\(\s*address\(this\)\.balance\s*\)|"
                r"\.call\s*\{[^}]*value\s*:\s*address\(this\)\.balance",
                func["body"],
            )
        )

        severity = "critical" if sends_full_balance else "high"

        return [
            {
                "swc_id": "SWC-105",
                "title": f"Unprotected Ether withdrawal: {func['name']}()",
                "severity": severity,
                "description": (
                    f"The function `{func['name']}()` sends Ether "
                    f"{'(the entire contract balance) ' if sends_full_balance else ''}"
                    f"without any access control. Any external account can call "
                    f"this function and drain funds from the contract."
                ),
                "recommendation": (
                    f"Add an `onlyOwner` modifier or `require(msg.sender == owner)` "
                    f"check to `{func['name']}()`. Consider using OpenZeppelin's "
                    f"Ownable to restrict privileged operations."
                ),
                "confidence": 90,
                "line_number": func["line"],
                "line_start": func["line"],
                "line_end": func["line"],
                "column": None,
                "code_snippet": f"function {func['name']}({func['params']})",
                "tags": ["heuristic", "access-control", "ether-drain", func["name"]],
                "reference_url": "https://swcregistry.io/docs/SWC-105",
                "metadata": {
                    "tool": "heuristic",
                    "check": "unguarded-ether-send",
                    "function": func["name"],
                    "sends_full_balance": sends_full_balance,
                },
            }
        ]

    # ------------------------------------------------------------------
    # Check: Denial of Service via external call
    # ------------------------------------------------------------------

    def _check_dos_via_external_call(self, func: dict) -> list[dict]:
        """Flag functions that send Ether via call/transfer without pull-payment.

        If msg.sender is a contract with a reverting receive/fallback,
        the withdrawal will always revert — locking user funds permanently.
        """
        if not func["is_public"] or func["is_view"]:
            return []

        # Look for patterns: msg.sender.call{value:...} or msg.sender.transfer(...)
        has_sender_send = bool(
            re.search(
                r"msg\.sender\.(?:call\s*\{|transfer\s*\(|send\s*\()",
                func["body"],
            )
        )
        if not has_sender_send:
            return []

        # If there's a pull-payment pattern (withdrawal mapping), skip.
        if re.search(r"pendingWithdrawals|pendingReturns|pullPayment", func["body"]):
            return []

        return [
            {
                "swc_id": "SWC-113",
                "title": f"Denial of service risk in {func['name']}()",
                "severity": "medium",
                "description": (
                    f"The function `{func['name']}()` sends Ether directly to "
                    f"`msg.sender`. If the caller is a contract with a reverting "
                    f"fallback/receive function, the call will always fail, "
                    f"permanently locking the user's funds in this contract."
                ),
                "recommendation": (
                    "Use a pull-payment pattern (e.g., OpenZeppelin's "
                    "PullPayment) instead of pushing Ether directly. Let "
                    "users withdraw via a separate claim function."
                ),
                "confidence": 65,
                "line_number": func["line"],
                "line_start": func["line"],
                "line_end": func["line"],
                "column": None,
                "code_snippet": "",
                "tags": ["heuristic", "dos", func["name"]],
                "reference_url": "https://swcregistry.io/docs/SWC-113",
                "metadata": {
                    "tool": "heuristic",
                    "check": "dos-external-call",
                    "function": func["name"],
                },
            }
        ]

    # ------------------------------------------------------------------
    # Check: missing event logging
    # ------------------------------------------------------------------

    @staticmethod
    def _check_missing_events(
        source_code: str, functions: list[dict],
    ) -> list[dict]:
        """Flag contracts with state-mutating functions but no event emissions."""
        # If the contract declares and emits events, it's fine.
        has_event_decl = bool(_EVENT_DECL_RE.search(source_code))
        has_event_emit = bool(_EVENT_EMIT_RE.search(source_code))
        if has_event_decl and has_event_emit:
            return []

        # Only flag if there are public mutating functions.
        public_mutating = [
            f for f in functions
            if f["is_public"] and not f["is_view"]
            and f["name"] not in ("constructor", "receive", "fallback")
        ]
        if not public_mutating:
            return []

        func_names = ", ".join(f"`{f['name']}()`" for f in public_mutating[:5])
        suffix = (
            f" and {len(public_mutating) - 5} more"
            if len(public_mutating) > 5
            else ""
        )

        return [
            {
                "swc_id": "",
                "title": "No event logging detected",
                "severity": "low",
                "description": (
                    f"This contract has state-modifying functions "
                    f"({func_names}{suffix}) but does not emit any events. "
                    f"Events are essential for off-chain monitoring, "
                    f"auditing, and front-end synchronisation."
                ),
                "recommendation": (
                    "Define events for significant state changes (deposits, "
                    "withdrawals, ownership transfers) and emit them in the "
                    "relevant functions."
                ),
                "confidence": 70,
                "line_number": 1,
                "line_start": 1,
                "line_end": 1,
                "column": None,
                "code_snippet": "",
                "tags": ["heuristic", "event-logging", "best-practice"],
                "reference_url": "",
                "metadata": {
                    "tool": "heuristic",
                    "check": "missing-events",
                    "affected_functions": [f["name"] for f in public_mutating],
                },
            }
        ]

    # ------------------------------------------------------------------
    # Check: contract-level missing ownership
    # ------------------------------------------------------------------

    @staticmethod
    def _check_missing_ownership(source_code: str) -> list[dict]:
        """Flag contracts that mutate state but have no governance pattern."""
        ownership_patterns = [
            r"Ownable",
            r"owner\s*=\s*msg\.sender",
            r"address\s+(?:public\s+)?owner",
            r"onlyOwner",
            r"AccessControl",
            r"hasRole",
            r"_grantRole",
        ]
        if any(re.search(p, source_code) for p in ownership_patterns):
            return []

        # Only flag if the contract has public state-modifying functions.
        has_public_mutating = bool(
            re.search(
                r"function\s+\w+\s*\([^)]*\)\s+(?:public|external)"
                r"(?!\s+view|\s+pure)",
                source_code,
            )
        )
        if not has_public_mutating:
            return []

        return [
            {
                "swc_id": "",
                "title": "No ownership or access control pattern detected",
                "severity": "high",
                "description": (
                    "This contract contains public state-modifying functions "
                    "but has no ownership or role-based access control pattern "
                    "(e.g., OpenZeppelin Ownable, AccessControl). Without "
                    "governance controls, any external account can invoke "
                    "privileged operations."
                ),
                "recommendation": (
                    "Implement an access control mechanism. Use OpenZeppelin's "
                    "Ownable for single-owner patterns or AccessControl for "
                    "role-based permissions."
                ),
                "confidence": 75,
                "line_number": 1,
                "line_start": 1,
                "line_end": 1,
                "column": None,
                "code_snippet": "",
                "tags": ["heuristic", "access-control", "governance"],
                "reference_url": "https://docs.openzeppelin.com/contracts/access-control",
                "metadata": {
                    "tool": "heuristic",
                    "check": "missing-ownership",
                },
            }
        ]
