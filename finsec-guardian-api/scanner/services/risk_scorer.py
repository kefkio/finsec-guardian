"""Risk Scoring Engine — deterministic, explainable, tool-agnostic.

Converts normalised findings into an aggregate risk assessment using a
weighted multi-factor model:

    Score_i = W_severity × W_tool × (confidence / 100)

The individual scores are summed and mapped to a bounded 0–100 scale via
an exponential saturation function:

    Risk = 100 × (1 − e^{−k × S})

where *S* is the raw aggregate and *k* = 0.08 controls the curve steepness.

Design properties:
  • Deterministic — same findings always produce the same score.
  • Tool-agnostic — works identically for Slither, Mythril, and Echidna.
  • Explainable — every weight and threshold is justified in code.
"""

from __future__ import annotations

import math


class RiskScorer:
    """Compute a composite risk score from a list of normalised findings."""

    # Base severity weights (10-point scale).
    SEVERITY_WEIGHTS: dict[str, int] = {
        "critical": 10,
        "high": 7,
        "medium": 4,
        "low": 2,
        "info": 1,
    }

    # Tool reliability multipliers.
    # Echidna findings represent actual exploit evidence (highest weight).
    # Mythril uses symbolic execution with strong formal reasoning.
    # Slither is pattern-based static analysis (slightly lower precision).
    # Heuristic is regex-based logic-flaw detection (moderate precision).
    TOOL_WEIGHTS: dict[str, float] = {
        "slither": 0.9,
        "mythril": 1.0,
        "echidna": 1.2,
        "heuristic": 0.85,
    }

    # Echidna findings are runtime-verified exploits — additional boost.
    ECHIDNA_EXPLOIT_BOOST: float = 1.5

    # Exponential saturation scaling factor.
    SCALING_FACTOR: float = 0.08

    # A single critical finding guarantees at least this score.
    CRITICAL_FLOOR: float = 80.0

    # Diversity bonus: more unique issue types → higher risk.
    DIVERSITY_BONUS_PER_CATEGORY: float = 0.5
    DIVERSITY_BONUS_CAP: float = 5.0

    # Verdict thresholds (descending).
    VERDICT_THRESHOLDS: list[tuple[float, str]] = [
        (85.0, "CRITICAL RISK"),
        (70.0, "HIGH RISK"),
        (50.0, "MEDIUM RISK"),
        (25.0, "LOW RISK"),
    ]
    VERDICT_DEFAULT: str = "MINIMAL RISK"

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def compute(self, findings: list[dict], onchain_data: dict | None = None) -> dict:
        """Score a set of normalised findings.

        Parameters
        ----------
        findings:
            List of finding dicts, each containing at minimum:
            ``severity``, ``confidence``, and ``metadata.tool`` (or top-level ``tool``).
        onchain_data:
            Optional on-chain enrichment payload from the Etherscan layer.
            When present, the reputation ``risk_adjustment`` is folded into
            the composite score.

        Returns
        -------
        dict
            ``risk_score`` (int 0–100), ``verdict`` (str), ``confidence`` (int),
            ``breakdown`` (severity counts), ``tool_contributions`` (per-tool scores),
            ``total_findings`` (int), ``diversity_bonus`` (float),
            ``onchain_adjustment`` (float, only when on-chain data is present).
        """
        if not findings:
            return self._empty_result()

        total_score = 0.0
        breakdown: dict[str, int] = {}
        tool_contributions: dict[str, float] = {}
        confidence_values: list[int] = []

        for f in findings:
            severity = f.get("severity", "info")
            tool = self._extract_tool(f)
            confidence = self._clamp(f.get("confidence", 50), 0, 100)
            confidence_values.append(confidence)

            score = self._score_finding(severity, tool, confidence)

            total_score += score
            breakdown[severity] = breakdown.get(severity, 0) + 1
            tool_contributions[tool] = tool_contributions.get(tool, 0.0) + score

        # Diversity bonus — more unique issue categories raise the score.
        unique_titles = len({f.get("title", "") for f in findings})
        diversity_bonus = min(
            unique_titles * self.DIVERSITY_BONUS_PER_CATEGORY,
            self.DIVERSITY_BONUS_CAP,
        )
        total_score += diversity_bonus

        # Exponential saturation → bounded 0–100.
        risk_score = 100.0 * (1.0 - math.exp(-self.SCALING_FACTOR * total_score))

        # Critical override — one critical finding guarantees a floor score.
        if any(f.get("severity") == "critical" for f in findings):
            risk_score = max(risk_score, self.CRITICAL_FLOOR)

        # --- On-chain reputation adjustment (Etherscan layer) -----------
        onchain_adjustment = 0.0
        if onchain_data:
            reputation = onchain_data.get("reputation", {})
            onchain_adjustment = reputation.get("risk_adjustment", 0.0)
            # Clamp adjustment to ±15 so on-chain data can't dominate.
            onchain_adjustment = max(-15.0, min(15.0, onchain_adjustment))
            risk_score = max(0.0, min(100.0, risk_score + onchain_adjustment))

            # Suspicious patterns from on-chain analysis act as additional
            # risk factors even when no static findings exist.
            suspicious = onchain_data.get("suspicious_patterns", [])
            if suspicious:
                pattern_penalty = min(len(suspicious) * 3.0, 10.0)
                risk_score = min(100.0, risk_score + pattern_penalty)
                onchain_adjustment += pattern_penalty

        # Round tool contributions for clean output.
        tool_contributions = {
            k: round(v, 2) for k, v in tool_contributions.items()
        }

        # Average confidence across all findings.
        avg_confidence = round(sum(confidence_values) / len(confidence_values))

        result = {
            "risk_score": round(risk_score),
            "verdict": self._classify(risk_score),
            "confidence": avg_confidence,
            "breakdown": breakdown,
            "tool_contributions": tool_contributions,
            "total_findings": len(findings),
            "diversity_bonus": round(diversity_bonus, 2),
        }

        if onchain_data:
            result["onchain_adjustment"] = round(onchain_adjustment, 2)

        return result

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _score_finding(self, severity: str, tool: str, confidence: int) -> float:
        """Compute the weighted score for a single finding.

        Formula: W_severity × W_tool × (confidence / 100)
        With an additional boost for Echidna (runtime exploit evidence).
        """
        base = self.SEVERITY_WEIGHTS.get(severity, 1)
        tool_weight = self.TOOL_WEIGHTS.get(tool, 1.0)
        confidence_factor = confidence / 100.0

        score = base * tool_weight * confidence_factor

        if tool == "echidna":
            score *= self.ECHIDNA_EXPLOIT_BOOST

        return score

    def _classify(self, score: float) -> str:
        """Map a numeric risk score to a human-readable verdict."""
        for threshold, verdict in self.VERDICT_THRESHOLDS:
            if score >= threshold:
                return verdict
        return self.VERDICT_DEFAULT

    @staticmethod
    def _extract_tool(finding: dict) -> str:
        """Get the originating tool name from a normalised finding."""
        tool = finding.get("metadata", {}).get("tool", "")
        if not tool:
            tool = finding.get("tool", "unknown")
        return tool

    @staticmethod
    def _clamp(value: int, lo: int, hi: int) -> int:
        return max(lo, min(hi, value))

    @staticmethod
    def _empty_result() -> dict:
        return {
            "risk_score": 0,
            "verdict": "MINIMAL RISK",
            "confidence": 0,
            "breakdown": {},
            "tool_contributions": {},
            "total_findings": 0,
            "diversity_bonus": 0.0,
        }
