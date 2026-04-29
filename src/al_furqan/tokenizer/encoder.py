"""Multi-level Quran encoder.

Reads verses from the ES ``furqan_quran`` index (or from JSON), runs
all tokenization levels (word, root, semantic, logic, transition), and
writes the result to the ``furqan_quran_tokens`` ES index.

The phonetic/tajweed layer has been deliberately removed.  The training
signal focuses on *idea transitions* and *logical structure* — teaching
the LLM how the Quran moves between concepts with smooth, robust logic.

Usage:
    python -m al_furqan.tokenizer.encoder                          # encode all
    python -m al_furqan.tokenizer.encoder --surah 1                # encode one surah
    python -m al_furqan.tokenizer.encoder --verse 2:255            # encode one verse
    python -m al_furqan.tokenizer.encoder --from-json data/quran/quran_complete.json
    python -m al_furqan.tokenizer.encoder --dry-run                # preview
"""

from __future__ import annotations

import argparse
import logging
import re
import time

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from al_furqan import setup_logging
from al_furqan.kb.es.client import create_es_client
from al_furqan.tokenizer.schema import (
    WordToken, RootToken, SemanticToken, VerseTokens,
)
from al_furqan.tokenizer.morphology import analyze_word, analyze_verse
from al_furqan.tokenizer.semantics import (
    analyze_semantics, analyze_verse_logic, analyze_verse_transitions,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tokenize a single verse
# ---------------------------------------------------------------------------

_WORD_SPLIT = re.compile(r'\s+')


def tokenize_verse(
    surah: int,
    ayah: int,
    text_ar: str,
    text_en: str = "",
    juz: int = 0,
    page: int = 0,
    position_in_mushaf: int = 0,
) -> VerseTokens:
    """Tokenize a single verse at all three levels.

    Args:
        surah: Surah number.
        ayah: Ayah number.
        text_ar: Full Arabic text with diacritics.
        text_en: English translation.
        juz: Juz number.
        page: Page number.
        position_in_mushaf: Global sequential position (0-indexed).

    Returns:
        VerseTokens with all three token levels populated.
    """
    verse_key = f"{surah}:{ayah}"
    words = _WORD_SPLIT.split(text_ar.strip())
    words = [w for w in words if w]  # remove empties

    # Use QAC-aware analysis (falls back to rule-based if QAC not available)
    morph_results = analyze_verse(verse_key, text_ar)

    word_tokens: list[WordToken] = []
    root_tokens: list[RootToken] = []
    semantic_tokens: list[SemanticToken] = []
    seen_roots: set[str] = set()

    for i, word in enumerate(words):
        # --- Level 1: Word ---
        morph = morph_results[i] if i < len(morph_results) else analyze_word(word)
        word_tokens.append(WordToken(
            position=i,
            surface=word,
            surface_clean=morph.surface_clean,
            is_stop_word=morph.is_stop_word,
        ))

        # --- Level 2A: Root ---
        root_tokens.append(RootToken(
            position=i,
            surface=word,
            root=morph.root,
            root_letters=morph.root_letters,
            pattern=morph.pattern,
            pos=morph.pos,
            verb_form="NONE",
            prefixes=morph.prefixes,
            suffixes=morph.suffixes,
            lemma=morph.surface_clean,
        ))
        if morph.root:
            seen_roots.add(morph.root)

        # --- Level 2B: Semantic ---
        semantic_tokens.append(analyze_semantics(morph, i))

    # --- Level 2C: Logic (requires full verse context) ---
    logic_tokens = analyze_verse_logic(morph_results)

    # --- Level 3: Transition (idea flow between words) ---
    transition_tokens = analyze_verse_transitions(
        morph_results, semantic_tokens, logic_tokens,
    )

    return VerseTokens(
        surah=surah,
        ayah=ayah,
        verse_key=verse_key,
        text_ar=text_ar,
        text_en=text_en,
        word_tokens=word_tokens,
        root_tokens=root_tokens,
        semantic_tokens=semantic_tokens,
        logic_tokens=logic_tokens,
        transition_tokens=transition_tokens,
        word_count=len(words),
        unique_roots=len(seen_roots),
        reasoning_pattern="none",  # TODO: classify at surah/passage level
        certainty=1.0,
        juz=juz,
        page=page,
        position_in_surah=ayah - 1,
        position_in_mushaf=position_in_mushaf,
    )


# ---------------------------------------------------------------------------
# ES index definition for tokenized data
# ---------------------------------------------------------------------------

TOKEN_INDEX_DEFINITION = {
    "settings": {"number_of_shards": 1, "number_of_replicas": 0},
    "mappings": {
        "properties": {
            "surah": {"type": "integer"},
            "ayah": {"type": "integer"},
            "verse_key": {"type": "keyword"},
            "text_ar": {"type": "text", "analyzer": "standard"},
            "text_en": {"type": "text", "analyzer": "english"},
            "word_tokens": {
                "type": "nested",
                "properties": {
                    "position": {"type": "integer"},
                    "surface": {"type": "keyword"},
                    "surface_clean": {"type": "keyword"},
                    "is_stop_word": {"type": "boolean"},
                },
            },
            "root_tokens": {
                "type": "nested",
                "properties": {
                    "position": {"type": "integer"},
                    "surface": {"type": "keyword"},
                    "root": {"type": "keyword"},
                    "root_letters": {"type": "keyword"},
                    "pattern": {"type": "keyword"},
                    "pos": {"type": "keyword"},
                    "verb_form": {"type": "keyword"},
                    "prefixes": {"type": "keyword"},
                    "suffixes": {"type": "keyword"},
                    "lemma": {"type": "keyword"},
                },
            },
            "semantic_tokens": {
                "type": "nested",
                "properties": {
                    "position": {"type": "integer"},
                    "surface": {"type": "keyword"},
                    "semantic_field": {"type": "keyword"},
                    "pattern_meaning": {"type": "keyword"},
                    "syntactic_role": {"type": "keyword"},
                    "referent": {"type": "keyword"},
                    "scope": {"type": "keyword"},
                    "meaning_ar": {"type": "text", "analyzer": "standard"},
                    "meaning_en": {"type": "text", "analyzer": "english"},
                },
            },
            "logic_tokens": {
                "type": "nested",
                "properties": {
                    "position": {"type": "integer"},
                    "surface": {"type": "keyword"},
                    "operator": {"type": "keyword"},
                    "role_in_argument": {"type": "keyword"},
                    "connects_to": {"type": "integer"},
                    "negation_scope": {"type": "integer"},
                    "emphasis_level": {"type": "float"},
                },
            },
            "transition_tokens": {
                "type": "nested",
                "properties": {
                    "position": {"type": "integer"},
                    "surface": {"type": "keyword"},
                    "transition_type": {"type": "keyword"},
                    "source_idea": {"type": "keyword"},
                    "target_idea": {"type": "keyword"},
                    "smoothness": {"type": "float"},
                    "discourse_depth": {"type": "integer"},
                    "returns_to": {"type": "integer"},
                },
            },
            "word_count": {"type": "integer"},
            "unique_roots": {"type": "integer"},
            "reasoning_pattern": {"type": "keyword"},
            "certainty": {"type": "float"},
            "juz": {"type": "integer"},
            "page": {"type": "integer"},
            "position_in_surah": {"type": "integer"},
            "position_in_mushaf": {"type": "integer"},
        },
    },
}


# ---------------------------------------------------------------------------
# Bulk encoding pipeline
# ---------------------------------------------------------------------------

def encode_from_es(
    es: Elasticsearch,
    source_index: str = "furqan_quran",
    target_index: str = "furqan_quran_tokens",
    surah_filter: int | None = None,
    dry_run: bool = False,
) -> int:
    """Read verses from ES, tokenize, and write to the tokens index.

    Returns the number of verses encoded.
    """
    # Create target index if it doesn't exist
    if not dry_run:
        if not es.indices.exists(index=target_index):
            logger.info("Creating index: %s", target_index)
            es.indices.create(index=target_index, body=TOKEN_INDEX_DEFINITION)

    # Build query
    query = {"match_all": {}}
    if surah_filter is not None:
        query = {"term": {"surah": surah_filter}}

    # Count total
    total = es.count(index=source_index, body={"query": query})["count"]
    logger.info("Encoding %d verses from %s...", total, source_index)

    if dry_run:
        logger.info("[DRY RUN] Would encode %d verses", total)
        return total

    # Scroll through all verses
    batch_size = 500
    resp = es.search(
        index=source_index,
        body={"query": query, "sort": [{"surah": "asc"}, {"ayah": "asc"}], "size": batch_size},
        scroll="5m",
    )
    scroll_id = resp["_scroll_id"]

    encoded = 0
    global_position = 0
    actions = []

    while True:
        hits = resp["hits"]["hits"]
        if not hits:
            break

        for hit in hits:
            src = hit["_source"]
            vt = tokenize_verse(
                surah=src["surah"],
                ayah=src["ayah"],
                text_ar=src.get("text_ar", ""),
                text_en=src.get("text_en", ""),
                juz=src.get("juz", 0),
                page=src.get("page", 0),
                position_in_mushaf=global_position,
            )
            actions.append({
                "_index": target_index,
                "_id": vt.verse_key,
                "_source": vt.to_dict(),
            })
            global_position += 1

        # Flush batch
        if actions:
            success, errors = bulk(es, actions, raise_on_error=False)
            if errors:
                logger.warning("%d indexing errors", len(errors))
            encoded += success
            actions = []

        resp = es.scroll(scroll_id=scroll_id, scroll="5m")

    es.clear_scroll(scroll_id=scroll_id)
    es.indices.refresh(index=target_index)

    logger.info("Encoded %d/%d verses into %s", encoded, total, target_index)
    return encoded


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Multi-level Quran tokenizer — reads from ES, writes tokens to ES")
    parser.add_argument("--surah", type=int, default=None,
                        help="Encode only this surah number")
    parser.add_argument("--verse", default=None,
                        help="Encode a single verse (format: surah:ayah)")
    parser.add_argument("--source-index", default="furqan_quran",
                        help="Source ES index with raw verses (default: furqan_quran)")
    parser.add_argument("--target-index", default="furqan_quran_tokens",
                        help="Target ES index for tokenized output")
    parser.add_argument("--es-url", default=None,
                        help="Elasticsearch URL")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without indexing")
    args = parser.parse_args()

    hosts = [args.es_url] if args.es_url else None
    es = create_es_client(hosts=hosts)

    start = time.monotonic()

    if args.verse:
        # Single verse mode — read from ES
        surah, ayah = args.verse.split(":")
        surah, ayah = int(surah), int(ayah)

        doc = es.get(index=args.source_index, id=f"{surah}:{ayah}")
        verse = doc["_source"] if doc else None

        if not verse:
            logger.error("Verse %d:%d not found in %s", surah, ayah, args.source_index)
            return

        vt = tokenize_verse(
            surah=verse["surah"], ayah=verse["ayah"],
            text_ar=verse["text_ar"], text_en=verse.get("text_en", ""),
            juz=verse.get("juz", 0), page=verse.get("page", 0),
        )

        logger.info("Verse %s: %s", vt.verse_key, vt.text_ar[:60])
        logger.info("Words: %d | Unique roots: %d | Certainty: %.1f",
                    vt.word_count, vt.unique_roots, vt.certainty)

        for i, (wt, rt, st, lt, tt) in enumerate(
            zip(vt.word_tokens, vt.root_tokens, vt.semantic_tokens,
                vt.logic_tokens, vt.transition_tokens)
        ):
            logger.info(
                "  [%d] %s | root=%s pos=%s | sem=%s logic=%s(%s) | "
                "transition=%s src=%s→tgt=%s",
                i, wt.surface, rt.root, rt.pos,
                st.semantic_field, lt.operator, lt.role_in_argument,
                tt.transition_type, tt.source_idea, tt.target_idea,
            )

        if not args.dry_run:
            if not es.indices.exists(index=args.target_index):
                es.indices.create(index=args.target_index, body=TOKEN_INDEX_DEFINITION)
            es.index(index=args.target_index, id=vt.verse_key,
                    body=vt.to_dict(), refresh="wait_for")
            logger.info("Indexed to %s/%s", args.target_index, vt.verse_key)

    else:
        encode_from_es(es, source_index=args.source_index,
                      target_index=args.target_index,
                      surah_filter=args.surah, dry_run=args.dry_run)

    elapsed = time.monotonic() - start
    logger.info("Done in %.1fs", elapsed)


if __name__ == "__main__":
    main()
