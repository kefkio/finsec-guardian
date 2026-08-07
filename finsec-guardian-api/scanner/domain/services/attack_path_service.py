from __future__ import annotations

from typing import Sequence

from scanner.domain.entities import Finding
from scanner.domain.enums import RiskLevel
from scanner.domain.services.finding_correlation_service import (
    FindingCorrelationService,
)
from scanner.domain.services.fingerprint_service import FingerprintService
from scanner.domain.value_objects.attack_path import AttackPath
from scanner.domain.value_objects.correlation_component import (
    CorrelationComponent,
)
from scanner.domain.value_objects.correlation_edge import CorrelationEdge
from scanner.domain.value_objects.correlation_graph import CorrelationGraph


class AttackPathService:
    """
    Domain Service responsible for discovering attack paths from
    correlated findings.

    This service orchestrates the attack-path discovery pipeline by
    composing existing domain services and value objects.

        Findings
            │
            ▼
    FindingCorrelationService
            │
            ▼
      CorrelationEdge(s)
            │
            ▼
      CorrelationGraph
            │
            ▼
    CorrelationComponent(s)
            │
            ▼
        AttackPath(s)

    The service intentionally contains only lightweight V2 heuristics.
    More advanced scoring, traversal, reasoning and AI-assisted
    analysis will be delegated to specialized services in Version 3.
    """

    @classmethod
    def discover(
        cls,
        findings: Sequence[Finding],
    ) -> tuple[AttackPath, ...]:
        """
        Discover attack paths from a collection of findings.
        """
        if not findings:
            return ()

        findings_tuple = tuple(findings)

        edges = cls._build_edges(findings_tuple)

        graph = CorrelationGraph.from_findings_and_edges(
            findings=findings_tuple,
            edges=edges,
        )

        attack_paths = tuple(
            cls._map_component_to_attack_path(component)
            for component in graph.components()
        )

        return tuple(
            sorted(
                attack_paths,
                key=lambda path: (
                    -path.severity_rank,
                    -path.score,
                    -path.confidence,
                    path.identifier,
                ),
            )
        )

    # ==========================================================
    # Correlation
    # ==========================================================

    @classmethod
    def _build_edges(
        cls,
        findings: tuple[Finding, ...],
    ) -> tuple[CorrelationEdge, ...]:
        """
        Correlate every pair of findings.
        """
        edges: list[CorrelationEdge] = []

        for index, left in enumerate(findings):
            for right in findings[index + 1 :]:

                result = FindingCorrelationService.correlate_pair(
                    left,
                    right,
                )

                if result.score <= 0:
                    continue

                edges.append(
                    CorrelationEdge(
                        source_finding_id=left.id,
                        target_finding_id=right.id,
                        score=result.score,
                        reasons=result.reasons,
                        is_directed=False,
                    )
                )

        return tuple(edges)

    # ==========================================================
    # Attack Path Mapping
    # ==========================================================

    @classmethod
    def _map_component_to_attack_path(
        cls,
        component: CorrelationComponent,
    ) -> AttackPath:
        """
        Convert a CorrelationComponent into an AttackPath.
        """
        entry_finding = cls._determine_entry_finding(component)
        impact_finding = cls._determine_impact_finding(component)

        return AttackPath(
            identifier=FingerprintService.attack_path(component),
            title=cls._generate_title(
                component,
                entry_finding,
                impact_finding,
            ),
            description=cls._generate_description(
                component,
                entry_finding,
                impact_finding,
            ),
            risk_level=cls._determine_risk_level(component),
            finding_ids=tuple(
                finding.id
                for finding in component.findings
            ),
            entry_finding_id=entry_finding.id,
            impact_finding_id=impact_finding.id,
            confidence=cls._calculate_confidence(component),
            score=cls._calculate_score(component),
            reasoning=cls._extract_reasoning(component),
        )

    # ==========================================================
    # V2 Heuristics
    # ==========================================================

    @classmethod
    def _calculate_score(
        cls,
        component: CorrelationComponent,
    ) -> float:
        """
        Temporary scoring heuristic.

        Version 3:
            AttackPathScoringService.score(...)
        """
        return round(
            component.average_correlation_score * component.node_count,
            2,
        )

    @classmethod
    def _calculate_confidence(
        cls,
        component: CorrelationComponent,
    ) -> float:
        """
        Temporary confidence heuristic.

        Version 3:
            AttackPathConfidenceService.confidence(...)
        """
        total = sum(
            finding.confidence.weight
            for finding in component.findings
        )

        return round(
            total / component.node_count,
            2,
        )

    @classmethod
    def _determine_risk_level(
        cls,
        component: CorrelationComponent,
    ) -> RiskLevel:
        """
        Temporary risk mapping.

        Version 3:
            AttackPathRiskService.risk(...)
        """
        return RiskLevel.from_severity(
            component.highest_severity
        )

    @classmethod
    def _determine_entry_finding(
        cls,
        component: CorrelationComponent,
    ) -> Finding:
        """
        Temporary entry-point heuristic.

        Version 3:
            AttackPathTraversalService.entry(...)
        """
        return component.entry_finding

    @classmethod
    def _determine_impact_finding(
        cls,
        component: CorrelationComponent,
    ) -> Finding:
        """
        Temporary impact heuristic.

        Version 3:
            AttackPathTraversalService.impact(...)
        """
        return max(
            component.findings,
            key=lambda finding: (
                finding.severity.weight,
                finding.confidence.weight,
            ),
        )

    @classmethod
    def _extract_reasoning(
        cls,
        component: CorrelationComponent,
    ) -> tuple[str, ...]:
        """
        Aggregate reasoning from all correlation edges.
        """
        return tuple(
            sorted(
                {
                    reason
                    for edge in component.edges
                    for reason in edge.reasons
                }
            )
        )

    # ==========================================================
    # Presentation Metadata
    # ==========================================================

    @classmethod
    def _generate_title(
        cls,
        component: CorrelationComponent,
        entry: Finding,
        impact: Finding,
    ) -> str:
        """
        Generate a concise title for the attack path.
        """
        analyzer = getattr(
            entry.analyzer,
            "display_name",
            str(entry.analyzer),
        )

        return (
            f"{analyzer} Attack Path "
            f"({component.node_count} finding(s))"
        )

    @classmethod
    def _generate_description(
        cls,
        component: CorrelationComponent,
        entry: Finding,
        impact: Finding,
    ) -> str:
        """
        Generate a human-readable summary.
        """
        return (
            f"Attack path containing "
            f"{component.node_count} correlated finding(s) "
            f"beginning at finding {entry.id} "
            f"and terminating at finding {impact.id}."
        )