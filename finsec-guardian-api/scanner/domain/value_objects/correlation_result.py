from __future__ import annotations

from dataclasses import dataclass

from scanner.domain.exceptions import DomainValidationError


@dataclass(frozen=True, slots=True)
class CorrelationResult:
    """
    Immutable Value Object representing the result of a pairwise
    correlation assessment between two Findings.

    The score is normalized between 0.0 and 1.0 and is accompanied
    by human-readable reasons explaining why the findings were
    considered related.
    """

    score: float

    reasons: tuple[str, ...]

    def __post_init__(self) -> None:

        if not isinstance(self.score, (int, float)):
            raise DomainValidationError(
                "score must be numeric."
            )

        if not (0.0 <= self.score <= 1.0):
            raise DomainValidationError(
                "score must be between 0.0 and 1.0."
            )

        for reason in self.reasons:

            if not isinstance(reason, str):
                raise DomainValidationError(
                    "Correlation reasons must be strings."
                )

            if not reason.strip():
                raise DomainValidationError(
                    "Correlation reasons cannot be empty."
                )

    @property
    def is_identical(self) -> bool:
        """Returns True when two findings are semantically identical."""
        return self.score == 1.0

    @property
    def is_correlated(self) -> bool:
        """
        Returns True when the findings are considered
        sufficiently related.
        """
        return self.score >= 0.50

    @property
    def confidence(self) -> str:
        """
        Human-readable confidence category.
        """

        if self.score >= 0.90:
            return "very_high"

        if self.score >= 0.70:
            return "high"

        if self.score >= 0.50:
            return "medium"

        return "low"

    def __bool__(self) -> bool:
        return self.is_correlated