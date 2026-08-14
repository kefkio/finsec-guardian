from __future__ import annotations

import hashlib
import re
from typing import Any

from scanner.domain.entities.finding import Finding
from scanner.domain.enums import (
    AnalyzerType,
    Confidence,
    RiskLevel,
    Severity,
)
from scanner.domain.exceptions import DomainValidationError
from scanner.domain.ports.analyzer import AnalyzerPort
from scanner.domain.value_objects.analysis_request import AnalysisRequest
from scanner.domain.value_objects.source_location import SourceLocation
from scanner.domain.value_objects.vulnerability_signature import (
    VulnerabilitySignature,
)


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

_ACCESS_CONTROL_RE = re.compile(
    "|".join(_ACCESS_CONTROL_PATTERNS),
    re.IGNORECASE,
)

_MAPPING_WRITE_RE = re.compile(
    r"(\w+)\s*\[(\w+)\]\s*[+\-*]?=",
)

_ETHER_SEND_RE = re.compile(
    r"\.transfer\s*\(|"
    r"\.send\s*\(|"
    r"\.call\s*\{[^}]*value\s*:",
)

_SETTER_NAME_RE = re.compile(
    r"^set[A-Z_]",
)

_PARAM_RE = re.compile(
    r"(?:address|uint\d*|int\d*|bool|string|bytes\d*)"
    r"(?:\s+(?:memory|calldata|storage))?"
    r"\s+(\w+)"
)


class HeuristicError(Exception):
    """Raised when deterministic heuristic analysis fails."""


class HeuristicAnalyzer(AnalyzerPort):
    """
    Deterministic regex-based heuristic analyzer.

    The analyzer preserves the four confirmed deterministic rules from
    the legacy heuristic implementation while emitting V2 domain
    Finding objects directly.

    Rules:
        1. Unguarded parameterised state mutation.
        2. Missing address input validation.
        3. Unguarded Ether transfers.
        4. Denial-of-service risk via direct Ether calls to msg.sender.
    """

    @property
    def name(self) -> str:
        """Return the canonical analyzer name."""
        return AnalyzerType.HEURISTIC.value

    async def analyze(
        self,
        request: AnalysisRequest,
    ) -> tuple[Finding, ...]:
        """
        Analyze Solidity source code and return domain findings.
        """
        if not isinstance(request, AnalysisRequest):
            raise DomainValidationError(
                "request must be an AnalysisRequest."
            )

        try:
            functions = self._extract_functions(
                request.source_code,
            )

            findings: list[Finding] = []

            for function in functions:
                findings.extend(
                    self._check_unguarded_state_mutation(
                        function=function,
                        filename=request.source_filename,
                    )
                )

                findings.extend(
                    self._check_missing_input_validation(
                        function=function,
                        filename=request.source_filename,
                    )
                )

                findings.extend(
                    self._check_unguarded_ether_send(
                        function=function,
                        filename=request.source_filename,
                    )
                )

                findings.extend(
                    self._check_dos_via_external_call(
                        function=function,
                        filename=request.source_filename,
                    )
                )

            return tuple(findings)

        except DomainValidationError:
            raise

        except Exception as exc:
            raise HeuristicError(
                "Deterministic heuristic analysis failed."
            ) from exc

    # ==========================================================
    # Function extraction
    # ==========================================================

    @staticmethod
    def _extract_functions(
        source_code: str,
    ) -> list[dict[str, Any]]:
        """
        Extract Solidity function signatures and bodies.

        This preserves the extraction strategy used by the legacy
        heuristic implementation.
        """
        pattern = re.compile(
            r"function\s+(\w+)\s*\(([^)]*)\)\s+"
            r"((?:public|external|internal|private|view|pure|payable|"
            r"virtual|override|returns\s*\([^)]*\)|\w+\s*)*)"
            r"\s*\{",
            re.MULTILINE,
        )

        functions: list[dict[str, Any]] = []

        for match in pattern.finditer(source_code):
            name = match.group(1)
            params = match.group(2)
            modifiers = match.group(3)

            start = match.end()
            depth = 1
            position = start

            while (
                position < len(source_code)
                and depth > 0
            ):
                char = source_code[position]

                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1

                position += 1

            body = source_code[
                start : position - 1
            ]

            line_number = (
                source_code[: match.start()]
                .count("\n")
                + 1
            )

            functions.append(
                {
                    "name": name,
                    "params": params,
                    "modifiers": modifiers,
                    "body": body,
                    "line": line_number,
                    "is_public": (
                        "public" in modifiers
                        or "external" in modifiers
                    ),
                    "is_view": (
                        "view" in modifiers
                        or "pure" in modifiers
                    ),
                }
            )

        return functions

    # ==========================================================
    # Unguarded state mutation
    # ==========================================================

    def _check_unguarded_state_mutation(
        self,
        *,
        function: dict[str, Any],
        filename: str,
    ) -> list[Finding]:
        if not function["is_public"] or function["is_view"]:
            return []

        name = str(function["name"])

        if name in {
            "constructor",
            "receive",
            "fallback",
        }:
            return []

        modifiers = str(function["modifiers"])
        body = str(function["body"])
        params = str(function["params"])

        if _ACCESS_CONTROL_RE.search(
            f"{modifiers} {body}",
        ):
            return []

        parameter_names = set(
            _PARAM_RE.findall(params)
        )

        writes = _MAPPING_WRITE_RE.findall(
            body,
        )

        parameter_writes = [
            (mapping, key)
            for mapping, key in writes
            if key in parameter_names
        ]

        is_setter = bool(
            _SETTER_NAME_RE.match(name)
        )

        if not parameter_writes and is_setter:
            for parameter_name in parameter_names:
                if re.search(
                    rf"\b\w+\s*=\s*"
                    rf"{re.escape(parameter_name)}\b",
                    body,
                ):
                    parameter_writes.append(
                        ("state", parameter_name)
                    )
                    break

        if not parameter_writes:
            return []

        visibility = (
            "public"
            if "public" in modifiers
            else "external"
        )

        severity = (
            Severity.CRITICAL
            if is_setter
            else Severity.HIGH
        )

        risk_level = (
            RiskLevel.CRITICAL
            if severity is Severity.CRITICAL
            else RiskLevel.HIGH
        )

        title = (
            f"Unrestricted setter: {name}()"
            if is_setter
            else f"Missing access control: {name}()"
        )

        description = (
            f"The function `{name}()` is `{visibility}` and "
            "modifies contract state using caller-supplied "
            "parameters, but has no access control "
            "(e.g., onlyOwner modifier or msg.sender check). "
            "Any external account can call this function and "
            "alter contract state arbitrarily."
        )

        recommendation = (
            f"Add an access control modifier (e.g., `onlyOwner`) "
            f"to `{name}()`, or add a "
            "`require(msg.sender == owner)` check. Consider "
            "using OpenZeppelin's Ownable or AccessControl."
        )

        return [
            self._build_finding(
                filename=filename,
                line=int(function["line"]),
                function_name=name,
                check="unguarded-state-mutation",
                title=title,
                description=description,
                recommendation=recommendation,
                severity=severity,
                risk_level=risk_level,
                confidence=Confidence.HIGH,
                swc_id="SWC-105",
            )
        ]

    # ==========================================================
    # Missing input validation
    # ==========================================================

    def _check_missing_input_validation(
        self,
        *,
        function: dict[str, Any],
        filename: str,
    ) -> list[Finding]:
        if not function["is_public"] or function["is_view"]:
            return []

        params = str(function["params"])

        if not params.strip():
            return []

        address_parameters = re.findall(
            r"address\s+(\w+)",
            params,
        )

        if not address_parameters:
            return []

        modifiers = str(function["modifiers"])
        body = str(function["body"])

        if _ACCESS_CONTROL_RE.search(
            f"{modifiers} {body}",
        ):
            return []

        has_validation = bool(
            re.search(
                r"require\s*\(|"
                r"assert\s*\(|"
                r"revert\b|"
                r"if\s*\(",
                body,
            )
        )

        if has_validation:
            return []

        name = str(function["name"])

        description = (
            f"The function `{name}()` accepts address "
            f"parameters ({', '.join(address_parameters)}) "
            "but performs no input validation. Address "
            "parameters should be checked against "
            "`address(0)` to prevent accidental burns or "
            "permanent lockouts."
        )

        recommendation = (
            f"Add `require({address_parameters[0]} "
            "!= address(0));` for each address parameter. "
            "Validate all inputs are within expected ranges "
            "before modifying state."
        )

        return [
            self._build_finding(
                filename=filename,
                line=int(function["line"]),
                function_name=name,
                check="missing-input-validation",
                title=(
                    f"Missing input validation in {name}()"
                ),
                description=description,
                recommendation=recommendation,
                severity=Severity.MEDIUM,
                risk_level=RiskLevel.MEDIUM,
                confidence=Confidence.MEDIUM,
                swc_id=None,
            )
        ]

    # ==========================================================
    # Unguarded Ether send
    # ==========================================================

    def _check_unguarded_ether_send(
        self,
        *,
        function: dict[str, Any],
        filename: str,
    ) -> list[Finding]:
        if not function["is_public"] or function["is_view"]:
            return []

        name = str(function["name"])

        if name in {
            "constructor",
            "receive",
            "fallback",
        }:
            return []

        modifiers = str(function["modifiers"])
        body = str(function["body"])

        if _ACCESS_CONTROL_RE.search(
            f"{modifiers} {body}",
        ):
            return []

        if not _ETHER_SEND_RE.search(body):
            return []

        sends_full_balance = bool(
            re.search(
                r"address\(this\)\.balance|"
                r"\.transfer\s*\(\s*"
                r"address\(this\)\.balance\s*\)|"
                r"\.call\s*\{[^}]*value\s*:\s*"
                r"address\(this\)\.balance",
                body,
            )
        )

        severity = (
            Severity.CRITICAL
            if sends_full_balance
            else Severity.HIGH
        )

        risk_level = (
            RiskLevel.CRITICAL
            if sends_full_balance
            else RiskLevel.HIGH
        )

        description = (
            f"The function `{name}()` sends Ether "
            f"{'(the entire contract balance) ' if sends_full_balance else ''}"
            "without any access control. Any external account "
            "can call this function and drain funds from the "
            "contract."
        )

        recommendation = (
            f"Add an `onlyOwner` modifier or "
            f"`require(msg.sender == owner)` check to `{name}()`. "
            "Consider using OpenZeppelin's Ownable to restrict "
            "privileged operations."
        )

        return [
            self._build_finding(
                filename=filename,
                line=int(function["line"]),
                function_name=name,
                check="unguarded-ether-send",
                title=(
                    f"Unprotected Ether withdrawal: {name}()"
                ),
                description=description,
                recommendation=recommendation,
                severity=severity,
                risk_level=risk_level,
                confidence=Confidence.HIGH,
                swc_id="SWC-105",
            )
        ]

    # ==========================================================
    # Denial of service via external call
    # ==========================================================

    def _check_dos_via_external_call(
        self,
        *,
        function: dict[str, Any],
        filename: str,
    ) -> list[Finding]:
        if not function["is_public"] or function["is_view"]:
            return []

        body = str(function["body"])

        has_sender_send = bool(
            re.search(
                r"msg\.sender\.(?:call\s*\{|"
                r"transfer\s*\(|send\s*\()",
                body,
            )
        )

        if not has_sender_send:
            return []

        if re.search(
            r"pendingWithdrawals|"
            r"pendingReturns|"
            r"pullPayment",
            body,
        ):
            return []

        name = str(function["name"])

        return [
            self._build_finding(
                filename=filename,
                line=int(function["line"]),
                function_name=name,
                check="dos-external-call",
                title=(
                    f"Denial of service risk in {name}()"
                ),
                description=(
                    f"The function `{name}()` sends Ether directly "
                    "to `msg.sender`. If the caller is a contract "
                    "with a reverting fallback/receive function, "
                    "the call will always fail, permanently locking "
                    "the user's funds in this contract."
                ),
                recommendation=(
                    "Use a pull-payment pattern instead of pushing "
                    "Ether directly. Let users withdraw through a "
                    "separate claim function."
                ),
                severity=Severity.MEDIUM,
                risk_level=RiskLevel.MEDIUM,
                confidence=Confidence.MEDIUM,
                swc_id="SWC-113",
            )
        ]

    # ==========================================================
    # Finding construction
    # ==========================================================

    @staticmethod
    def _build_finding(
        *,
        filename: str,
        line: int,
        function_name: str,
        check: str,
        title: str,
        description: str,
        recommendation: str,
        severity: Severity,
        risk_level: RiskLevel,
        confidence: Confidence,
        swc_id: str | None,
    ) -> Finding:
        """
        Construct a domain Finding with a deterministic SHA-256
        vulnerability fingerprint.
        """
        location = SourceLocation(
            filename=filename or "contract.sol",
            line=line,
            column=1,
            end_line=line,
            end_column=None,
        )

        signature_material = (
            f"heuristic|"
            f"{check}|"
            f"{function_name}|"
            f"{filename}|"
            f"{line}"
        )

        signature_value = hashlib.sha256(
            signature_material.encode("utf-8"),
        ).hexdigest()

        return Finding(
            title=title,
            description=description,
            recommendation=recommendation,
            severity=severity,
            confidence=confidence,
            risk_level=risk_level,
            analyzer=AnalyzerType.HEURISTIC,
            location=location,
            signature=VulnerabilitySignature(
                signature_value,
            ),
            swc_id=swc_id,
        )