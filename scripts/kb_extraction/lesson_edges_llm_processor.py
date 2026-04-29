#!/usr/bin/env python3
"""Extract relationship edges from a lesson transcript via LLM.

Chunks the transcript and runs the relationship extractor over a slice of
chunks. Results are saved to ProposedEdgeStore. Supersedes the earlier
process_lesson_01.py / extract_remaining_chunks.py pair.

Usage:
    python extract_lesson.py                          # process all chunks of lesson_01
    python extract_lesson.py --start 3 --end 14       # only chunks 3..13
    python extract_lesson.py --transcript path.json --lesson-id ep02
"""

import argparse
import logging
import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from al_furqan import setup_logging  # noqa: E402
from al_furqan.kb.ingestion.transcript_chunker import chunk_transcript, format_chunk_timestamp  # noqa: E402
from al_furqan.kb.ingestion.proposed_edge_store import ProposedEdgeStore  # noqa: E402
from al_furqan.kb.ingestion.reference_validator import validate_reference  # noqa: E402
from al_furqan.kb.ingestion.relationship_extractor import (  # noqa: E402
    extract_relationships,
    create_extraction_llm,
)
from al_furqan.paths import DATA_LESSONS, PROPOSED_EDGES_DB  # noqa: E402

logger = logging.getLogger(__name__)

DEFAULT_TRANSCRIPT = str(DATA_LESSONS / "lesson_01_transcript.json")
DEFAULT_DB = str(PROPOSED_EDGES_DB)
DEFAULT_MODEL = "qwen3-235b-a22b"
DEFAULT_LESSON_ID = "lesson_01"
DEFAULT_LESSON_REF = "مدارسة سورة الأنعام — الحلقة 01"


def main():  # pylint: disable=too-many-locals, too-many-statements
    setup_logging()
    parser = argparse.ArgumentParser(description="Extract KG edges from a lesson transcript")
    parser.add_argument("--transcript", default=DEFAULT_TRANSCRIPT, help="Transcript JSON path")
    parser.add_argument("--lesson-id", default=DEFAULT_LESSON_ID)
    parser.add_argument("--lesson-reference", default=DEFAULT_LESSON_REF)
    parser.add_argument("--db-path", default=DEFAULT_DB)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--overlap", type=int, default=50)
    parser.add_argument("--start", type=int, default=0, help="First chunk index (inclusive)")
    parser.add_argument("--end", type=int, default=None, help="Last chunk index (exclusive); default = all")
    args = parser.parse_args()

    api_key = os.environ.get("DASHSCOPE_API_KEY", "")
    if not api_key:
        raise SystemExit("DASHSCOPE_API_KEY environment variable not set")

    logger.info("=" * 60)
    logger.info("Al-Furqan KG Extractor - lesson=%s model=%s", args.lesson_id, args.model)
    logger.info("=" * 60)

    logger.info("Chunking transcript %s", args.transcript)
    chunks = chunk_transcript(args.transcript, chunk_size=args.chunk_size, overlap=args.overlap)
    logger.info("   Total chunks: %d", len(chunks))

    end = args.end if args.end is not None else len(chunks)
    start = max(0, args.start)
    end = min(end, len(chunks))
    if start >= end:
        logger.error("Empty chunk range: start=%d end=%d", start, end)
        return

    logger.info("Processing chunks [%d, %d)", start, end)

    llm = create_extraction_llm(api_key=api_key, model_name=args.model)
    store = ProposedEdgeStore(db_path=args.db_path)
    logger.info("   DB: %s", args.db_path)

    all_edges = []
    all_verse_refs = []
    all_topics = set()
    central_verse = ""
    total_errors = 0

    for i in range(start, end):
        chunk = chunks[i]
        logger.info("--- Chunk %d (%d words, %s) ---", i, chunk.word_count, format_chunk_timestamp(chunk))
        chunk._previous_central_verse = central_verse  # pylint: disable=protected-access

        t0 = time.time()
        try:
            result = extract_relationships(
                chunk=chunk,
                llm=llm,
                lesson_id=args.lesson_id,
                lesson_reference=args.lesson_reference,
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.exception("   Error on chunk %d: %s", i, e)
            total_errors += 1
            continue
        elapsed = time.time() - t0

        if hasattr(result, "central_verse") and result.central_verse:
            central_verse = result.central_verse

        logger.info("   LLM response in %.1fs | edges=%d | verse_refs=%s | topics=%s",
                    elapsed, len(result.edges), result.verse_references, result.topics)

        for edge in result.edges:
            store.save(edge)
            logger.info("    %s --%s--> %s (conf:%s)",
                        edge.source_node, edge.edge_type, edge.target_node, edge.llm_confidence)

        all_edges.extend(result.edges)
        all_verse_refs.extend(result.verse_references)
        all_topics.update(result.topics)

    logger.info("Validating %d verse references...", len(all_verse_refs))
    valid = 0
    invalid = 0
    for ref in all_verse_refs:
        r = validate_reference(ref)
        if r.valid:
            valid += 1
        else:
            invalid += 1
            logger.warning("   Invalid: %s - %s", ref, r.error)
    logger.info("   Valid: %d, Invalid: %d", valid, invalid)

    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info("   Chunks processed: %d..%d (of %d total)", start, end - 1, len(chunks))
    logger.info("   New edges:        %d", len(all_edges))
    logger.info("   Errors:           %d", total_errors)
    if all_edges:
        avg_conf = sum(e.llm_confidence for e in all_edges) / len(all_edges)
        logger.info("   Avg confidence:   %.3f", avg_conf)
    logger.info("   Topics found:     %d", len(all_topics))
    logger.info("   Store stats:      %s", store.get_stats())

    store.close()


if __name__ == "__main__":
    main()
