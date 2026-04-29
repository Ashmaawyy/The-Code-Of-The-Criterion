"""Enrich clean lesson JSON files with verse and hadith references.

Uses Elasticsearch phrase_match for matching instead of Python sliding-window.
All index names and defaults are read from PipelineConfig.

Usage:
    python -m al_furqan.lessons.enrich_lessons                         # default
    python -m al_furqan.lessons.enrich_lessons --surah 6 --input DIR
"""

import argparse
import json
import logging
from pathlib import Path

from al_furqan.lessons.config import PipelineConfig

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ES-backed matching
# ---------------------------------------------------------------------------

def _get_es_client(config: PipelineConfig):
    """Create an Elasticsearch client from config."""
    from al_furqan.kb.es.client import create_es_client
    return create_es_client(hosts=[config.es_url])


def find_verse_matches(es, content: str, config: PipelineConfig,
                       surah_filter: int | None = None) -> list[dict]:
    """Find Quranic verses referenced in the content using ES phrase_match."""
    query = {
        "match_phrase": {
            "text_ar": {"query": content, "slop": config.verse_match_slop}
        }
    }
    if surah_filter is not None:
        query = {
            "bool": {
                "must": [query],
                "filter": [{"term": {"surah": surah_filter}}],
            }
        }

    resp = es.search(
        index=config.es_quran_index,
        body={"query": query, "size": config.verse_match_limit},
    )
    return [hit["_source"] for hit in resp["hits"]["hits"]]


def find_hadith_matches(es, content: str, config: PipelineConfig) -> list[dict]:
    """Find hadith referenced in the content using ES phrase_match."""
    resp = es.search(
        index=config.es_hadith_index,
        body={
            "query": {
                "match_phrase": {
                    "text_ar": {"query": content, "slop": config.verse_match_slop}
                }
            },
            "size": config.hadith_match_limit,
        },
    )
    return [hit["_source"] for hit in resp["hits"]["hits"]]


# ---------------------------------------------------------------------------
# Format output
# ---------------------------------------------------------------------------

def _index_lesson_to_es(es, lesson: dict, config: PipelineConfig) -> bool:
    """Index a single enriched lesson document into Elasticsearch.

    Uses the same document structure as migrate_data._load_lessons so that
    pipeline-time indexing and bulk migration produce identical documents.
    """
    index = f"{config.es_index_prefix}_lessons"

    if not es.indices.exists(index=index):
        logger.warning("Index %s does not exist — skipping ES indexing", index)
        return False

    lesson_num = lesson["lesson_number"]
    doc_id = f"lesson_{lesson_num:02d}"

    chapters = []
    for ch in lesson.get("chapters", []):
        chapters.append({
            "chapter_number": ch["chapter_number"],
            "title": ch.get("title", ""),
            "content": ch.get("content", ""),
            "taught_verses": ch.get("taught_verses", []),
            "linked_verses": ch.get("linked_verses", []),
            "mentioned_ahadeeth": ch.get("mentioned_ahadeeth", []),
        })

    doc = {
        "lesson_number": lesson_num,
        "surah": lesson.get("surah", ""),
        "title": lesson.get("title", ""),
        "total_chapters": lesson.get("total_chapters", len(chapters)),
        "chapters": chapters,
    }

    try:
        es.index(index=index, id=doc_id, body=doc, refresh="wait_for")
        logger.info("Indexed lesson %02d into %s", lesson_num, index)
        return True
    except Exception:
        logger.exception("Failed to index lesson %02d into ES", lesson_num)
        return False


def format_verse_ref(verse: dict) -> dict:
    return {
        "surah": verse["surah"],
        "surah_name_ar": verse.get("surah_name_ar", ""),
        "surah_name_en": verse.get("surah_name_en", ""),
        "ayah": verse["ayah"],
        "verse_key": verse.get("verse_key", f"{verse['surah']}:{verse['ayah']}"),
        "text_ar": verse["text_ar"],
        "text_en": verse.get("text_en", ""),
    }


def format_hadith_ref(h: dict) -> dict:
    return {
        "collection": h.get("collection_name", ""),
        "number": h.get("number", 0),
        "text_ar": h.get("text_ar", ""),
        "text_en": h.get("text_en", ""),
        "narrator": h.get("narrator", ""),
        "grading": h.get("grading", ""),
    }


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------

def _enrich_single_chapter(chapter, es, config: PipelineConfig):
    """Enrich a single chapter via ES."""
    content = chapter["content"]
    target = config.target_surah

    taught = find_verse_matches(es, content, config, surah_filter=target)
    taught = sorted(taught, key=lambda v: v["ayah"])

    all_verses = find_verse_matches(es, content, config, surah_filter=None)
    linked = [v for v in all_verses if v["surah"] != target]
    linked = sorted(linked, key=lambda v: (v["surah"], v["ayah"]))

    hadith_matches = find_hadith_matches(es, content, config)

    # Deduplicate
    seen_v = set()
    deduped_taught = []
    for v in taught:
        key = (v["surah"], v["ayah"])
        if key not in seen_v:
            seen_v.add(key)
            deduped_taught.append(v)

    deduped_linked = []
    for v in linked:
        key = (v["surah"], v["ayah"])
        if key not in seen_v:
            seen_v.add(key)
            deduped_linked.append(v)

    seen_h = set()
    deduped_hadith = []
    for h in hadith_matches:
        key = (h.get("collection_name", ""), h.get("number", 0))
        if key not in seen_h:
            seen_h.add(key)
            deduped_hadith.append(h)

    chapter["taught_verses"] = [format_verse_ref(v) for v in deduped_taught]
    chapter["linked_verses"] = [format_verse_ref(v) for v in deduped_linked]
    chapter["mentioned_ahadeeth"] = [format_hadith_ref(h) for h in deduped_hadith]
    return len(deduped_taught), len(deduped_linked), len(deduped_hadith)


def process_all(lessons_dir: Path, output_dir: Path,
                config: PipelineConfig | None = None):
    """Run enrichment on all clean lesson JSON files via ES."""
    if config is None:
        config = PipelineConfig()

    es = _get_es_client(config)

    for idx in (config.es_quran_index, config.es_hadith_index):
        if not es.indices.exists(index=idx):
            logger.error("Index %s not found. Run: python -m al_furqan.kb.es.migrate_data", idx)
            return

    quran_count = es.count(index=config.es_quran_index)["count"]
    hadith_count = es.count(index=config.es_hadith_index)["count"]
    logger.info("ES: %d verses, %d hadith (target surah: %d)",
                quran_count, hadith_count, config.target_surah)

    output_dir.mkdir(parents=True, exist_ok=True)
    totals = [0, 0, 0]

    lesson_files = sorted(lessons_dir.glob("lesson_*_Anaam.json"))
    if not lesson_files:
        logger.warning("No lesson files found in %s", lessons_dir)
        return

    for lesson_file in lesson_files:
        try:
            with open(lesson_file, encoding="utf-8") as f:
                lesson = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Failed to read %s: %s", lesson_file.name, exc)
            continue

        lesson_num = lesson["lesson_number"]
        logger.info("Processing lesson %02d...", lesson_num)

        for chapter in lesson["chapters"]:
            counts = _enrich_single_chapter(chapter, es, config)
            for i in range(3):
                totals[i] += counts[i]
            if sum(counts) > 0:
                logger.info("  Ch %2d: %d taught, %d linked, %d hadith",
                            chapter['chapter_number'], *counts)

        out_path = output_dir / lesson_file.name
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(lesson, f, ensure_ascii=False, indent=2)

        _index_lesson_to_es(es, lesson, config)

    logger.info("Total: %d taught, %d linked, %d hadith", *totals)
    logger.info("Output in %s", output_dir)


def main():
    """CLI entry point."""
    from al_furqan.lessons.logging_config import setup_logging
    setup_logging()

    cfg = PipelineConfig()

    parser = argparse.ArgumentParser(
        description="Enrich lessons with verse/hadith references via Elasticsearch.")
    parser.add_argument("--input", type=Path, default=cfg.lessons_clean_dir)
    parser.add_argument("--output", type=Path, default=cfg.lessons_enriched_dir)
    parser.add_argument("--surah", type=int, default=cfg.target_surah,
                        help=f"Target surah (default: {cfg.target_surah})")
    parser.add_argument("--es-url", default=cfg.es_url)
    args = parser.parse_args()

    cfg.target_surah = args.surah
    cfg.es_url = args.es_url

    process_all(args.input, args.output, config=cfg)


if __name__ == "__main__":
    main()
