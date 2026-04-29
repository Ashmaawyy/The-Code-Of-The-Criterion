"""Extract ayah→tafsir edges directly from ES tafsir indices."""

from __future__ import annotations

import logging

from training.pipeline.extractors.loaders import load_quran_map
from training.pipeline.extractors.types import ExtractorResult, add_edge

logger = logging.getLogger(__name__)

MIN_CONTENT_CHARS = 30


def _scroll_index(es, index: str, quran: dict, result: ExtractorResult, source_tag: str) -> int:
    """Scroll an ES tafsir index and yield edges."""
    if not es.indices.exists(index=index):
        logger.warning("Index %s does not exist, skipping", index)
        return 0

    total = es.count(index=index)["count"]
    logger.info("Reading %d docs from %s...", total, index)

    resp = es.search(
        index=index,
        body={"query": {"match_all": {}}, "size": 500},
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
            content = src.get("content") or src.get("tafsir_content") or ""
            if len(content.strip()) < MIN_CONTENT_CHARS:
                continue

            vk = src.get("verse_key", "")
            if not vk or vk not in quran:
                continue

            book = src.get("tafsir_book", "")
            add_edge(result, vk, {
                "edge_type": "tafsir",
                "target_id": f"tafsir:{vk}:{hash(book) % 100000:05d}",
                "weight": 1.0,
                "confidence": 1.0,
                "provenance": source_tag,
                "data": {
                    "tafsir_book": book,
                    "tafsir_scholar": src.get("tafsir_scholar", ""),
                    "tafsir_era": src.get("tafsir_era", ""),
                    "tafsir_text": content,
                },
            })
            count += 1

        resp = es.scroll(scroll_id=scroll_id, scroll="5m")

    try:
        es.clear_scroll(scroll_id=scroll_id)
    except Exception:
        pass
    return count


def extract(es=None, **kwargs) -> ExtractorResult:
    result: ExtractorResult = {}

    if es is None:
        try:
            from al_furqan.kb.es.client import create_es_client
            es = create_es_client()
            if not es.ping():
                logger.warning("ES not reachable, skipping tafsir edges")
                return result
        except Exception:
            logger.warning("Cannot connect to ES, skipping tafsir edges")
            return result

    quran = load_quran_map()

    structural = _scroll_index(es, "furqan_tafsir_structural", quran, result, "es_structural")
    logger.info("  structural: %d edges", structural)

    hf = _scroll_index(es, "furqan_tafsir", quran, result, "es_hf")
    logger.info("  hf: %d edges", hf)

    total = structural + hf
    logger.info("tafsir: %d edges across %d verses", total, len(result))
    return result
