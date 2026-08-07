from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

from scanner.domain.exceptions import DomainValidationError

STRONG_CORRELATION_THRESHOLD = 0.80
MEDIUM_CORRELATION_THRESHOLD = 0.50


@dataclass(frozen=True, slots=True)
class CorrelationEdge:
    """
    Immutable Value Object representing a semantic relationship
    between two Findings in the correlation graph.
    """

    source_finding_id: UUID
    target_finding_id: UUID

    score: float

    reasons: tuple[str, ...] = ()

    is_directed: bool = False

    def __post_init__(self) -> None:

        if not isinstance(self.source_finding_id, UUID):
            raise DomainValidationError(
                "source_finding_id must be a UUID."
            )

        if not isinstance(self.target_finding_id, UUID):
            raise DomainValidationError(
                "target_finding_id must be a UUID."
            )

        if self.source_finding_id == self.target_finding_id:
            raise DomainValidationError(
                "CorrelationEdge cannot connect a finding to itself."
            )

        if (
            not isinstance(self.score, (int, float))
            or not (0.0 <= self.score <= 1.0)
        ):
            raise DomainValidationError(
                "score must be between 0.0 and 1.0."
            )

        object.__setattr__(self, "score", float(self.score))

        if not isinstance(self.is_directed, bool):
            raise DomainValidationError(
                "is_directed must be a boolean."
            )

        normalized_reasons = self._normalize_reasons(self.reasons)
        object.__setattr__(self, "reasons", normalized_reasons)

    @classmethod
    def _normalize_reasons(cls, reasons: Iterable[str]) -> tuple[str, ...]:
        """Validates, strips, and deduplicates reasoning statements."""
        if isinstance(reasons, (str, bytes)) or not isinstance(reasons, Iterable):
            raise DomainValidationError(
                "reasons must be an iterable of non-empty strings."
            )

        cleaned: list[str] = []
        for reason in reasons:
            if not isinstance(reason, str):
                raise DomainValidationError(
                    "All reasons must be strings."
                )
            stripped = reason.strip()
            if not stripped:
                raise DomainValidationError(
                    "reason elements cannot be empty or whitespace."
                )
            cleaned.append(stripped)

        return tuple(dict.fromkeys(cleaned))

    # ==========================================================
    # Graph Identity & Structure Properties
    # ==========================================================

    @property
    def key(self) -> tuple[UUID, UUID]:
        """
        Canonical identifier for the edge.
        Preserves orientation if directed, otherwise returns sorted endpoints.
        """
        if self.is_directed or self.source_finding_id <= self.target_finding_id:
            return (self.source_finding_id, self.target_finding_id)
        return (self.target_finding_id, self.source_finding_id)

    @property
    def endpoints(self) -> tuple[UUID, UUID]:
        """Returns the ordered (source, target) tuple of finding IDs."""
        return (
            self.source_finding_id,
            self.target_finding_id,
        )

    @property
    def nodes(self) -> frozenset[UUID]:
        """Returns the set of endpoint finding UUIDs connected by this edge."""
        return frozenset(
            (
                self.source_finding_id,
                self.target_finding_id,
            )
        )

    # ==========================================================
    # Metrics & Categorization Properties
    # ==========================================================

    @property
    def is_strong(self) -> bool:
        return self.score >= STRONG_CORRELATION_THRESHOLD

    @property
    def is_medium(self) -> bool:
        return (
            MEDIUM_CORRELATION_THRESHOLD
            <= self.score
            < STRONG_CORRELATION_THRESHOLD
        )

    @property
    def is_weak(self) -> bool:
        return self.score < MEDIUM_CORRELATION_THRESHOLD

    @property
    def strength(self) -> str:
        """Returns string representation of the correlation strength."""
        if self.is_strong:
            return "strong"
        if self.is_medium:
            return "medium"
        return "weak"

    @property
    def has_reasoning(self) -> bool:
        return bool(self.reasons)

    @property
    def sort_key(self) -> tuple[float, int]:
        """
        Tuple for sorting edges deterministically:
        Highest score first (-score), most reasons second (-len).
        """
        return (-self.score, -len(self.reasons))

    # ==========================================================
    # Graph Query Behaviors
    # ==========================================================

    def connects(self, finding_id: UUID) -> bool:
        """Returns True if the given finding_id is an endpoint of this edge."""
        return finding_id in (self.source_finding_id, self.target_finding_id)

    def connects_pair(self, left: UUID, right: UUID) -> bool:
        """
        Returns True if this edge connects the specified pair of finding IDs.
        Respects orientation if is_directed is True.
        """
        if self.is_directed:
            return (
                self.source_finding_id == left
                and self.target_finding_id == right
            )
        return self.nodes == frozenset((left, right))

    def other_endpoint(self, finding_id: UUID) -> UUID:
        """Given one endpoint UUID, returns the opposite endpoint UUID."""
        if finding_id == self.source_finding_id:
            return self.target_finding_id
        if finding_id == self.target_finding_id:
            return self.source_finding_id
        raise DomainValidationError(
            f"Finding ID {finding_id} is not an endpoint of this edge."
        )