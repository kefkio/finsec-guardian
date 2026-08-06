from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TypeVar
from uuid import UUID

from scanner.domain.enums import RiskLevel
from scanner.domain.exceptions import DomainValidationError

_CONFIDENT_THRESHOLD: float = 0.75
T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class AttackPath:
    """
    Immutable Value Object representing a potential attack path
    discovered from correlated security findings.
    """

    identifier: str
    title: str
    description: str

    risk_level: RiskLevel

    finding_ids: tuple[UUID, ...]

    entry_finding_id: UUID
    impact_finding_id: UUID

    confidence: float
    score: float

    reasoning: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        # 1. Field validation & whitespace stripping
        self._validate_and_strip("identifier", self.identifier)
        self._validate_and_strip("title", self.title)
        self._validate_and_strip("description", self.description)

        # 2. Enum type validation
        if not isinstance(self.risk_level, RiskLevel):
            raise DomainValidationError("risk_level must be a RiskLevel enum.")

        # 3. Finding IDs collection validation & uniqueness check
        finding_ids_tuple = self._ensure_tuple_of_type(
            self.finding_ids, UUID, "finding_ids"
        )
        object.__setattr__(self, "finding_ids", finding_ids_tuple)

        if not self.finding_ids:
            raise DomainValidationError(
                "AttackPath must contain at least one finding ID."
            )

        if len(set(self.finding_ids)) != len(self.finding_ids):
            raise DomainValidationError("finding_ids must contain unique elements.")

        # 4. Entry / Impact UUID presence checks
        if not isinstance(self.entry_finding_id, UUID):
            raise DomainValidationError("entry_finding_id must be a UUID.")

        if not isinstance(self.impact_finding_id, UUID):
            raise DomainValidationError("impact_finding_id must be a UUID.")

        if self.entry_finding_id not in self.finding_ids:
            raise DomainValidationError("entry_finding_id must exist in finding_ids.")

        if self.impact_finding_id not in self.finding_ids:
            raise DomainValidationError("impact_finding_id must exist in finding_ids.")

        # 5. Range checks (unbounded upper score limit)
        if not isinstance(self.confidence, (int, float)) or not (
            0.0 <= self.confidence <= 1.0
        ):
            raise DomainValidationError(
                "confidence must be a float between 0.0 and 1.0."
            )

        if not isinstance(self.score, (int, float)) or self.score < 0.0:
            raise DomainValidationError("score must be a non-negative number.")

        # 6. Reasoning tuple coercion
        reasoning_tuple = self._ensure_tuple_of_type(
            self.reasoning, str, "reasoning"
        )
        object.__setattr__(self, "reasoning", reasoning_tuple)

        for reason in self.reasoning:
            self._validate_non_empty("reason", reason)

    # ==========================================================
    # Validation Helpers (Python 3.10 Compatible)
    # ==========================================================

    def _validate_and_strip(self, field_name: str, value: str) -> None:
        self._validate_non_empty(field_name, value)
        object.__setattr__(self, field_name, value.strip())

    @staticmethod
    def _validate_non_empty(field_name: str, value: str) -> None:
        if not isinstance(value, str):
            raise DomainValidationError(f"{field_name} must be a string.")

        if not value.strip():
            raise DomainValidationError(f"{field_name} cannot be empty.")

    @staticmethod
    def _ensure_tuple_of_type(
        value: Iterable[T], expected_type: type[T], field_name: str
    ) -> tuple[T, ...]:
        if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
            raise DomainValidationError(
                f"{field_name} must be an iterable of {expected_type.__name__}."
            )

        items = tuple(value)
        for item in items:
            if not isinstance(item, expected_type):
                raise DomainValidationError(
                    f"All elements in {field_name} must be instances of {expected_type.__name__}."
                )

        return items

    # ==========================================================
    # Identity & Accessors
    # ==========================================================

    @property
    def key(self) -> str:
        """Canonical identifier for the value object."""
        return self.identifier

    @property
    def entry_point(self) -> UUID:
        return self.entry_finding_id

    @property
    def impact_point(self) -> UUID:
        return self.impact_finding_id

    # ==========================================================
    # Derived Properties & Metrics
    # ==========================================================

    @property
    def findings_count(self) -> int:
        return len(self.finding_ids)

    @property
    def step_count(self) -> int:
        return self.findings_count

    @property
    def spans_multiple_findings(self) -> bool:
        return self.findings_count > 1

    @property
    def is_single_stage(self) -> bool:
        return self.findings_count == 1

    @property
    def is_multi_stage(self) -> bool:
        return self.findings_count > 1

    @property
    def is_complex(self) -> bool:
        return self.findings_count >= 3

    # ==========================================================
    # Scoring & Ordering Helpers
    # ==========================================================

    @property
    def normalized_score(self) -> float:
        return self.score / max(self.findings_count, 1)

    @property
    def severity_rank(self) -> int:
        return self.risk_level.weight

    @property
    def is_confident(self) -> bool:
        return self.confidence >= _CONFIDENT_THRESHOLD

    # ==========================================================
    # Risk Level Predicates
    # ==========================================================

    @property
    def has_reasoning(self) -> bool:
        return bool(self.reasoning)

    @property
    def is_critical_risk(self) -> bool:
        return self.risk_level is RiskLevel.CRITICAL

    @property
    def is_high_risk(self) -> bool:
        return self.risk_level is RiskLevel.HIGH

    @property
    def is_medium_risk(self) -> bool:
        return self.risk_level is RiskLevel.MEDIUM

    @property
    def is_low_risk(self) -> bool:
        return self.risk_level is RiskLevel.LOW

    @property
    def is_info_risk(self) -> bool:
        return self.risk_level is RiskLevel.INFO