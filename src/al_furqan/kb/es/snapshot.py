"""Export ES indices to local JSONL cache files for offline fallback.

Creates data_archive/.es_cache/<index_name>.jsonl for each index that
generators read from. Each line is a JSON doc with _source fields + _id preserved.

Run this:
  - After every data update to ES
  - Before planned ES maintenance
  - Periodically as a safety net

Usage:
    python -m training.pipeline.es_snapshot                    # all indices
    python -m training.pipeline.es_snapshot --only furqan_quran
    python -m training.pipeline.es_snapshot --list             # show what would be exported
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from al_furqan.paths import ES_CACHE_DIR as CACHE_DIR

logger = logging.getLogger(__name__)

# Indices that generators read from — only these are snapshotted.
# Write-only indices (furqan_training_examples etc.) are NOT included.
SNAPSHOT_INDICES: dict[str, dict] = {
    "furqan_tafsir_structural": {
        "description": "Structural tafsir entries (39K docs, ~218 MB)",
        "sort": [{"surah": "asc"}, {"ayah": "asc"}],
        "id_field": None,  # use ES _id
    },
    "furqan_quran": {
        "description": "Quran verses with Arabic/English text (6,236 docs)",
        "sort": [{"surah": "asc"}, {"ayah": "asc"}],
        "id_field": "verse_key",  # compose _id from this field
    },
    "furqan_quran_tokens": {
        "description": "5-level tokenized Quran (418K docs)",
        "sort": [{"surah": "asc"}, {"ayah": "asc"}],
        "id_field": "verse_key",
    },
    "furqan_tafsir": {
        "description": "Classical tafsir chunks (165K docs)",
        "sort": None,
        "id_field": None,
    },
    "furqan_hadith": {
        "description": "Hadith collection (55 docs)",
        "sort": None,
        "id_field": None,
    },
    "furqan_lessons": {
        "description": "Teacher lesson transcripts (2,434 docs)",
        "sort": None,
        "id_field": None,
    },
}


def snapshot_index(
    es,
    index: str,
    config: dict,
    cache_dir: Path,
) -> int:
    """Export one ES index to a JSONL cache file. Returns doc count."""
    out_path = cache_dir / f"{index}.jsonl"

    body: dict = {"query": {"match_all": {}}}
    sort = config.get("sort")
    if sort:
        body["sort"] = sort
    id_field = config.get("id_field")

    resp = es.search(index=index, body=body, scroll="5m", size=500)
    scroll_id = resp["_scroll_id"]
    total = resp["hits"]["total"]
    total_count = total["value"] if isinstance(total, dict) else total
    logger.info("  Snapshotting %s (%s docs)...", index, total_count)

    count = 0
    with out_path.open("w", encoding="utf-8") as f:
        while True:
            hits = resp["hits"]["hits"]
            if not hits:
                break
            for hit in hits:
                doc = hit["_source"]
                # Preserve the ES _id so point lookups work from cache
                if id_field and id_field in doc:
                    doc["_id"] = doc[id_field]
                else:
                    doc["_id"] = hit["_id"]
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
                count += 1
            resp = es.scroll(scroll_id=scroll_id, scroll="5m")

    try:
        es.clear_scroll(scroll_id=scroll_id)
    except Exception:
        pass

    size_mb = out_path.stat().st_size / (1024 * 1024)
    logger.info("  %s -> %d docs (%.1f MB)", out_path.name, count, size_mb)
    return count


def run(es, indices: list[str] | None, cache_dir: Path) -> dict[str, int]:
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Write a .gitignore in the cache dir
    gitignore = cache_dir / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("*\n!.gitignore\n")

    targets = indices if indices else list(SNAPSHOT_INDICES.keys())
    results: dict[str, int] = {}

    for idx_name in targets:
        if idx_name not in SNAPSHOT_INDICES:
            logger.warning("Unknown index: %s — skipping", idx_name)
            continue
        config = SNAPSHOT_INDICES[idx_name]
        if not es.indices.exists(index=idx_name):
            logger.warning("Index %s does not exist in ES — skipping", idx_name)
            continue
        results[idx_name] = snapshot_index(es, idx_name, config, cache_dir)

    return results


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    parser = argparse.ArgumentParser(description="Snapshot ES indices to local cache")
    parser.add_argument("--es-url", default=None)
    parser.add_argument("--cache-dir", type=Path, default=CACHE_DIR)
    parser.add_argument(
        "--only", nargs="*", default=None, help="Limit to specific indices"
    )
    parser.add_argument(
        "--list", action="store_true", help="List indices that would be snapshotted"
    )
    args = parser.parse_args()

    if args.list:
        for name, cfg in SNAPSHOT_INDICES.items():
            print(f"  {name:35s} — {cfg['description']}")
        return

    from al_furqan.kb.es.client import create_es_client

    hosts = [args.es_url] if args.es_url else None
    es = create_es_client(hosts=hosts)

    results = run(es, args.only, args.cache_dir)

    logger.info("=" * 60)
    logger.info("ES snapshot complete")
    logger.info("=" * 60)
    total = 0
    for idx, count in results.items():
        logger.info("  %s: %d docs", idx, count)
        total += count
    logger.info("  Total: %d docs in %s", total, args.cache_dir)


if __name__ == "__main__":
    main()
