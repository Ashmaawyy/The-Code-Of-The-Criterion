"""Extract Quranic Arabic Corpus morphological data from the PostgreSQL SQL dump.

Parses the ``mini_quran_dev.sql`` dump file and extracts:
    - words table     → word_id, verse_key, position, text_uthmani, root_id, lemma_id
    - roots table     → root_id, arabic_trilateral (e.g., "ر ح م")
    - lemmas table    → lemma_id, text_clean
    - morphology_word_segments → word_id, pos, root_name, lemma_name, verb_form, pos_tags

Indexes the extracted data directly into the ``furqan_qac_morphology``
Elasticsearch index, keyed by verse_key.  No intermediate JSON files.

Usage:
    python -m al_furqan.tokenizer.qac_extractor                           # default
    python -m al_furqan.tokenizer.qac_extractor --sql path/to/dump.sql
    python -m al_furqan.tokenizer.qac_extractor --es-url http://localhost:9200
    python -m al_furqan.tokenizer.qac_extractor --dry-run                  # parse only
"""

import argparse
import logging
import re
import time
from collections import defaultdict
from pathlib import Path

from al_furqan import setup_logging
from al_furqan.paths import DATA_EXTERNAL

logger = logging.getLogger(__name__)

_DEFAULT_SQL = DATA_EXTERNAL / "mini_quran_dev.sql"


# ---------------------------------------------------------------------------
# PostgreSQL COPY parser
# ---------------------------------------------------------------------------


def _parse_copy_block(f, columns: list[str]) -> list[dict]:
    """Parse a PostgreSQL COPY ... FROM stdin block.

    Reads tab-separated lines until the terminator line '\\.' is found.
    Returns a list of dicts keyed by column names.
    """
    rows = []
    for line in f:
        line = line.rstrip("\n").rstrip("\r")
        if line == "\\.":
            break
        fields = line.split("\t")
        row = {}
        for i, col in enumerate(columns):
            val = fields[i] if i < len(fields) else ""
            row[col] = None if val == "\\N" else val
        rows.append(row)
    return rows


def _extract_columns(copy_line: str) -> list[str]:
    """Extract column names from a COPY statement."""
    # COPY quran.table_name (col1, col2, ...) FROM stdin;
    m = re.search(r"\((.+?)\)", copy_line)
    if not m:
        return []
    raw = m.group(1)
    # Handle quoted column names like "position"
    cols = [c.strip().strip('"') for c in raw.split(",")]
    return cols


# ---------------------------------------------------------------------------
# Main extraction
# ---------------------------------------------------------------------------


def extract_qac(sql_path: Path) -> dict:
    """Parse the SQL dump and return structured morphological data.

    Returns:
        {
            "roots": {root_id: {"letters": "ر ح م", "trilateral": "ر-ح-م"}},
            "lemmas": {lemma_id: {"text": "..."}},
            "words": {word_id: {"verse_key": "1:1", "position": 1, "text": "بِسْمِ", ...}},
            "segments": {word_id: [{"pos": "P", "pos_name": "preposition", ...}]},
            "by_verse": {"1:1": [word_annotations_in_order]},
        }
    """
    roots = {}
    lemmas = {}
    words = {}
    segments = defaultdict(list)

    logger.info("Parsing SQL dump: %s (this may take a minute...)", sql_path)
    start = time.monotonic()

    with open(sql_path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n").rstrip("\r")

            # --- roots ---
            if line.startswith("COPY quran.roots "):
                cols = _extract_columns(line)
                for row in _parse_copy_block(f, cols):
                    rid = row.get("id")
                    if rid:
                        text_clean = row.get("text_clean", "") or ""
                        letters = text_clean.strip().split()
                        roots[rid] = {
                            "letters_spaced": text_clean.strip(),
                            "trilateral": "-".join(letters),
                            "arabic_trilateral": row.get("arabic_trilateral", ""),
                            "english_trilateral": row.get("english_trilateral", ""),
                            "frequency": row.get("words_count", "0"),
                        }

            # --- lemmas ---
            elif line.startswith("COPY quran.lemmas "):
                cols = _extract_columns(line)
                for row in _parse_copy_block(f, cols):
                    lid = row.get("id")
                    if lid:
                        lemmas[lid] = {
                            "text": row.get("text_madani", "")
                            or row.get("text_clean", ""),
                            "text_clean": row.get("text_clean", ""),
                            "en_translations": row.get("en_translations", ""),
                        }

            # --- words ---
            elif line.startswith("COPY quran.words "):
                cols = _extract_columns(line)
                for row in _parse_copy_block(f, cols):
                    wid = row.get("id")
                    if wid:
                        words[wid] = {
                            "verse_key": row.get("verse_key", ""),
                            "position": int(row.get("position", 0) or 0),
                            "text_uthmani": row.get("text_uthmani", ""),
                            "text_clean": row.get("text_imlaei_simple", ""),
                            "transliteration": row.get("en_transliteration", ""),
                            "root_id": row.get("root_id"),
                            "lemma_id": row.get("lemma_id"),
                            "stem_id": row.get("stem_id"),
                            "char_type": row.get("char_type_name", ""),
                        }

            # --- morphology_word_segments ---
            elif line.startswith("COPY quran.morphology_word_segments "):
                cols = _extract_columns(line)
                for row in _parse_copy_block(f, cols):
                    wid = row.get("word_id")
                    if wid:
                        segments[wid].append(
                            {
                                "position": int(row.get("position", 0) or 0),
                                "text": row.get("text_uthmani", ""),
                                "pos_key": row.get("part_of_speech_key", ""),
                                "pos_name": row.get("part_of_speech_name", ""),
                                "pos_tags": row.get("pos_tags", ""),
                                "root_name": row.get("root_name", ""),
                                "lemma_name": row.get("lemma_name", ""),
                                "verb_form": row.get("verb_form", ""),
                                "grammar_desc_en": row.get(
                                    "grammar_term_desc_english", ""
                                ),
                                "grammar_desc_ar": row.get(
                                    "grammar_term_desc_arabic", ""
                                ),
                                "segment_type": row.get("segment_type", ""),
                            }
                        )

    elapsed = time.monotonic() - start
    logger.info(
        "Parsed: %d roots, %d lemmas, %d words, %d segment entries in %.1fs",
        len(roots),
        len(lemmas),
        len(words),
        sum(len(v) for v in segments.values()),
        elapsed,
    )

    # --- Build by_verse index ---
    by_verse = defaultdict(list)
    for wid, word_data in words.items():
        vk = word_data.get("verse_key", "")
        if not vk or word_data.get("char_type") != "word":
            continue

        root_id = word_data.get("root_id")
        lemma_id = word_data.get("lemma_id")

        # Resolve root
        root_info = roots.get(root_id, {}) if root_id else {}
        lemma_info = lemmas.get(lemma_id, {}) if lemma_id else {}

        # Merge segment data
        word_segments = segments.get(wid, [])
        # Sort segments by position
        word_segments.sort(key=lambda s: s.get("position", 0))

        # Collect POS tags from segments
        pos_tags = []
        for seg in word_segments:
            if seg.get("pos_tags"):
                pos_tags.extend(seg["pos_tags"].split(","))

        annotation = {
            "word_id": wid,
            "position": word_data["position"],
            "text_uthmani": word_data["text_uthmani"],
            "text_clean": word_data["text_clean"],
            "transliteration": word_data.get("transliteration", ""),
            "root": root_info.get("trilateral", ""),
            "root_letters": root_info.get("letters_spaced", ""),
            "root_arabic": root_info.get("arabic_trilateral", ""),
            "lemma": lemma_info.get("text", ""),
            "lemma_clean": lemma_info.get("text_clean", ""),
            "pos_tags": list(dict.fromkeys(pos_tags)),  # deduplicate
            "segments": word_segments,
            "verb_form": next(
                (s.get("verb_form", "") for s in word_segments if s.get("verb_form")),
                "",
            ),
        }
        by_verse[vk].append(annotation)

    # Sort words within each verse by position
    for vk in by_verse:
        by_verse[vk].sort(key=lambda w: w["position"])

    logger.info("Built verse index: %d verses with word annotations", len(by_verse))

    return {
        "meta": {
            "source": str(sql_path),
            "roots_count": len(roots),
            "lemmas_count": len(lemmas),
            "words_count": len(words),
            "verses_count": len(by_verse),
        },
        "by_verse": dict(by_verse),
    }


# ---------------------------------------------------------------------------
# ES index definition for QAC morphology data
# ---------------------------------------------------------------------------

QAC_INDEX_NAME = "furqan_qac_morphology"

QAC_INDEX_DEFINITION = {
    "settings": {"number_of_shards": 1, "number_of_replicas": 0},
    "mappings": {
        "properties": {
            "verse_key": {"type": "keyword"},
            "words": {
                "type": "nested",
                "properties": {
                    "word_id": {"type": "keyword"},
                    "position": {"type": "integer"},
                    "text_uthmani": {"type": "keyword"},
                    "text_clean": {"type": "keyword"},
                    "transliteration": {"type": "keyword"},
                    "root": {"type": "keyword"},
                    "root_letters": {"type": "keyword"},
                    "root_arabic": {"type": "keyword"},
                    "lemma": {"type": "keyword"},
                    "lemma_clean": {"type": "keyword"},
                    "pos_tags": {"type": "keyword"},
                    "verb_form": {"type": "keyword"},
                    "segments": {"type": "object", "enabled": False},
                },
            },
        },
    },
}


def index_to_es(data: dict, es, index: str = QAC_INDEX_NAME) -> int:
    """Bulk-index extracted QAC data into Elasticsearch.

    Args:
        data: Output of extract_qac() with "by_verse" key.
        es: Elasticsearch client.
        index: Target index name.

    Returns:
        Number of documents indexed.
    """
    from elasticsearch.helpers import bulk

    by_verse = data.get("by_verse", {})
    if not by_verse:
        logger.warning("No verse data to index")
        return 0

    # Create index if needed
    if not es.indices.exists(index=index):
        logger.info("Creating index: %s", index)
        es.indices.create(index=index, body=QAC_INDEX_DEFINITION)

    actions = []
    for verse_key, word_list in by_verse.items():
        actions.append(
            {
                "_index": index,
                "_id": verse_key,
                "_source": {
                    "verse_key": verse_key,
                    "words": word_list,
                },
            }
        )

    logger.info("Indexing %d verses into %s...", len(actions), index)
    success, errors = bulk(es, actions, raise_on_error=False)
    if errors:
        logger.warning("%d indexing errors", len(errors))

    es.indices.refresh(index=index)
    logger.info("Indexed %d verses into %s", success, index)
    return success


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Extract QAC morphological data from SQL dump into Elasticsearch"
    )
    parser.add_argument(
        "--sql",
        type=Path,
        default=_DEFAULT_SQL,
        help=f"Path to SQL dump (default: {_DEFAULT_SQL})",
    )
    parser.add_argument(
        "--es-url",
        default=None,
        help="Elasticsearch URL (default: from env or localhost:9200)",
    )
    parser.add_argument(
        "--index",
        default=QAC_INDEX_NAME,
        help=f"Target index name (default: {QAC_INDEX_NAME})",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Parse SQL but don't index to ES"
    )
    args = parser.parse_args()

    if not args.sql.exists():
        logger.error("SQL dump not found: %s", args.sql)
        return

    data = extract_qac(args.sql)

    if args.dry_run:
        logger.info(
            "[DRY RUN] Parsed %d verses, would index to %s",
            len(data.get("by_verse", {})),
            args.index,
        )
        # Show a sample
        by_verse = data.get("by_verse", {})
        sample_key = next(iter(by_verse), None)
        if sample_key:
            sample = by_verse[sample_key]
            logger.info("Sample verse %s: %d words", sample_key, len(sample))
            for w in sample[:3]:
                logger.info(
                    "  pos=%d text=%s root=%s pos_tags=%s",
                    w.get("position", 0),
                    w.get("text_clean", ""),
                    w.get("root", ""),
                    w.get("pos_tags", []),
                )
        return

    from al_furqan.kb.es.client import create_es_client

    hosts = [args.es_url] if args.es_url else None
    es = create_es_client(hosts=hosts)

    count = index_to_es(data, es, index=args.index)
    logger.info("Done: %d verses indexed", count)


if __name__ == "__main__":
    main()
