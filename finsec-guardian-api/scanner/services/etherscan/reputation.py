"""Etherscan reputation scorer — computes a reputation score from on-chain insights.

Maps behavioral indicators (transaction volume, failure rate, caller
diversity, value flows, contract age, suspicious patterns) into a single
0–100 **reputation score** and a human-readable verdict.

A *higher* reputation score means the contract appears *more trustworthy*
based on on-chain behaviour.  This is the *inverse* of a risk score:

    risk_adjustment = 100 - reputation_score

The adjustment is merged into the RiskScorer's composite calculation by
the orchestrator, allowing on-chain behaviour to raise or lower the
overall risk assessment.

Scoring Factors:
  ┌──────────────────────────────────┬────────┬───────────┐
  │ Factor                           │ Weight │ Direction │
  ├──────────────────────────────────┼────────┼───────────┤
  │ Contract age (maturity)          │ 15     │ +rep      │
  │ Transaction volume               │ 10     │ +rep      │
  │ Failure rate                     │ 20     │ −rep      │
  │ Suspicious patterns detected     │ 25     │ −rep      │
  │ High-value transaction exposure  │ 15     │ −rep      │
  │ Caller diversity (unique callers)│ 10     │ +rep      │
  │ Verification status              │  5     │ +rep      │
  └──────────────────────────────────┴────────┴───────────┘
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .analyzer import OnChainInsights

logger = logging.getLogger(__name__)


@dataclass
class ReputationResult:
    """Output of the reputation scoring layer."""

    reputation_score: int = 50  # 0–100 (higher = more trustworthy)
    verdict: str = "UNKNOWN"
    factors: dict[str, float] = None  # factor name → contribution
    risk_adjustment: float = 0.0  # signed value added to risk score

    def __post_init__(self):
        if self.factors is None:
            self.factors = {}


class ReputationScorer:
    """Compute a reputation score from ``OnChainInsights``."""

    # Verdict thresholds (descending).
    VERDICT_THRESHOLDS: list[tuple[int, str]] = [
        (80, "HIGH REPUTATION"),
        (60, "MODERATE REPUTATION"),
        (40, "LOW REPUTATION"),
        (20, "POOR REPUTATION"),
    ]
    VERDICT_DEFAULT: str = "VERY POOR REPUTATION"

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def score(self, insights: OnChainInsights) -> ReputationResult:
        """Compute reputation from on-chain insights.

        Returns a ``ReputationResult`` with a 0–100 score and a signed
        ``risk_adjustment`` that the RiskScorer can add to the final risk.
        """
        if not insights or insights.tx_count == 0:
            return ReputationResult(
                reputation_score=50,
                verdict="INSUFFICIENT DATA",
                factors={"note": "No on-chain transactions available"},
                risk_adjustment=0.0,
            )

        factors: dict[str, float] = {}
        total = 0.0

        # 1. Contract age — older contracts with activity are more trusted.
        age_score = self._score_age(insights.contract_age_days)
        factors["contract_age"] = age_score
        total += age_score * 0.15

        # 2. Transaction volume — healthy activity signal.
        volume_score = self._score_volume(insights.tx_count)
        factors["tx_volume"] = volume_score
        total += volume_score * 0.10

        # 3. Failure rate — high failure rate is a red flag.
        failure_score = self._score_failure_rate(insights.failure_rate)
        factors["failure_rate"] = failure_score
        total += failure_score * 0.20

        # 4. Suspicious patterns — direct penalty.
        pattern_score = self._score_suspicious_patterns(
            len(insights.suspicious_patterns),
        )
        factors["suspicious_patterns"] = pattern_score
        total += pattern_score * 0.25

        # 5. High-value exposure — more high-value txs = more risk surface.
        hv_score = self._score_high_value(
            insights.high_value_tx_count, insights.tx_count,
        )
        factors["high_value_exposure"] = hv_score
        total += hv_score * 0.15

        # 6. Caller diversity — many unique callers = broader trust.
        diversity_score = self._score_caller_diversity(insights.unique_callers)
        factors["caller_diversity"] = diversity_score
        total += diversity_score * 0.10

        # 7. Verification bonus — verified source code.
        verification_bonus = 100.0 if getattr(insights, "_is_verified", False) else 0.0
        # We don't have direct access here; default to neutral.
        # The orchestrator can override via insights.warnings check.
        factors["verification"] = 50.0  # neutral default
        total += 50.0 * 0.05

        reputation_score = max(0, min(100, round(total)))

        # Risk adjustment: reputation < 50 raises risk, > 50 lowers it.
        # Scale: ±15 points max influence on the composite risk score.
        risk_adjustment = round((50 - reputation_score) * 0.30, 2)

        verdict = self._classify(reputation_score)

        return ReputationResult(
            reputation_score=reputation_score,
            verdict=verdict,
            factors={k: round(v, 2) for k, v in factors.items()},
            risk_adjustment=risk_adjustment,
        )

    # ------------------------------------------------------------------
    # Factor scoring (each returns 0–100)
    # ------------------------------------------------------------------

    @staticmethod
    def _score_age(age_days: int) -> float:
        """Older contracts are generally more trusted (diminishing returns)."""
        if age_days >= 365:
            return 100.0
        if age_days >= 180:
            return 80.0
        if age_days >= 90:
            return 60.0
        if age_days >= 30:
            return 40.0
        if age_days >= 7:
            return 20.0
        return 5.0

    @staticmethod
    def _score_volume(tx_count: int) -> float:
        """More transactions indicate real usage (diminishing returns)."""
        if tx_count >= 10000:
            return 100.0
        if tx_count >= 1000:
            return 80.0
        if tx_count >= 100:
            return 60.0
        if tx_count >= 10:
            return 40.0
        return 20.0

    @staticmethod
    def _score_failure_rate(rate: float) -> float:
        """Lower failure rate = higher reputation score."""
        if rate <= 0.01:
            return 100.0
        if rate <= 0.05:
            return 80.0
        if rate <= 0.10:
            return 60.0
        if rate <= 0.20:
            return 40.0
        if rate <= 0.40:
            return 20.0
        return 0.0

    @staticmethod
    def _score_suspicious_patterns(count: int) -> float:
        """More suspicious patterns = lower reputation."""
        if count == 0:
            return 100.0
        if count == 1:
            return 60.0
        if count == 2:
            return 40.0
        if count <= 4:
            return 20.0
        return 0.0

    @staticmethod
    def _score_high_value(hv_count: int, total_tx: int) -> float:
        """High-value transactions relative to total activity."""
        if total_tx == 0:
            return 50.0
        ratio = hv_count / total_tx
        if ratio <= 0.01:
            return 100.0
        if ratio <= 0.05:
            return 70.0
        if ratio <= 0.15:
            return 50.0
        if ratio <= 0.30:
            return 30.0
        return 10.0

    @staticmethod
    def _score_caller_diversity(unique_callers: int) -> float:
        """More unique callers indicates broader community trust."""
        if unique_callers >= 1000:
            return 100.0
        if unique_callers >= 100:
            return 80.0
        if unique_callers >= 20:
            return 60.0
        if unique_callers >= 5:
            return 40.0
        return 20.0

    def _classify(self, score: int) -> str:
        for threshold, verdict in self.VERDICT_THRESHOLDS:
            if score >= threshold:
                return verdict
        return self.VERDICT_DEFAULT
