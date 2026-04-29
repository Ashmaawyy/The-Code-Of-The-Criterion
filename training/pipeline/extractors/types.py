"""Domain types shared by all edge extractors.

Zero-dependency module — contains only the ``Edge`` TypedDict, the
``ExtractorResult`` alias, and the ``add_edge`` helper. I/O and paths
live in sibling modules (``loaders.py`` and ``al_furqan.paths``).
"""

from __future__ import annotations

from typing import TypedDict

# Type returned by every extractor: {verse_key: [Edge, ...]}
ExtractorResult = dict[str, list["Edge"]]


class Edge(TypedDict, total=False):
    edge_type: str       # tafsir | next_ayah | prev_ayah | sira_event | lesson | cross_ref | hadith
    target_id: str       # unique ID of the target node
    weight: float        # 0.0–1.0
    confidence: float    # 0.0–1.0
    provenance: str      # data source
    data: dict           # edge-type-specific payload


def add_edge(result: ExtractorResult, verse_key: str, edge: Edge) -> None:
    """Append an edge to a verse's edge list."""
    result.setdefault(verse_key, []).append(edge)
