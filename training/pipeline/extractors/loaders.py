"""Static-data loaders used by edge extractors.

These read the canonical Quran and graph JSON files from the archive and
return in-memory structures the extractors can iterate. Paths come from
:mod:`al_furqan.paths` so that a rename of the archive directory is a
one-file change.
"""

from __future__ import annotations

import json

from al_furqan.paths import QURAN_COMPLETE_JSON, SAMPLE_GRAPH_JSON


def load_quran_map() -> dict[str, dict]:
    """Load verse_key -> {surah, ayah, text_ar, text_en, ...}."""
    with open(QURAN_COMPLETE_JSON, encoding="utf-8") as f:
        raw = json.load(f)
    out = {}
    for v in raw["verses"]:
        key = f"{v['surah']}:{v['ayah']}"
        out[key] = v
    return out


def load_graph_edges() -> list[dict]:
    """Load edges from sample_graph.json."""
    with open(SAMPLE_GRAPH_JSON, encoding="utf-8") as f:
        return json.load(f).get("edges", [])
