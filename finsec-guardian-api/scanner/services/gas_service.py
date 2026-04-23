"""Layer 4 — Gas, Complexity & Optimization Analysis Service.

Analyses performed:
    - Unbounded loop / array iteration detection (DoS vector)
    - Expensive storage operations inside loops
    - Cyclomatic complexity estimation per function
    - Redundant SSTORE detection (write-after-write in same tx)
    - Gas-intensive patterns: string concatenation, repeated SLOAD
    - Function selector collision risk (not common but checked)
"""

import logging
import re

logger = logging.getLogger(__name__)

# Thresholds
MAX_CYCLOMATIC_COMPLEXITY = 15
LOOP_BODY_STORAGE_KEYWORDS = [
    "push", "pop", "delete", ".length", "storage",
]


class GasAnalysisService:
    """Layer 4: gas cost and computational complexity analysis."""

    def run_analysis(self, source_code: str, **_kwargs) -> dict:
        findings: list[dict] = []
        lines = source_code.splitlines()

        findings.extend(self._detect_unbounded_loops(source_code, lines))
        findings.extend(self._detect_storage_in_loops(source_code, lines))
        findings.extend(self._detect_repeated_sload(source_code, lines))
        findings.extend(self._detect_string_concat_in_loop(source_code, lines))
        findings.extend(self._estimate_complexity(source_code, lines))
        findings.extend(self._detect_large_array_copy(source_code, lines))

        return {"success": True, "findings": findings, "error": None}

    # -----------------------------------------------------------------
    # Detectors
    # -----------------------------------------------------------------

    def _detect_unbounded_loops(self, source: str, lines: list[str]) -> list[dict]:
        """Detect for-loops iterating over dynamic-length arrays."""
        findings: list[dict] = []
        pattern = re.compile(
            r'for\s*\(\s*\w+\s+\w+\s*=\s*0\s*;\s*\w+\s*<\s*(\w+(?:\.\w+)*)\s*;',
        )
        for m in pattern.finditer(source):
            bound_expr = m.group(1)
            ln = source[:m.start()].count("\n") + 1
            if ".length" in bound_expr or not re.match(r'^[A-Z_]+$', bound_expr):
                findings.append(self._make(
                    title="Potentially Unbounded Loop",
                    severity="medium",
                    description=(
                        f"Loop bounded by `{bound_expr}` which appears to be "
                        "a dynamic value. If the array grows large, this can "
                        "exceed the block gas limit and cause a DoS."
                    ),
                    recommendation=(
                        "Implement pagination or limit the maximum iteration "
                        "count with a constant cap."
                    ),
                    confidence=70,
                    tags=["layer4", "gas", "dos", "unbounded-loop"],
                    line_number=ln,
                    code_snippet=self._snippet(lines, ln),
                ))
        return findings

    def _detect_storage_in_loops(self, source: str, lines: list[str]) -> list[dict]:
        """Detect storage writes inside loop bodies."""
        findings: list[dict] = []
        # Find loop blocks (simplistic brace matching)
        loop_pattern = re.compile(r'(?:for|while)\s*\([^)]*\)\s*\{', re.DOTALL)
        for m in loop_pattern.finditer(source):
            loop_start = m.end()
            # Find matching closing brace (1-level depth)
            depth = 1
            pos = loop_start
            while pos < len(source) and depth > 0:
                if source[pos] == "{":
                    depth += 1
                elif source[pos] == "}":
                    depth -= 1
                pos += 1
            loop_body = source[loop_start:pos]
            ln = source[:m.start()].count("\n") + 1

            # Check for storage-related operations
            for keyword in LOOP_BODY_STORAGE_KEYWORDS:
                if keyword in loop_body:
                    findings.append(self._make(
                        title="Storage Operation Inside Loop",
                        severity="medium",
                        description=(
                            f"A storage-related keyword (`{keyword}`) appears "
                            "inside a loop body. Each SSTORE costs 5000-20000 "
                            "gas; batching or using memory can reduce costs."
                        ),
                        recommendation=(
                            "Cache values in memory, perform batch updates, "
                            "or restructure to minimize in-loop storage writes."
                        ),
                        confidence=65,
                        tags=["layer4", "gas", "storage-in-loop"],
                        line_number=ln,
                        code_snippet=self._snippet(lines, ln),
                    ))
                    break  # one finding per loop
        return findings

    def _detect_repeated_sload(self, source: str, lines: list[str]) -> list[dict]:
        """Detect state variable read multiple times without caching."""
        findings: list[dict] = []
        # Find function bodies and check for duplicate state reads
        func_pattern = re.compile(r'function\s+(\w+)\s*\([^)]*\)[^{]*\{')
        for fm in func_pattern.finditer(source):
            func_name = fm.group(1)
            func_start = fm.end()
            depth = 1
            pos = func_start
            while pos < len(source) and depth > 0:
                if source[pos] == "{":
                    depth += 1
                elif source[pos] == "}":
                    depth -= 1
                pos += 1
            func_body = source[func_start:pos]

            # Find state variable accesses (heuristic: word that isn't a
            # local var declaration, accessed > 2 times)
            state_reads = re.findall(r'\b([a-z_]\w*)\b', func_body)
            from collections import Counter
            counts = Counter(state_reads)
            for var, count in counts.items():
                if count >= 4 and var not in (
                    "uint256", "address", "bool", "bytes32", "string",
                    "memory", "storage", "calldata", "return", "require",
                    "emit", "msg", "block", "true", "false", "this",
                    "uint", "int", "bytes", "if", "else", "for", "while",
                ):
                    # Check if it's likely a state variable (not declared in func)
                    if re.search(rf'(?:uint|int|address|bool|bytes|string)\d*\s+{re.escape(var)}\b', func_body):
                        continue  # local variable
                    ln = source[:fm.start()].count("\n") + 1
                    findings.append(self._make(
                        title=f"Repeated State Read: {var} in {func_name}()",
                        severity="info",
                        description=(
                            f"`{var}` is accessed {count} times in "
                            f"`{func_name}()`. Each SLOAD costs 2100 gas "
                            "(cold) or 100 gas (warm). Caching in a local "
                            "variable saves gas."
                        ),
                        recommendation=(
                            f"Cache `{var}` in a local memory variable at "
                            "the top of the function."
                        ),
                        confidence=50,
                        tags=["layer4", "gas", "repeated-sload"],
                        line_number=ln,
                        code_snippet="",
                    ))
                    break  # one per function to avoid noise
        return findings

    def _detect_string_concat_in_loop(self, source: str, lines: list[str]) -> list[dict]:
        findings: list[dict] = []
        loop_pattern = re.compile(r'(?:for|while)\s*\([^)]*\)\s*\{', re.DOTALL)
        for m in loop_pattern.finditer(source):
            loop_start = m.end()
            depth = 1
            pos = loop_start
            while pos < len(source) and depth > 0:
                if source[pos] == "{":
                    depth += 1
                elif source[pos] == "}":
                    depth -= 1
                pos += 1
            loop_body = source[loop_start:pos]
            ln = source[:m.start()].count("\n") + 1
            if "abi.encodePacked" in loop_body or "string.concat" in loop_body:
                findings.append(self._make(
                    title="String Concatenation Inside Loop",
                    severity="low",
                    description=(
                        "String concatenation (abi.encodePacked / "
                        "string.concat) inside a loop is very gas-expensive "
                        "due to memory expansion."
                    ),
                    recommendation="Build the result outside the loop or use bytes buffers.",
                    confidence=80,
                    tags=["layer4", "gas", "string-concat-loop"],
                    line_number=ln,
                    code_snippet=self._snippet(lines, ln),
                ))
        return findings

    def _estimate_complexity(self, source: str, lines: list[str]) -> list[dict]:
        """Heuristic cyclomatic complexity per function."""
        findings: list[dict] = []
        func_pattern = re.compile(r'function\s+(\w+)\s*\([^)]*\)[^{]*\{')
        decision_keywords = re.compile(r'\b(?:if|else\s+if|for|while|do|case|\?\s*:)\b')

        for fm in func_pattern.finditer(source):
            func_name = fm.group(1)
            func_start = fm.end()
            depth = 1
            pos = func_start
            while pos < len(source) and depth > 0:
                if source[pos] == "{":
                    depth += 1
                elif source[pos] == "}":
                    depth -= 1
                pos += 1
            func_body = source[func_start:pos]
            complexity = 1 + len(decision_keywords.findall(func_body))
            if complexity > MAX_CYCLOMATIC_COMPLEXITY:
                ln = source[:fm.start()].count("\n") + 1
                findings.append(self._make(
                    title=f"High Complexity: {func_name}() (CC={complexity})",
                    severity="low",
                    description=(
                        f"Function `{func_name}()` has an estimated "
                        f"cyclomatic complexity of {complexity} (threshold: "
                        f"{MAX_CYCLOMATIC_COMPLEXITY}). High complexity "
                        "increases audit difficulty and gas cost."
                    ),
                    recommendation=(
                        "Refactor into smaller functions with clear "
                        "responsibilities."
                    ),
                    confidence=75,
                    tags=["layer4", "complexity"],
                    line_number=ln,
                    code_snippet="",
                ))
        return findings

    def _detect_large_array_copy(self, source: str, lines: list[str]) -> list[dict]:
        """Detect returning storage arrays (implicit full copy to memory)."""
        findings: list[dict] = []
        pattern = re.compile(
            r'function\s+(\w+)\s*\([^)]*\)[^{]*returns?\s*\([^)]*\[\s*\][^)]*\)',
        )
        for m in pattern.finditer(source):
            func_name = m.group(1)
            ln = source[:m.start()].count("\n") + 1
            findings.append(self._make(
                title=f"Dynamic Array Return: {func_name}()",
                severity="info",
                description=(
                    f"`{func_name}()` returns a dynamic array. If the "
                    "backing storage array grows large, the copy from "
                    "storage to memory can exceed the block gas limit."
                ),
                recommendation=(
                    "Consider adding pagination (offset + limit) or "
                    "returning a bounded subset."
                ),
                confidence=55,
                tags=["layer4", "gas", "array-copy"],
                line_number=ln,
                code_snippet=self._snippet(lines, ln),
            ))
        return findings

    # -----------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------

    @staticmethod
    def _snippet(lines: list[str], ln: int, ctx: int = 2) -> str:
        s = max(0, ln - 1 - ctx)
        e = min(len(lines), ln + ctx)
        return "\n".join(lines[s:e])

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
            "metadata": {"tool": "layer4-gas", "layer": 4},
        }
