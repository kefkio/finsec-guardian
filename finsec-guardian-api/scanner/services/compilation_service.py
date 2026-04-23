"""Layer 2 — Compilation & Semantic Validation Service.

Ensures that the Solidity source is correctly compiled, the pragma is
resolved, and the AST can be parsed before deeper layers run.  Many
vulnerability-detection tools fail silently or produce false positives when
compilation is broken; this layer catches those issues early.

Analyses performed:
    - Pragma version resolution & mismatch detection
    - Compilation success / error surfacing
    - Bytecode vs source consistency check
    - AST structural validation via Slither
    - Dependency / import resolution warnings
"""

import logging
import os
import re
import tempfile

logger = logging.getLogger(__name__)


class CompilationValidationError(Exception):
    """Raised when compilation or semantic validation fails."""


class CompilationValidationService:
    """Layer 2: validate compilation artifacts and AST integrity."""

    def run_analysis(
        self,
        source_code: str,
        contract_name: str | None = None,
        compiled_abi: list | None = None,
        compiled_bytecode: str = "",
        compilation_error: str = "",
        solidity_version: str = "",
    ) -> dict:
        findings: list[dict] = []

        # --- 2a. Compilation failure ----------------------------------------
        if compilation_error:
            findings.append(self._make_finding(
                title="Compilation Failure",
                severity="critical",
                description=(
                    f"The Solidity source failed to compile: {compilation_error}"
                ),
                recommendation="Fix compilation errors before scanning.",
                confidence=100,
                tags=["layer2", "compilation"],
            ))
            return {"success": False, "findings": findings, "error": compilation_error}

        # --- 2b. Pragma analysis --------------------------------------------
        findings.extend(self._check_pragma(source_code, solidity_version))

        # --- 2c. Bytecode consistency check ---------------------------------
        if compiled_abi is not None and not compiled_bytecode:
            findings.append(self._make_finding(
                title="Empty Bytecode After Compilation",
                severity="medium",
                description=(
                    "Compilation succeeded with an ABI but produced no "
                    "bytecode. This may indicate an abstract contract or "
                    "interface — analysis tools that rely on bytecode (e.g. "
                    "Mythril) will be unable to run."
                ),
                recommendation=(
                    "If this is an implementation contract, check for "
                    "missing function bodies or constructor issues."
                ),
                confidence=80,
                tags=["layer2", "bytecode"],
            ))

        # --- 2d. AST validation via Slither ---------------------------------
        findings.extend(self._validate_ast(source_code, contract_name))

        # --- 2e. Import / dependency warnings --------------------------------
        findings.extend(self._check_imports(source_code))

        success = not any(f["severity"] == "critical" for f in findings)
        return {"success": success, "findings": findings, "error": None}

    # ------------------------------------------------------------------
    # Pragma checks
    # ------------------------------------------------------------------

    def _check_pragma(self, source_code: str, resolved_version: str) -> list[dict]:
        findings: list[dict] = []
        pragma_match = re.search(r'pragma\s+solidity\s+([^;]+);', source_code)

        if not pragma_match:
            findings.append(self._make_finding(
                title="Missing Pragma Directive",
                severity="medium",
                description=(
                    "No `pragma solidity` directive found. The compiler "
                    "version was inferred as the platform default, which "
                    "may not match the author's intent."
                ),
                recommendation="Add an explicit `pragma solidity ^X.Y.Z;` directive.",
                confidence=95,
                tags=["layer2", "pragma", "SWC-103"],
            ))
            return findings

        pragma_text = pragma_match.group(1).strip()

        # Floating pragma
        if pragma_text.startswith("^") or pragma_text.startswith(">="):
            findings.append(self._make_finding(
                title="Floating Pragma",
                severity="low",
                description=(
                    f"Pragma `{pragma_text}` allows a range of compiler "
                    "versions. Contracts should be deployed with the exact "
                    "version used during testing."
                ),
                recommendation="Use a fixed pragma, e.g. `pragma solidity 0.8.21;`.",
                confidence=90,
                tags=["layer2", "pragma", "SWC-103"],
                swc_id="SWC-103",
            ))

        # Outdated compiler
        version_match = re.search(r'(\d+)\.(\d+)', pragma_text)
        if version_match:
            major, minor = int(version_match.group(1)), int(version_match.group(2))
            if major == 0 and minor < 8:
                findings.append(self._make_finding(
                    title="Outdated Compiler Version",
                    severity="medium",
                    description=(
                        f"Solidity {major}.{minor}.x lacks built-in overflow "
                        "protection and numerous security fixes present in 0.8.x."
                    ),
                    recommendation="Upgrade to Solidity 0.8.x or later.",
                    confidence=95,
                    tags=["layer2", "pragma", "SWC-102"],
                    swc_id="SWC-102",
                ))

        return findings

    # ------------------------------------------------------------------
    # AST validation
    # ------------------------------------------------------------------

    def _validate_ast(self, source_code: str, contract_name: str | None) -> list[dict]:
        findings: list[dict] = []
        try:
            from slither import Slither  # noqa: PLC0415
        except ImportError:
            return findings

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".sol", prefix="finsec_ast_",
            delete=False, encoding="utf-8",
        ) as tmp:
            tmp.write(source_code)
            tmp_path = tmp.name

        try:
            sl = Slither(tmp_path)
            # Check for contracts without functions (empty / abstract)
            for contract in sl.contracts:
                if contract.is_interface:
                    continue
                if len(contract.functions) == 0:
                    findings.append(self._make_finding(
                        title=f"Empty Contract: {contract.name}",
                        severity="info",
                        description=(
                            f"Contract `{contract.name}` has no functions. "
                            "This may be a base abstract contract or a stub."
                        ),
                        recommendation="Verify this is intentional.",
                        confidence=70,
                        tags=["layer2", "ast"],
                    ))
        except Exception as exc:
            findings.append(self._make_finding(
                title="AST Parse Failure",
                severity="high",
                description=(
                    f"Cannot parse AST: {exc}. Tools relying on the AST "
                    "(Slither, pattern layer) may produce incomplete results."
                ),
                recommendation="Fix compilation issues first.",
                confidence=95,
                tags=["layer2", "ast"],
            ))
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

        return findings

    # ------------------------------------------------------------------
    # Import / dependency checks
    # ------------------------------------------------------------------

    def _check_imports(self, source_code: str) -> list[dict]:
        findings: list[dict] = []
        import_matches = re.findall(
            r'import\s+(?:"([^"]+)"|\'([^\']+)\'|{[^}]*}\s+from\s+"([^"]+)")',
            source_code,
        )
        for groups in import_matches:
            path = next((g for g in groups if g), "")
            if path.startswith("http://") or path.startswith("https://"):
                findings.append(self._make_finding(
                    title="Remote Import Detected",
                    severity="high",
                    description=(
                        f"The source imports from a remote URL: `{path}`. "
                        "Remote imports cannot be verified at analysis time "
                        "and may introduce supply-chain risks."
                    ),
                    recommendation=(
                        "Pin dependencies locally or use a package manager "
                        "(npm / Foundry remappings) with integrity checks."
                    ),
                    confidence=90,
                    tags=["layer2", "dependency", "supply-chain"],
                ))
        return findings

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_finding(
        title: str,
        severity: str,
        description: str,
        recommendation: str,
        confidence: int,
        tags: list[str],
        swc_id: str = "",
    ) -> dict:
        return {
            "swc_id": swc_id,
            "title": title,
            "severity": severity,
            "description": description,
            "recommendation": recommendation,
            "confidence": confidence,
            "line_number": None,
            "line_start": None,
            "line_end": None,
            "column": None,
            "code_snippet": "",
            "tags": tags,
            "reference_url": (
                f"https://swcregistry.io/docs/{swc_id}" if swc_id else ""
            ),
            "metadata": {"tool": "layer2-compilation", "layer": 2},
        }
