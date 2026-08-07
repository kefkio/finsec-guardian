from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping
from uuid import UUID

from scanner.domain.entities import Finding
from scanner.domain.value_objects.correlation_component import CorrelationComponent
from scanner.domain.value_objects.correlation_edge import CorrelationEdge


@dataclass(frozen=True, slots=True)
class CorrelationGraph:
    """
    Immutable Value Object representing an undirected graph of correlated findings.
    Uses read-only mapping proxies to guarantee structural immutability.
    """

    nodes: Mapping[UUID, Finding]
    edges: tuple[CorrelationEdge, ...]
    adjacency_list: Mapping[UUID, tuple[UUID, ...]]

    @classmethod
    def from_findings_and_edges(
        cls,
        findings: tuple[Finding, ...],
        edges: tuple[CorrelationEdge, ...],
    ) -> CorrelationGraph:
        """
        Factory method building an immutable CorrelationGraph using read-only proxies.
        """
        mutable_nodes = {f.id: f for f in findings}
        mutable_adj: dict[UUID, list[UUID]] = {f.id: [] for f in findings}

        for edge in edges:
            u, v = edge.source_finding_id, edge.target_finding_id
            if u in mutable_adj and v in mutable_adj:
                mutable_adj[u].append(v)
                mutable_adj[v].append(u)

        # Freeze dictionaries into MappingProxyType and inner tuples
        frozen_nodes = MappingProxyType(mutable_nodes)
        frozen_adj = MappingProxyType(
            {node: tuple(neighbors) for node, neighbors in mutable_adj.items()}
        )

        return cls(
            nodes=frozen_nodes,
            edges=tuple(edges),
            adjacency_list=frozen_adj,
        )

    # ==========================================================
    # Graph Metrics & Properties
    # ==========================================================

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    @property
    def is_empty(self) -> bool:
        return len(self.nodes) == 0

    @property
    def density(self) -> float:
        """Calculates global density for undirected graph: 2E / (V * (V - 1))."""
        v = self.node_count
        if v <= 1:
            return 0.0
        max_possible_edges = (v * (v - 1)) / 2.0
        return round(self.edge_count / max_possible_edges, 4)

    # ==========================================================
    # Traversal & Query Helpers
    # ==========================================================

    def degree(self, finding_id: UUID) -> int:
        """Returns the degree (number of connected edges) for a given finding node."""
        return len(self.adjacency_list.get(finding_id, ()))

    def neighbors(self, finding_id: UUID) -> tuple[Finding, ...]:
        """Returns the neighboring Finding entities connected to the specified node."""
        neighbor_ids = self.adjacency_list.get(finding_id, ())
        return tuple(self.nodes[nid] for nid in neighbor_ids if nid in self.nodes)

    def isolated_nodes(self) -> tuple[Finding, ...]:
        """Returns findings that have no correlation edges connected to them."""
        return tuple(
            finding
            for fid, finding in self.nodes.items()
            if self.degree(fid) == 0
        )

    # ==========================================================
    # Component Decomposition
    # ==========================================================

    def components(self) -> tuple[CorrelationComponent, ...]:
        """
        Decomposes graph into connected sub-components via BFS traversal,
        returning a tuple of CorrelationComponent Value Objects deterministically
        ordered by component sort_key.
        """
        visited: set[UUID] = set()
        components: list[CorrelationComponent] = []

        for start_id in self.nodes:
            if start_id in visited:
                continue

            component_node_ids: set[UUID] = set()
            queue: deque[UUID] = deque([start_id])
            visited.add(start_id)

            while queue:
                current = queue.popleft()
                component_node_ids.add(current)

                for neighbor_id in self.adjacency_list.get(current, ()):
                    if neighbor_id not in visited:
                        visited.add(neighbor_id)
                        queue.append(neighbor_id)

            # Extract findings for this component
            component_findings = tuple(
                self.nodes[node_id]
                for node_id in sorted(component_node_ids, key=lambda u: str(u))
            )

            # Filter edges belonging strictly to this component
            component_edges = tuple(
                edge
                for edge in self.edges
                if edge.source_finding_id in component_node_ids
                and edge.target_finding_id in component_node_ids
            )

            # Determine entry finding (highest degree, then highest severity)
            entry_finding = max(
                component_findings,
                key=lambda f: (self.degree(f.id), f.severity.weight),
            )

            component = CorrelationComponent.create(
                findings=component_findings,
                edges=component_edges,
                entry_finding_id=entry_finding.id,
            )
            components.append(component)

        # Deterministic component ordering
        components.sort(key=lambda c: c.sort_key)

        return tuple(components)