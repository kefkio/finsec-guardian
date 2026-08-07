from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from scanner.domain.entities import Finding
from scanner.domain.enums import Severity
from scanner.domain.exceptions import DomainValidationError
from scanner.domain.value_objects.correlation_edge import CorrelationEdge


@dataclass(frozen=True, slots=True)
class CorrelationComponent:
    """
    Immutable Value Object representing a connected sub-graph component of findings.
    Encapsulates structural metrics, edge relationships, entry finding identification,
    and finding membership.
    """

    findings: tuple[Finding, ...]
    edges: tuple[CorrelationEdge, ...]
    entry_finding_id: UUID
    density: float
    average_correlation_score: float

    def __post_init__(self) -> None:
        if not self.findings:
            raise DomainValidationError(
                "CorrelationComponent must contain at least one Finding."
            )

        if not isinstance(self.entry_finding_id, UUID):
            raise DomainValidationError(
                "entry_finding_id must be a UUID."
            )

        finding_ids = {finding.id for finding in self.findings}
        if self.entry_finding_id not in finding_ids:
            raise DomainValidationError(
                "entry_finding_id must belong to the component findings."
            )

    @classmethod
    def create(
        cls,
        findings: tuple[Finding, ...],
        edges: tuple[CorrelationEdge, ...],
        entry_finding_id: UUID,
    ) -> CorrelationComponent:
        """
        Factory method computing component metrics upon instantiation.
        """
        node_count = len(findings)
        edge_count = len(edges)

        # Calculate graph density for undirected sub-graph: 2E / (V * (V - 1))
        if node_count <= 1:
            density = 0.0
        else:
            max_possible_edges = (node_count * (node_count - 1)) / 2.0
            density = round(edge_count / max_possible_edges, 4)

        # Calculate average correlation score (0.0 if no correlation edges exist)
        if edge_count == 0:
            avg_correlation_score = 0.0
        else:
            avg_correlation_score = round(
                sum(edge.score for edge in edges) / edge_count, 4
            )

        return cls(
            findings=findings,
            edges=edges,
            entry_finding_id=entry_finding_id,
            density=density,
            average_correlation_score=avg_correlation_score,
        )

    # ==========================================================
    # Entity Accessors & Derived Properties
    # ==========================================================

    @property
    def entry_finding(self) -> Finding:
        """Returns the primary entry Finding entity for this component."""
        return next(
            finding
            for finding in self.findings
            if finding.id == self.entry_finding_id
        )

    @property
    def node_count(self) -> int:
        return len(self.findings)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    @property
    def is_isolated(self) -> bool:
        """Returns True if this component consists of a single isolated finding."""
        return self.node_count == 1 and self.edge_count == 0

    @property
    def highest_severity(self) -> Severity:
        """Returns the highest Severity level present across member findings."""
        return max(self.findings, key=lambda f: f.severity.weight).severity

    @property
    def highest_risk(self) -> float:
        """Returns the maximum risk score evaluated across member findings."""
        return max(getattr(f, "risk_score", 0.0) for f in self.findings)

    @property
    def complexity(self) -> str:
        """Categorizes path complexity for analytics and threat modeling."""
        if self.node_count <= 2:
            return "simple"
        if self.node_count <= 5:
            return "moderate"
        return "complex"

    @property
    def sort_key(self) -> tuple[float, int, int]:
        """Deterministic sort key: Highest correlation score first, largest node/edge count second."""
        return (
            -self.average_correlation_score,
            -self.node_count,
            -self.edge_count,
        )