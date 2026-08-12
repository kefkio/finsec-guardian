from __future__ import annotations

import math
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

    An AttackPath represents a correlated sequence or group of findings
    that collectively indicate a potential security attack chain.
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
        # ======================================================
        # 1. Textual Fields
        # ======================================================

        self._validate_and_strip("identifier", self.identifier)
        self._validate_and_strip("title", self.title)
        self._validate_and_strip("description", self.description)

        # ======================================================
        # 2. Risk Level
        # ======================================================

        if not isinstance(self.risk_level, RiskLevel):
            raise DomainValidationError(
                "risk_level must be a RiskLevel enum."
            )

        # ======================================================
        # 3. Finding IDs
        # ======================================================

        finding_ids = self._ensure_tuple_of_type(
            self.finding_ids,
            UUID,
            "finding_ids",
        )

        if not finding_ids:
            raise DomainValidationError(
                "AttackPath must contain at least one finding ID."
            )

        if len(set(finding_ids)) != len(finding_ids):
            raise DomainValidationError(
                "finding_ids must contain unique elements."
            )

        object.__setattr__(
            self,
            "finding_ids",
            finding_ids,
        )

        # ======================================================
        # 4. Entry / Impact Findings
        # ======================================================

        self._validate_uuid(
            self.entry_finding_id,
            "entry_finding_id",
        )

        self._validate_uuid(
            self.impact_finding_id,
            "impact_finding_id",
        )

        if self.entry_finding_id not in self.finding_ids:
            raise DomainValidationError(
                "entry_finding_id must exist in finding_ids."
            )

        if self.impact_finding_id not in self.finding_ids:
            raise DomainValidationError(
                "impact_finding_id must exist in finding_ids."
            )

        # ======================================================
        # 5. Confidence
        # ======================================================

        confidence = self._validate_number(
            self.confidence,
            "confidence",
        )

        if not 0.0 <= confidence <= 1.0:
            raise DomainValidationError(
                "confidence must be between 0.0 and 1.0."
            )

        object.__setattr__(
            self,
            "confidence",
            confidence,
        )

        # ======================================================
        # 6. Score
        # ======================================================

        score = self._validate_number(
            self.score,
            "score",
        )

        if score < 0.0:
            raise DomainValidationError(
                "score must be a non-negative number."
            )

        object.__setattr__(
            self,
            "score",
            score,
        )

        # ======================================================
        # 7. Reasoning
        # ======================================================

        reasoning = self._ensure_tuple_of_type(
            self.reasoning,
            str,
            "reasoning",
        )

        cleaned_reasoning = tuple(
            self._clean_reason(reason, "reason")
            for reason in reasoning
        )

        object.__setattr__(
            self,
            "reasoning",
            cleaned_reasoning,
        )

    # ==========================================================
    # Validation Helpers
    # ==========================================================

    def _validate_and_strip(
        self,
        field_name: str,
        value: str,
    ) -> None:
        """
        Validate a textual field and replace it with its
        whitespace-normalized representation.
        """
        self._validate_non_empty(field_name, value)

        object.__setattr__(
            self,
            field_name,
            value.strip(),
        )

    @staticmethod
    def _validate_non_empty(
        field_name: str,
        value: str,
    ) -> None:
        if not isinstance(value, str):
            raise DomainValidationError(
                f"{field_name} must be a string."
            )

        if not value.strip():
            raise DomainValidationError(
                f"{field_name} cannot be empty."
            )

    @staticmethod
    def _clean_reason(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise DomainValidationError(
                f"{field_name} must be a string."
            )

        cleaned = value.strip()

        if not cleaned:
            raise DomainValidationError(
                f"{field_name} cannot be empty."
            )

        return cleaned

    @staticmethod
    def _validate_uuid(
        value: object,
        field_name: str,
    ) -> None:
        if not isinstance(value, UUID):
            raise DomainValidationError(
                f"{field_name} must be a UUID."
            )

    @staticmethod
    def _validate_number(
        value: object,
        field_name: str,
    ) -> float:
        """
        Validate and normalize a numeric domain value.

        bool is explicitly rejected because bool is a subclass of int
        in Python.
        """
        if isinstance(value, bool) or not isinstance(
            value,
            (int, float),
        ):
            raise DomainValidationError(
                f"{field_name} must be a number."
            )

        numeric_value = float(value)

        if not math.isfinite(numeric_value):
            raise DomainValidationError(
                f"{field_name} must be a finite number."
            )

        return numeric_value

    @staticmethod
    def _ensure_tuple_of_type(
        value: Iterable[T],
        expected_type: type[T],
        field_name: str,
    ) -> tuple[T, ...]:
        """
        Normalize an iterable into an immutable tuple while validating
        every element.
        """
        if isinstance(value, (str, bytes)) or not isinstance(
            value,
            Iterable,
        ):
            raise DomainValidationError(
                f"{field_name} must be an iterable of "
                f"{expected_type.__name__}."
            )

        try:
            items = tuple(value)
        except TypeError as exc:
            raise DomainValidationError(
                f"{field_name} must be an iterable of "
                f"{expected_type.__name__}."
            ) from exc

        for item in items:
            if not isinstance(item, expected_type):
                raise DomainValidationError(
                    f"All elements in {field_name} must be "
                    f"instances of {expected_type.__name__}."
                )

        return items

    # ==========================================================
    # Identity & Accessors
    # ==========================================================

    @property
    def key(self) -> str:
        """
        Canonical identifier for the AttackPath.
        """
        return self.identifier

    @property
    def entry_point(self) -> UUID:
        """
        Alias for the entry finding identifier.
        """
        return self.entry_finding_id

    @property
    def impact_point(self) -> UUID:
        """
        Alias for the impact finding identifier.
        """
        return self.impact_finding_id

    # ==========================================================
    # Structural Metrics
    # ==========================================================

    @property
    def findings_count(self) -> int:
        """
        Number of findings participating in the attack path.
        """
        return len(self.finding_ids)

    @property
    def step_count(self) -> int:
        """
        Number of findings/stages represented by the attack path.
        """
        return self.findings_count

    @property
    def spans_multiple_findings(self) -> bool:
        """
        True when the attack path contains more than one finding.
        """
        return self.findings_count > 1

    @property
    def is_single_stage(self) -> bool:
        return self.findings_count == 1

    @property
    def is_multi_stage(self) -> bool:
        return self.findings_count > 1

    @property
    def is_complex(self) -> bool:
        """
        A path containing three or more findings is considered complex.
        """
        return self.findings_count >= 3

    # ==========================================================
    # Scoring & Confidence
    # ==========================================================

    @property
    def normalized_score(self) -> float:
        """
        Score normalized by the number of findings participating
        in the attack path.
        """
        return self.score / self.findings_count

    @property
    def severity_rank(self) -> int:
        """
        Numeric priority of the path's RiskLevel.
        """
        return self.risk_level.weight

    @property
    def risk_priority(self) -> int:
        """
        Explicit alias for the RiskLevel priority.
        """
        return self.risk_level.priority

    @property
    def is_confident(self) -> bool:
        """
        True when confidence meets the domain confidence threshold.
        """
        return self.confidence >= _CONFIDENT_THRESHOLD

    # ==========================================================
    # Reasoning
    # ==========================================================

    @property
    def has_reasoning(self) -> bool:
        return bool(self.reasoning)

    # ==========================================================
    # Risk Predicates
    # ==========================================================

    @property
    def is_critical_risk(self) -> bool:
        """
        True only for CRITICAL risk.
        """
        return self.risk_level is RiskLevel.CRITICAL

    @property
    def is_high_risk(self) -> bool:
        """
        True for HIGH and CRITICAL risk levels.
        Delegates categorization to RiskLevel.
        """
        return self.risk_level.is_high_risk

    @property
    def is_medium_risk(self) -> bool:
        """
        True only for MEDIUM risk.
        """
        return self.risk_level.is_medium_risk

    @property
    def is_low_risk(self) -> bool:
        """
        True for VERY_LOW and LOW risk levels.
        Delegates categorization to RiskLevel.
        """
        return self.risk_level.is_low_risk

    @property
    def is_info_risk(self) -> bool:
        """
        Compatibility/convenience predicate for informational findings.

        RiskLevel does not contain an INFO member. Informational findings
        map to RiskLevel.VERY_LOW.
        """
        return self.risk_level is RiskLevel.VERY_LOW

    @property
    def is_very_low_risk(self) -> bool:
        """Return True when the attack path has VERY_LOW risk."""
        return self.risk_level is RiskLevel.VERY_LOW