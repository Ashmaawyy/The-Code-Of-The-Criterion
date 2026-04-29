"""Extract ayah→ayah cross-reference edges from the knowledge graph and lessons."""

from __future__ import annotations

import json
import logging

from al_furqan.paths import LESSONS_ENRICHED_DIR as LESSONS_DIR
from training.pipeline.extractors.loaders import load_graph_edges
from training.pipeline.extractors.types import ExtractorResult, add_edge

logger = logging.getLogger(__name__)


def _parse_ayah_node(node: str) -> str | None:
    """Convert 'ayah:2:275' → '2:275', or return None."""
    if node.startswith("ayah:"):
        parts = node.split(":", 2)
        if len(parts) == 3:
            return f"{parts[1]}:{parts[2]}"
    return None


def extract(**kwargs) -> ExtractorResult:
    result: ExtractorResult = {}
    count = 0

    # Source 1: sample_graph.json — ayah-to-ayah edges
    for edge in load_graph_edges():
        etype = edge.get("edge_type", "")
        src = _parse_ayah_node(edge.get("source", ""))
        tgt = _parse_ayah_node(edge.get("target", ""))

        if not src or not tgt:
            continue
        if etype not in ("REFERENCES", "REINFORCES", "QUALIFIES", "CONTRASTS"):
            continue

        edge_data = {
            "relation": etype.lower(),
            "provenance_detail": edge.get("provenance", ""),
            "reference": edge.get("reference", ""),
        }

        # Bidirectional
        add_edge(result, src, {
            "edge_type": "cross_ref",
            "target_id": tgt,
            "weight": edge.get("weight", 1.0),
            "confidence": edge.get("confidence", 1.0),
            "provenance": "knowledge_graph",
            "data": edge_data,
        })
        add_edge(result, tgt, {
            "edge_type": "cross_ref",
            "target_id": src,
            "weight": edge.get("weight", 1.0),
            "confidence": edge.get("confidence", 1.0),
            "provenance": "knowledge_graph",
            "data": {**edge_data, "relation": f"inverse_{etype.lower()}"},
        })
        count += 2

    # Source 2: lesson linked_verses
    if LESSONS_DIR.exists():
        for lesson_path in sorted(LESSONS_DIR.glob("lesson_*_Anaam.json")):
            try:
                with open(lesson_path, encoding="utf-8") as f:
                    lesson = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            for ch in lesson.get("chapters", []):
                taught = [tv.get("verse_key", "") for tv in ch.get("taught_verses", [])]
                linked = [lv.get("verse_key", "") for lv in ch.get("linked_verses", [])]

                for tvk in taught:
                    if not tvk:
                        continue
                    for lvk in linked:
                        if not lvk or lvk == tvk:
                            continue
                        add_edge(result, tvk, {
                            "edge_type": "cross_ref",
                            "target_id": lvk,
                            "weight": 0.8,
                            "confidence": 0.9,
                            "provenance": f"lesson:{lesson_path.stem}",
                            "data": {"relation": "lesson_linked"},
                        })
                        count += 1

    logger.info("crossref: %d edges across %d verses", count, len(result))
    return result
