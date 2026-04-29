"""Elasticsearch-backed Graph Store.

Drop-in replacement for ``kb/graph/store.py``.  Stores edges in the
``furqan_graph`` index and delegates node lookups to the appropriate
collection index (quran, hadith, etc.).
"""

from __future__ import annotations

import logging
from typing import Any

from elasticsearch import Elasticsearch

logger = logging.getLogger(__name__)


class ESGraphStore:
    """Graph store backed by Elasticsearch.

    Edges are stored in the graph index. Nodes live in their own indices
    (quran, hadith) and are resolved on demand.
    """

    def __init__(
        self,
        es: Elasticsearch,
        graph_index: str = "furqan_graph",
        enforce_provenance: bool = False,
    ) -> None:
        self._es = es
        self._index = graph_index
        self._enforce_provenance = enforce_provenance

    # ------------------------------------------------------------------
    # Edge operations
    # ------------------------------------------------------------------

    def add_edge(
        self,
        source: str,
        target: str,
        edge_type: str,
        weight: float = 1.0,
        metadata: dict[str, Any] | None = None,
        *,
        provenance: str = "",
        provenance_type: str = "",
        reference: str = "",
        verified_by: str = "",
        confidence: float = 1.0,
    ) -> str:
        """Add a directed edge. Returns the edge document ID."""
        if self._enforce_provenance and not provenance:
            raise ValueError(
                f"Edge {source} → {target} ({edge_type}) rejected: "
                f"provenance is REQUIRED."
            )

        edge_id = f"{source}--{edge_type}--{target}"
        doc = {
            "source": source,
            "target": target,
            "edge_type": edge_type,
            "weight": weight,
            "metadata": metadata or {},
            "provenance": provenance,
            "provenance_type": provenance_type,
            "reference": reference,
            "verified_by": verified_by,
            "confidence": confidence,
        }
        self._es.index(index=self._index, id=edge_id, body=doc, refresh="wait_for")
        return edge_id

    def get_edges_by_type(self, edge_type: str, limit: int = 200) -> list[dict[str, Any]]:
        """Return all edges of a given type."""
        body = {"query": {"term": {"edge_type": edge_type}}, "size": limit}
        resp = self._es.search(index=self._index, body=body)
        return [h["_source"] for h in resp["hits"]["hits"]]

    # ------------------------------------------------------------------
    # Neighbor queries
    # ------------------------------------------------------------------

    def get_neighbors(
        self,
        node_id: str,
        edge_types: list[str] | None = None,
        direction: str = "out",
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return edges connected to a node.

        Args:
            node_id: The node to query from.
            edge_types: Filter by edge types (None = all).
            direction: "out", "in", or "both".
            limit: Max edges to return.

        Returns:
            List of edge dicts with source, target, edge_type, etc.
        """
        clauses = []

        if direction in ("out", "both"):
            clauses.append({"term": {"source": node_id}})
        if direction in ("in", "both"):
            clauses.append({"term": {"target": node_id}})

        query: dict[str, Any]
        if len(clauses) == 1:
            query = clauses[0]
        else:
            query = {"bool": {"should": clauses, "minimum_should_match": 1}}

        # Add edge_type filter if specified
        if edge_types:
            query = {
                "bool": {
                    "must": [query],
                    "filter": [{"terms": {"edge_type": edge_types}}],
                },
            }

        body = {"query": query, "size": limit}
        resp = self._es.search(index=self._index, body=body)
        return [h["_source"] for h in resp["hits"]["hits"]]

    def get_outgoing(self, node_id: str, edge_types: list[str] | None = None,
                     limit: int = 100) -> list[dict]:
        """Shortcut for outgoing edges."""
        return self.get_neighbors(node_id, edge_types=edge_types, direction="out", limit=limit)

    def get_incoming(self, node_id: str, edge_types: list[str] | None = None,
                     limit: int = 100) -> list[dict]:
        """Shortcut for incoming edges."""
        return self.get_neighbors(node_id, edge_types=edge_types, direction="in", limit=limit)

    # ------------------------------------------------------------------
    # Traversal (BFS, 1-2 hops)
    # ------------------------------------------------------------------

    def bfs(
        self,
        start: str,
        max_depth: int = 2,
        edge_types: list[str] | None = None,
        limit_per_hop: int = 50,
    ) -> list[dict[str, Any]]:
        """Breadth-first traversal from a starting node.

        Returns all edges discovered up to max_depth hops.
        """
        visited: set[str] = {start}
        all_edges: list[dict] = []
        frontier = [start]

        for _depth in range(max_depth):
            next_frontier = []
            for node_id in frontier:
                edges = self.get_outgoing(node_id, edge_types=edge_types,
                                          limit=limit_per_hop)
                for edge in edges:
                    all_edges.append(edge)
                    target = edge["target"]
                    if target not in visited:
                        visited.add(target)
                        next_frontier.append(target)
            frontier = next_frontier
            if not frontier:
                break

        return all_edges

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        """Return graph statistics."""
        total = self._es.count(index=self._index)["count"]

        # Count by edge type
        body = {
            "size": 0,
            "aggs": {"by_type": {"terms": {"field": "edge_type", "size": 50}}},
        }
        resp = self._es.search(index=self._index, body=body)
        by_type = {
            b["key"]: b["doc_count"]
            for b in resp["aggregations"]["by_type"]["buckets"]
        }
        return {"total_edges": total, "by_type": by_type}
