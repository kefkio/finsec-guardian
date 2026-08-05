from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from scanner.domain.entities import Finding
from scanner.domain.exceptions import DomainValidationError


@dataclass(frozen=True)
class CorrelationResult:
    """Detailed result of a pairwise correlation assessment."""

    score: float
    reasons: tuple[str, ...]


class FindingCorrelationService:
    """Stateless domain service responsible for discovering semantic

    relationships between security findings.
    """

    # Scoring Constants
    _CONTRACT_MATCH_SCORE: ClassVar[float] = 0.35
    _FILE_MATCH_SCORE: ClassVar[float] = 0.20
    _ANALYZER_MATCH_SCORE: ClassVar[float] = 0.10
    _SEVERITY_MATCH_SCORE: ClassVar[float] = 0.10

    _PROXIMITY_NEAR_SCORE: ClassVar[float] = 0.25
    _PROXIMITY_MEDIUM_SCORE: ClassVar[float] = 0.15
    _PROXIMITY_FAR_SCORE: ClassVar[float] = 0.05

    # Distance Thresholds (in lines)
    _NEAR_DISTANCE: ClassVar[int] = 5
    _MEDIUM_DISTANCE: ClassVar[int] = 15
    _FAR_DISTANCE: ClassVar[int] = 30

    # Bounds
    _MAX_SCORE: ClassVar[float] = 1.0

    # ==========================================================
    # Pairwise Correlation
    # ==========================================================

    @classmethod
    def correlate_pair(
        cls,
        left: Finding,
        right: Finding,
    ) -> CorrelationResult:
        """Calculate the semantic correlation score and explanation between two

        findings.
        """
        if not isinstance(left, Finding):
            raise DomainValidationError("'left' must be a Finding.")

        if not isinstance(right, Finding):
            raise DomainValidationError("'right' must be a Finding.")

        if left is right:
            return CorrelationResult(
                score=cls._MAX_SCORE, reasons=("Same finding instance",)
            )

        if left.signature == right.signature:
            return CorrelationResult(
                score=cls._MAX_SCORE,
                reasons=("Matching vulnerability signature",),
            )

        reasons: list[str] = []
        score = 0.0

        contract_score = cls._contract_score(left, right)
        if contract_score > 0:
            score += contract_score
            reasons.append("Same smart contract")

        file_score = cls._file_score(left, right)
        if file_score > 0:
            score += file_score
            reasons.append("Same source file")

        analyzer_score = cls._analyzer_score(left, right)
        if analyzer_score > 0:
            score += analyzer_score
            reasons.append("Same analyzer")

        severity_score = cls._severity_score(left, right)
        if severity_score > 0:
            score += severity_score
            reasons.append("Same severity level")

        proximity_score, proximity_reason = cls._proximity_score(left, right)
        if proximity_score > 0:
            score += proximity_score
            if proximity_reason:
                reasons.append(proximity_reason)

        final_score = round(min(score, cls._MAX_SCORE), 2)
        return CorrelationResult(score=final_score, reasons=tuple(reasons))

    # ==========================================================
    # Scoring Rules
    # ==========================================================

    @classmethod
    def _contract_score(cls, left: Finding, right: Finding) -> float:
        left_contract = getattr(left.location, "contract_name", None)
        right_contract = getattr(right.location, "contract_name", None)

        if left_contract and right_contract and left_contract == right_contract:
            return cls._CONTRACT_MATCH_SCORE

        return 0.0

    @classmethod
    def _file_score(cls, left: Finding, right: Finding) -> float:
        if left.location.filename == right.location.filename:
            return cls._FILE_MATCH_SCORE
        return 0.0

    @classmethod
    def _analyzer_score(cls, left: Finding, right: Finding) -> float:
        if left.analyzer == right.analyzer:
            return cls._ANALYZER_MATCH_SCORE
        return 0.0

    @classmethod
    def _severity_score(cls, left: Finding, right: Finding) -> float:
        if left.severity == right.severity:
            return cls._SEVERITY_MATCH_SCORE
        return 0.0

    @classmethod
    def _proximity_score(
        cls, left: Finding, right: Finding
    ) -> tuple[float, str | None]:
        if left.location.filename != right.location.filename:
            return 0.0, None

        distance = abs(left.location.line - right.location.line)

        if distance <= cls._NEAR_DISTANCE:
            return cls._PROXIMITY_NEAR_SCORE, "Immediate proximity (<= 5 lines)"
        if distance <= cls._MEDIUM_DISTANCE:
            return cls._PROXIMITY_MEDIUM_SCORE, "Close proximity (<= 15 lines)"
        if distance <= cls._FAR_DISTANCE:
            return cls._PROXIMITY_FAR_SCORE, "Same file proximity (<= 30 lines)"

        return 0.0, None