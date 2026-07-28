from __future__ import annotations

from dataclasses import dataclass

from scanner.domain.entities import Entity
from scanner.domain.enums import (
    AnalyzerType,
    Confidence,
    RiskLevel,
    Severity,
)
from scanner.domain.exceptions import DomainValidationError
from scanner.domain.value_objects.source_location import SourceLocation


@dataclass(eq=False, slots=True)
class Finding(Entity):
    """
    Represents a security finding identified during
    smart contract analysis.

    A Finding is the central domain entity within the
    scanning bounded context. It captures the details
    of a vulnerability or issue reported by a security
    analyzer.
    """

    title: str
    description: str
    recommendation: str

    severity: Severity
    confidence: Confidence
    risk_level: RiskLevel

    analyzer: AnalyzerType

    location: SourceLocation

def __post_init__(self) -> None:
    """
    Validate the integrity of the finding.
    """
    self._validate_text_fields()
    self._validate_enums()
    self._validate_location()
    self._validate_business_rules()

def _validate_text_fields(self) -> None:
    """
    Validate all textual fields.
    """
    fields = {
        "Title": self.title,
        "Description": self.description,
        "Recommendation": self.recommendation,
    }

    for name, value in fields.items():
        if not value.strip():
            raise DomainValidationError(
                f"{name} cannot be empty."
            )

    if len(self.title) > 200:
        raise DomainValidationError(
            "Title cannot exceed 200 characters."
        )
    
    
def _validate_enums(self) -> None:
    """
    Validate enumeration fields.
    """
    if not isinstance(self.severity, Severity):
        raise DomainValidationError(
            "Invalid severity."
        )

    if not isinstance(self.confidence, Confidence):
        raise DomainValidationError(
            "Invalid confidence."
        )

    if not isinstance(self.risk_level, RiskLevel):
        raise DomainValidationError(
            "Invalid risk level."
        )

    if not isinstance(self.analyzer, AnalyzerType):
        raise DomainValidationError(
            "Invalid analyzer."
        )
    
def _validate_location(self) -> None:
    """
    Validate the source location.
    """
    if not isinstance(self.location, SourceLocation):
        raise DomainValidationError(
            "Invalid source location."
        )
    
def _validate_business_rules(self) -> None:
    """
    Validate business invariants.
    """

    if (
        self.severity is Severity.CRITICAL
        and self.risk_level is not RiskLevel.CRITICAL
    ):
        raise DomainValidationError(
            "Critical findings must have a "
            "critical risk level."
        )


def summary(self) -> str:
    """
    Returns a concise human-readable summary of the finding.
    """
    return (
        f"[{self.severity.display_name}] "
        f"{self.title} "
        f"({self.location})"
    )

def matches(self, other: "Finding") -> bool:
    """
    Returns True if two findings represent
    the same security issue.
    """
    if not isinstance(other, Finding):
        return False

    return (
        self.fingerprint == other.fingerprint
    )

def same_location(self, other: "Finding") -> bool:
    """
    Returns True if both findings occur at
    the same source location.
    """
    if not isinstance(other, Finding):
        return False

    return self.location == other.location

def same_analyzer(self, other: "Finding") -> bool:
    """
    Returns True if both findings were produced
    by the same analyzer.
    """
    if not isinstance(other, Finding):
        return False

    return self.analyzer is other.analyzer