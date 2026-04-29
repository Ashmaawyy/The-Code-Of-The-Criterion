"""Phase 2: Migrate static data from JSON files into Elasticsearch.

Loads Quran verses, Hadith, knowledge graph edges, and enriched lessons
from the project's data/ directory and bulk-indexes them into ES.

Usage:
    python -m al_furqan.kb.es.migrate_data                     # migrate all
    python -m al_furqan.kb.es.migrate_data --collection quran   # migrate one
    python -m al_furqan.kb.es.migrate_data --data-dir /path     # custom data dir
    python -m al_furqan.kb.es.migrate_data --dry-run             # preview without indexing
"""

import argparse
import json
import logging
import time
from pathlib import Path

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk, BulkIndexError

from al_furqan import setup_logging
from al_furqan.kb.es.client import create_es_client
from al_furqan.paths import DATA_ARCHIVE as _DEFAULT_DATA_DIR

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Loaders — read JSON files and yield ES bulk actions
# ---------------------------------------------------------------------------

def _load_quran(data_dir: Path, prefix: str):
    """Yield bulk actions for Quran verses."""
    path = data_dir / "quran" / "quran_complete.json"
    if not path.exists():
        logger.error("Quran data not found: %s", path)
        return

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    index = f"{prefix}_quran"
    for verse in data["verses"]:
        verse_key = f"{verse['surah']}:{verse['ayah']}"
        yield {
            "_index": index,
            "_id": verse_key,
            "_source": {
                "surah": verse["surah"],
                "ayah": verse["ayah"],
                "verse_key": verse_key,
                "surah_name_ar": verse["surah_name_ar"],
                "surah_name_en": verse["surah_name_en"],
                "text_ar": verse["text_ar"],
                "text_en": verse["text_en"],
                "juz": verse.get("juz"),
                "page": verse.get("page"),
                "revelation_type": verse.get("revelation_type", ""),
                "topics": verse.get("topics", []),
            },
        }


def _load_hadith(data_dir: Path, prefix: str):
    """Yield bulk actions for Hadith records."""
    path = data_dir / "hadith" / "hadith_sample.json"
    if not path.exists():
        logger.error("Hadith data not found: %s", path)
        return

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    index = f"{prefix}_hadith"
    for h in data["hadith"]:
        hadith_key = f"{h['collection_name']}:{h['number']}"
        yield {
            "_index": index,
            "_id": hadith_key,
            "_source": {
                "collection_name": h["collection_name"],
                "number": h["number"],
                "hadith_key": hadith_key,
                "text_ar": h["text_ar"],
                "text_en": h.get("text_en", ""),
                "narrator": h.get("narrator", ""),
                "grading": h.get("grading", ""),
                "topics": h.get("topics", []),
            },
        }


def _load_graph(data_dir: Path, prefix: str):
    """Yield bulk actions for knowledge graph edges."""
    path = data_dir / "graph" / "sample_graph.json"
    if not path.exists():
        logger.error("Graph data not found: %s", path)
        return

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    index = f"{prefix}_graph"
    for edge in data.get("edges", []):
        edge_id = f"{edge['source']}--{edge['edge_type']}--{edge['target']}"
        yield {
            "_index": index,
            "_id": edge_id,
            "_source": {
                "source": edge["source"],
                "target": edge["target"],
                "edge_type": edge["edge_type"],
                "weight": edge.get("weight", 1.0),
                "provenance": edge.get("provenance", ""),
                "provenance_type": edge.get("provenance_type", ""),
                "reference": edge.get("reference", ""),
                "verified_by": edge.get("verified_by", ""),
                "confidence": edge.get("confidence", 1.0),
                "metadata": edge.get("metadata", {}),
            },
        }


def _load_lessons(data_dir: Path, prefix: str):
    """Yield bulk actions for enriched lesson files."""
    lessons_dir = data_dir / "lessons" / "lessons_enriched_json"
    if not lessons_dir.exists():
        logger.error("Enriched lessons dir not found: %s", lessons_dir)
        return

    index = f"{prefix}_lessons"
    for lesson_file in sorted(lessons_dir.glob("lesson_*_Anaam.json")):
        try:
            with open(lesson_file, encoding="utf-8") as f:
                lesson = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Failed to read %s: %s", lesson_file.name, exc)
            continue

        lesson_num = lesson["lesson_number"]
        doc_id = f"lesson_{lesson_num:02d}"

        # Build clean chapter data for ES
        chapters = []
        for ch in lesson.get("chapters", []):
            chapter_doc = {
                "chapter_number": ch["chapter_number"],
                "title": ch.get("title", ""),
                "content": ch.get("content", ""),
                "taught_verses": ch.get("taught_verses", []),
                "linked_verses": ch.get("linked_verses", []),
                "mentioned_ahadeeth": ch.get("mentioned_ahadeeth", []),
            }
            chapters.append(chapter_doc)

        yield {
            "_index": index,
            "_id": doc_id,
            "_source": {
                "lesson_number": lesson_num,
                "surah": lesson.get("surah", ""),
                "title": lesson.get("title", ""),
                "total_chapters": lesson.get("total_chapters", len(chapters)),
                "chapters": chapters,
            },
        }


# ---------------------------------------------------------------------------
# Collection registry
# ---------------------------------------------------------------------------

COLLECTIONS = {
    "quran": _load_quran,
    "hadith": _load_hadith,
    "graph": _load_graph,
    "lessons": _load_lessons,
}


# ---------------------------------------------------------------------------
# Bulk indexing
# ---------------------------------------------------------------------------

def migrate_collection(
    es: Elasticsearch,
    name: str,
    data_dir: Path,
    prefix: str,
    dry_run: bool = False,
) -> int:
    """Migrate a single collection. Returns the number of documents indexed."""
    loader = COLLECTIONS.get(name)
    if loader is None:
        logger.error("Unknown collection: %s (available: %s)",
                     name, ", ".join(COLLECTIONS.keys()))
        return 0

    index_name = f"{prefix}_{name}"
    if not dry_run and not es.indices.exists(index=index_name):
        logger.error("Index %s does not exist. Run setup_indices first.", index_name)
        return 0

    actions = list(loader(data_dir, prefix))
    if not actions:
        logger.warning("No documents found for collection: %s", name)
        return 0

    if dry_run:
        logger.info("[DRY RUN] Would index %d documents into %s", len(actions), index_name)
        return len(actions)

    logger.info("Indexing %d documents into %s...", len(actions), index_name)
    start = time.monotonic()

    try:
        success, errors = bulk(es, actions, raise_on_error=False)
        elapsed = time.monotonic() - start

        if errors:
            logger.error("%d indexing errors in %s:", len(errors), index_name)
            for err in errors[:5]:
                logger.error("  %s", err)

        logger.info("Indexed %d documents into %s in %.2fs", success, index_name, elapsed)

        # Refresh so documents are immediately searchable
        es.indices.refresh(index=index_name)
        return success

    except BulkIndexError as exc:
        logger.error("Bulk indexing failed for %s: %s", index_name, exc)
        return 0


def migrate_all(
    es: Elasticsearch,
    data_dir: Path,
    prefix: str,
    dry_run: bool = False,
    only: list[str] | None = None,
) -> dict[str, int]:
    """Migrate all (or selected) collections. Returns {name: doc_count}."""
    targets = only or list(COLLECTIONS.keys())
    results = {}

    for name in targets:
        count = migrate_collection(es, name, data_dir, prefix, dry_run=dry_run)
        results[name] = count

    return results


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify_counts(es: Elasticsearch, data_dir: Path, prefix: str) -> bool:
    """Verify that indexed document counts match source data."""
    expected = {}

    # Quran
    quran_path = data_dir / "quran" / "quran_complete.json"
    if quran_path.exists():
        with open(quran_path, encoding="utf-8") as f:
            expected["quran"] = len(json.load(f)["verses"])

    # Hadith
    hadith_path = data_dir / "hadith" / "hadith_sample.json"
    if hadith_path.exists():
        with open(hadith_path, encoding="utf-8") as f:
            expected["hadith"] = len(json.load(f)["hadith"])

    # Graph
    graph_path = data_dir / "graph" / "sample_graph.json"
    if graph_path.exists():
        with open(graph_path, encoding="utf-8") as f:
            expected["graph"] = len(json.load(f).get("edges", []))

    # Lessons
    lessons_dir = data_dir / "lessons" / "lessons_enriched_json"
    if lessons_dir.exists():
        expected["lessons"] = len(list(lessons_dir.glob("lesson_*_Anaam.json")))

    all_match = True
    for name, expected_count in expected.items():
        index_name = f"{prefix}_{name}"
        if not es.indices.exists(index=index_name):
            logger.error("Index %s does not exist", index_name)
            all_match = False
            continue

        actual = es.count(index=index_name)["count"]
        status = "OK" if actual == expected_count else "MISMATCH"
        log_fn = logger.info if status == "OK" else logger.error
        log_fn("  %-12s expected=%d  actual=%d  [%s]",
               name, expected_count, actual, status)
        if actual != expected_count:
            all_match = False

    return all_match


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    """Entry point."""
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Migrate static data from JSON files into Elasticsearch")
    parser.add_argument("--collection", nargs="*", default=None,
                        choices=list(COLLECTIONS.keys()),
                        help="Migrate specific collections (default: all)")
    parser.add_argument("--data-dir", type=Path, default=_DEFAULT_DATA_DIR,
                        help=f"Path to data directory (default: {_DEFAULT_DATA_DIR})")
    parser.add_argument("--prefix", default="furqan",
                        help="Index name prefix (default: furqan)")
    parser.add_argument("--es-url", default=None,
                        help="Elasticsearch URL")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview what would be indexed without writing")
    parser.add_argument("--verify", action="store_true",
                        help="Verify document counts after migration")
    args = parser.parse_args()

    hosts = [args.es_url] if args.es_url else None
    es = create_es_client(hosts=hosts)

    logger.info("Data directory: %s", args.data_dir)

    results = migrate_all(
        es,
        data_dir=args.data_dir,
        prefix=args.prefix,
        dry_run=args.dry_run,
        only=args.collection,
    )

    total = sum(results.values())
    logger.info("Migration complete: %d total documents", total)
    for name, count in results.items():
        logger.info("  %-12s %d documents", name, count)

    if args.verify and not args.dry_run:
        logger.info("Verifying document counts...")
        if verify_counts(es, args.data_dir, args.prefix):
            logger.info("All counts verified.")
        else:
            logger.error("Count verification FAILED — check errors above.")


if __name__ == "__main__":
    main()
