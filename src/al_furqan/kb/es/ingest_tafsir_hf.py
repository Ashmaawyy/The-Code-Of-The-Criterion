"""Ingest the MohamedRashad/Quran-Tafseer HuggingFace dataset into Elasticsearch.

Downloads 218,530 tafsir entries (84 books x ~6,236 verses) and indexes them
into ``furqan_tafsir`` for use as training data.

This data is NOT part of the Quran tokenization (certainty=1.0 anchor).
It is scholarly interpretation — valuable for training but not ground truth.

Usage:
    python -m al_furqan.kb.es.ingest_tafsir_hf                # download + index
    python -m al_furqan.kb.es.ingest_tafsir_hf --dry-run       # preview
    python -m al_furqan.kb.es.ingest_tafsir_hf --drop           # recreate index
"""

import argparse
import json
import logging
import re
from pathlib import Path

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from al_furqan import setup_logging
from al_furqan.kb.es.analyzers import ANALYSIS_SETTINGS
from al_furqan.kb.es.client import create_es_client

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ES index definition
# ---------------------------------------------------------------------------

TAFSIR_INDEX = "furqan_tafsir"

TAFSIR_INDEX_DEFINITION = {
    "settings": {
        **ANALYSIS_SETTINGS,
        "number_of_shards": 2,
        "number_of_replicas": 0,
    },
    "mappings": {
        "properties": {
            "verse_key": {"type": "keyword"},
            "surah": {"type": "integer"},
            "ayah": {"type": "integer"},
            "surah_name": {"type": "keyword"},
            "revelation_type": {"type": "keyword"},
            "ayah_text": {
                "type": "text",
                "analyzer": "arabic_furqan",
            },
            "tafsir_book": {"type": "keyword"},
            "tafsir_scholar": {"type": "keyword"},
            "tafsir_era": {"type": "keyword"},
            "tafsir_content": {
                "type": "text",
                "analyzer": "arabic_furqan",
            },
            "content_length": {"type": "integer"},
        },
    },
}


# ---------------------------------------------------------------------------
# Surah name → number mapping
# ---------------------------------------------------------------------------


def _build_surah_map(quran_path: Path | None = None) -> dict[str, int]:
    """Build surah_name_ar → surah_number mapping from quran_complete.json."""
    if quran_path is None:
        quran_path = (
            Path(__file__).resolve().parent.parent.parent.parent.parent
            / "data"
            / "quran"
            / "quran_complete.json"
        )

    if quran_path.exists():
        with open(quran_path, encoding="utf-8") as f:
            data = json.load(f)
        mapping = {}
        for v in data["verses"]:
            mapping[v["surah_name_ar"]] = v["surah"]
        return mapping

    # Fallback: try ES
    logger.info("quran_complete.json not found, building map from ES")
    return {}


def _build_surah_map_from_es(es: Elasticsearch) -> dict[str, int]:
    """Build surah name → number mapping from the furqan_quran ES index."""
    mapping = {}
    body = {
        "size": 0,
        "aggs": {
            "surahs": {
                "terms": {"field": "surah_name_ar", "size": 200},
                "aggs": {"surah_num": {"min": {"field": "surah"}}},
            }
        },
    }
    resp = es.search(index="furqan_quran", body=body)
    for bucket in resp["aggregations"]["surahs"]["buckets"]:
        mapping[bucket["key"]] = int(bucket["surah_num"]["value"])
    return mapping


# ---------------------------------------------------------------------------
# Ayah text → ayah number matching
# ---------------------------------------------------------------------------

_AYAH_NUMBER_CACHE: dict[tuple[int, str], int] = {}


def _match_ayah_number(es: Elasticsearch, surah: int, ayah_text: str) -> int:
    """Match ayah text to ayah number using ES phrase search.

    The dataset doesn't have ayah numbers — only the verse text.
    We match against our indexed Quran to resolve the number.
    """
    cache_key = (surah, ayah_text[:100])
    if cache_key in _AYAH_NUMBER_CACHE:
        return _AYAH_NUMBER_CACHE[cache_key]

    resp = es.search(
        index="furqan_quran",
        body={
            "query": {
                "bool": {
                    "must": [
                        {"match_phrase": {"text_ar": {"query": ayah_text, "slop": 0}}},
                    ],
                    "filter": [{"term": {"surah": surah}}],
                }
            },
            "size": 1,
        },
    )

    hits = resp["hits"]["hits"]
    if hits:
        ayah_num = hits[0]["_source"]["ayah"]
        _AYAH_NUMBER_CACHE[cache_key] = ayah_num
        return ayah_num

    # Fallback: try relaxed match
    resp = es.search(
        index="furqan_quran",
        body={
            "query": {
                "bool": {
                    "must": [{"match": {"text_ar": ayah_text}}],
                    "filter": [{"term": {"surah": surah}}],
                }
            },
            "size": 1,
        },
    )
    hits = resp["hits"]["hits"]
    if hits:
        ayah_num = hits[0]["_source"]["ayah"]
        _AYAH_NUMBER_CACHE[cache_key] = ayah_num
        return ayah_num

    _AYAH_NUMBER_CACHE[cache_key] = 0
    return 0


# ---------------------------------------------------------------------------
# Parse tafsir book metadata
# ---------------------------------------------------------------------------

_ERA_PATTERN = re.compile(r"\(ت\s*(\d+)\s*هـ\)")
_MODERN_PATTERN = re.compile(r"\(مـ\s*(\d+)\s*م")


def _parse_book_meta(book_name: str) -> tuple[str, str]:
    """Extract scholar name and era from tafsir_book string.

    Examples:
        "تفسير تفسير القرآن العظيم/ ابن كثير (ت 774 هـ)" → ("ابن كثير", "774 هـ")
        "تفسير صفوة التفاسير/ الصابوني (مـ 1930م -)" → ("الصابوني", "1930 م")
    """
    # Extract era
    era_match = _ERA_PATTERN.search(book_name)
    if era_match:
        era = f"{era_match.group(1)} هـ"
    else:
        modern_match = _MODERN_PATTERN.search(book_name)
        era = f"{modern_match.group(1)} م" if modern_match else ""

    # Extract scholar name (after / and before ()
    scholar = ""
    if "/" in book_name:
        after_slash = book_name.split("/")[-1].strip()
        # Remove era part
        scholar = re.sub(r"\(.*\)", "", after_slash).strip()
        # Remove leading *
        scholar = scholar.lstrip("* ").strip()

    return scholar, era


# ---------------------------------------------------------------------------
# Main ingestion
# ---------------------------------------------------------------------------


def ingest_tafsir(
    es: Elasticsearch,
    index: str = TAFSIR_INDEX,
    drop_existing: bool = False,
    dry_run: bool = False,
    batch_size: int = 2000,
) -> int:
    """Download and index the HuggingFace Quran-Tafseer dataset.

    Returns the number of documents indexed.
    """
    # Create/recreate index
    if not dry_run:
        if es.indices.exists(index=index):
            if drop_existing:
                logger.warning("Dropping existing index: %s", index)
                es.indices.delete(index=index)
            else:
                count = es.count(index=index)["count"]
                if count > 0:
                    logger.info(
                        "Index %s already has %d docs. Use --drop to recreate.",
                        index,
                        count,
                    )
                    return count

        if not es.indices.exists(index=index):
            logger.info("Creating index: %s", index)
            es.indices.create(index=index, body=TAFSIR_INDEX_DEFINITION)

    # Build surah name → number mapping
    surah_map = _build_surah_map()
    if not surah_map:
        surah_map = _build_surah_map_from_es(es)
    if not surah_map:
        logger.error("Cannot build surah mapping. Ensure quran data is available.")
        return 0
    logger.info("Surah mapping: %d surahs", len(surah_map))

    # Load HuggingFace dataset
    logger.info("Downloading MohamedRashad/Quran-Tafseer from HuggingFace...")
    from datasets import load_dataset  # pylint: disable=import-outside-toplevel

    ds = load_dataset("MohamedRashad/Quran-Tafseer", split="train")
    logger.info("Downloaded %d rows", len(ds))

    if dry_run:
        books = set(ds["tafsir_book"])
        logger.info(
            "[DRY RUN] Would index %d entries from %d tafsir books", len(ds), len(books)
        )
        return len(ds)

    # Process and index in batches
    actions = []
    indexed = 0
    skipped = 0
    unmatched_ayahs = 0

    for i, row in enumerate(ds):
        surah_name = row["surah_name"]
        surah_num = surah_map.get(surah_name, 0)
        if surah_num == 0:
            skipped += 1
            continue

        ayah_text = row["ayah"]
        tafsir_content = row["tafsir_content"]

        # Skip empty tafsir
        if not tafsir_content or len(tafsir_content.strip()) < 10:
            skipped += 1
            continue

        # Match ayah number via ES
        ayah_num = _match_ayah_number(es, surah_num, ayah_text)
        if ayah_num == 0:
            unmatched_ayahs += 1
            # Still index with ayah=0, we can fix later
            verse_key = f"{surah_num}:?"
        else:
            verse_key = f"{surah_num}:{ayah_num}"

        scholar, era = _parse_book_meta(row["tafsir_book"])

        doc_id = f"{verse_key}_{hash(row['tafsir_book']) % 100000:05d}"

        actions.append(
            {
                "_index": index,
                "_id": doc_id,
                "_source": {
                    "verse_key": verse_key,
                    "surah": surah_num,
                    "ayah": ayah_num,
                    "surah_name": surah_name,
                    "revelation_type": row.get("revelation_type", ""),
                    "ayah_text": ayah_text,
                    "tafsir_book": row["tafsir_book"],
                    "tafsir_scholar": scholar,
                    "tafsir_era": era,
                    "tafsir_content": tafsir_content,
                    "content_length": len(tafsir_content),
                },
            }
        )

        # Flush batch
        if len(actions) >= batch_size:
            success, errors = bulk(es, actions, raise_on_error=False)
            if errors:
                logger.warning("%d errors in batch at row %d", len(errors), i)
            indexed += success
            actions = []

            if (i + 1) % 20000 == 0:
                logger.info(
                    "Progress: %d/%d indexed (%d skipped, %d unmatched ayahs)",
                    indexed,
                    i + 1,
                    skipped,
                    unmatched_ayahs,
                )

    # Final batch
    if actions:
        success, errors = bulk(es, actions, raise_on_error=False)
        if errors:
            logger.warning("%d errors in final batch", len(errors))
        indexed += success

    es.indices.refresh(index=index)

    logger.info("Ingestion complete:")
    logger.info("  Indexed:  %d", indexed)
    logger.info("  Skipped:  %d (empty or no surah match)", skipped)
    logger.info("  Unmatched ayahs: %d (indexed with ayah=0)", unmatched_ayahs)

    # Show stats
    stats = es.indices.stats(index=index)
    size_mb = (
        stats["indices"][index]["primaries"]["store"]["size_in_bytes"] / 1024 / 1024
    )
    logger.info("  Index size: %.1f MB", size_mb)

    return indexed


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Ingest MohamedRashad/Quran-Tafseer dataset into Elasticsearch"
    )
    parser.add_argument("--es-url", default=None, help="Elasticsearch URL")
    parser.add_argument(
        "--index", default=TAFSIR_INDEX, help=f"Index name (default: {TAFSIR_INDEX})"
    )
    parser.add_argument("--drop", action="store_true", help="Drop and recreate index")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without indexing"
    )
    parser.add_argument("--batch-size", type=int, default=2000, help="Bulk batch size")
    args = parser.parse_args()

    hosts = [args.es_url] if args.es_url else None
    es = create_es_client(hosts=hosts)

    ingest_tafsir(
        es,
        index=args.index,
        drop_existing=args.drop,
        dry_run=args.dry_run,
        batch_size=args.batch_size,
    )


if __name__ == "__main__":
    main()
