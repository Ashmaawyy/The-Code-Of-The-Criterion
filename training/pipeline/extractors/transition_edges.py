"""Extract ayah→next_ayah / ayah→prev_ayah edges from furqan_quran_tokens."""

from __future__ import annotations

import logging

from training.pipeline.extractors.loaders import load_quran_map
from training.pipeline.extractors.types import ExtractorResult, add_edge

logger = logging.getLogger(__name__)


def extract(es=None, **kwargs) -> ExtractorResult:
    result: ExtractorResult = {}

    if es is None:
        try:
            from al_furqan.kb.es.client import create_es_client
            es = create_es_client()
            if not es.ping():
                logger.warning("ES not reachable, skipping transition edges")
                return result
        except Exception:
            logger.warning("Cannot connect to ES, skipping transition edges")
            return result

    index = "furqan_quran_tokens"
    if not es.indices.exists(index=index):
        logger.warning("Index %s does not exist", index)
        return result

    # Build ordered verse list per surah for next/prev linking
    quran = load_quran_map()
    surah_verses: dict[int, list[str]] = {}
    for vk, v in quran.items():
        surah_verses.setdefault(v["surah"], []).append(vk)
    for s in surah_verses:
        surah_verses[s].sort(key=lambda k: int(k.split(":")[1]))

    # Build next/prev maps
    next_map: dict[str, str] = {}
    prev_map: dict[str, str] = {}
    for verses in surah_verses.values():
        for i in range(len(verses) - 1):
            next_map[verses[i]] = verses[i + 1]
            prev_map[verses[i + 1]] = verses[i]

    # Scroll through tokens index for transition metadata
    total = es.count(index=index)["count"]
    logger.info("Reading %d docs from %s...", total, index)

    resp = es.search(
        index=index,
        body={
            "query": {"match_all": {}},
            "sort": [{"surah": "asc"}, {"ayah": "asc"}],
            "size": 500,
            "_source": ["verse_key", "surah", "ayah", "transition_tokens",
                        "reasoning_pattern", "word_count", "unique_roots"],
        },
        scroll="5m",
    )
    scroll_id = resp["_scroll_id"]
    count = 0

    while True:
        hits = resp["hits"]["hits"]
        if not hits:
            break
        for hit in hits:
            src = hit["_source"]
            vk = src.get("verse_key", "")
            if not vk:
                continue

            transitions = src.get("transition_tokens") or []
            # Summarise the dominant transition type
            type_counts: dict[str, int] = {}
            total_smoothness = 0.0
            for t in transitions:
                tt = t.get("transition_type", "none")
                if tt != "none":
                    type_counts[tt] = type_counts.get(tt, 0) + 1
                total_smoothness += t.get("smoothness", 0.0)

            dominant = max(type_counts, key=type_counts.get) if type_counts else "continuation"
            avg_smooth = total_smoothness / len(transitions) if transitions else 1.0

            next_vk = next_map.get(vk)
            if next_vk:
                add_edge(result, vk, {
                    "edge_type": "next_ayah",
                    "target_id": next_vk,
                    "weight": avg_smooth,
                    "confidence": 1.0,
                    "provenance": "quran_tokens",
                    "data": {
                        "transition_type": dominant,
                        "smoothness": round(avg_smooth, 3),
                        "reasoning_pattern": src.get("reasoning_pattern", ""),
                        "word_count": src.get("word_count", 0),
                        "unique_roots": src.get("unique_roots", 0),
                    },
                })
                count += 1

            prev_vk = prev_map.get(vk)
            if prev_vk:
                add_edge(result, vk, {
                    "edge_type": "prev_ayah",
                    "target_id": prev_vk,
                    "weight": avg_smooth,
                    "confidence": 1.0,
                    "provenance": "quran_tokens",
                    "data": {"transition_type": dominant, "smoothness": round(avg_smooth, 3)},
                })
                count += 1

        resp = es.scroll(scroll_id=scroll_id, scroll="5m")

    try:
        es.clear_scroll(scroll_id=scroll_id)
    except Exception:
        pass

    logger.info("transition: %d edges (next+prev) across %d verses", count, len(result))
    return result
