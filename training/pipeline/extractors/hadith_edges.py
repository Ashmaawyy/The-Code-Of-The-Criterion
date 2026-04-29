"""Extract ayah→hadith edges via Quran quote detection in hadith texts.

Three sources of verse-hadith links:
  1. Curated edges from sample_graph.json
  2. {}-bracketed Quran quotes in plain hadith CSVs
  3. Commentary analysis from mushakkala_mufassala CSVs:
     - "قوله تعالى" + (quote) or {quote} patterns
     - {}-bracketed quotes in scholarly commentary
"""

from __future__ import annotations

import csv
import logging
import re
from pathlib import Path

from al_furqan.paths import DATA_HADITH as HADITH_DIR
from training.pipeline.extractors.loaders import load_graph_edges, load_quran_map
from training.pipeline.extractors.types import ExtractorResult, add_edge

logger = logging.getLogger(__name__)

# Pattern: collection name from filename
_COLLECTION_RE = re.compile(r"^(.+?)_ahadith(?:_mushakkala(?:_mufassala)?)?\.utf8\.csv$")

# Quote extraction patterns
_BRACE_RE = re.compile(r"\{([^}]{5,})\}")
_PAREN_RE = re.compile(r"\(([^)]{5,})\)")
_QAWL_BRACE_RE = re.compile(r"قَوْلُ?هُ?\s*تَعَالَى\s*[:\s]*\{([^}]{5,}?)\}")
_QAWL_PAREN_RE = re.compile(r"قَوْلُ?هُ?\s*تَعَالَى\s*[:\s]*\(([^)]{5,}?)\)")

# Arabic normalization for matching
_DIACRITICS = re.compile(
    "[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E4"
    "\u06E7\u06E8\u06EA-\u06ED\u200F]"
)
_ALEF_VARIANTS = re.compile("[\u0625\u0623\u0622\u0671]")
_TAA_MARBOUTA = re.compile("\u0629")
_ALEF_MAQSURA = re.compile("\u0649")
_TATWEEL = re.compile("\u0640")


def _normalize(text: str) -> str:
    """Minimal Arabic normalization for fuzzy matching."""
    text = _DIACRITICS.sub("", text)
    text = _ALEF_VARIANTS.sub("\u0627", text)
    text = _TAA_MARBOUTA.sub("\u0647", text)
    text = _ALEF_MAQSURA.sub("\u064A", text)
    text = _TATWEEL.sub("", text)
    return " ".join(text.split())


def _build_verse_index(quran: dict[str, dict]) -> dict[str, list[str]]:
    """Build normalized 4-word-window → [verse_key] index for matching."""
    index: dict[str, list[str]] = {}
    for vk, v in quran.items():
        norm = _normalize(v.get("text_ar", ""))
        words = norm.split()
        # Index all 4-word windows
        window = min(4, len(words))
        for i in range(len(words) - window + 1):
            key = " ".join(words[i:i + window])
            index.setdefault(key, []).append(vk)
    return index


def _match_quote(quote_norm: str, window_index: dict[str, list[str]]) -> list[str]:
    """Match a normalized quote against the verse window index."""
    words = quote_norm.split()
    if len(words) < 4:
        return []

    # Try the first 4-word window
    key = " ".join(words[:4])
    matches = window_index.get(key, [])
    if not matches and len(words) >= 5:
        # Try second window
        key = " ".join(words[1:5])
        matches = window_index.get(key, [])

    return matches


def extract(**kwargs) -> ExtractorResult:
    result: ExtractorResult = {}

    quran = load_quran_map()
    window_index = _build_verse_index(quran)
    logger.info("Built verse matching index (%d windows)", len(window_index))

    # Source 1: Knowledge graph curated edges
    graph_count = 0
    for edge in load_graph_edges():
        src_raw = edge.get("source", "")
        tgt_raw = edge.get("target", "")
        etype = edge.get("edge_type", "")

        # hadith→ayah edges
        if src_raw.startswith("hadith:") and tgt_raw.startswith("ayah:") and etype == "EXPLAINS":
            parts = tgt_raw.split(":", 2)
            if len(parts) == 3:
                vk = f"{parts[1]}:{parts[2]}"
                add_edge(result, vk, {
                    "edge_type": "hadith",
                    "target_id": src_raw,
                    "weight": edge.get("weight", 1.0),
                    "confidence": edge.get("confidence", 1.0),
                    "provenance": "knowledge_graph",
                    "data": {"relation": "explains", "reference": edge.get("reference", "")},
                })
                graph_count += 1

    logger.info("hadith (graph): %d curated edges", graph_count)

    # Dedup tracker: (verse_key, collection, hadith_num) -> True
    seen: set[tuple[str, str, str]] = set()

    def _add_hadith_edge(
        vk: str, collection: str, hadith_num: str,
        quote: str, text: str, provenance: str,
        confidence: float,
    ) -> bool:
        key = (vk, collection, hadith_num)
        if key in seen:
            return False
        seen.add(key)
        add_edge(result, vk, {
            "edge_type": "hadith",
            "target_id": f"hadith:{collection}:{hadith_num}",
            "weight": 0.9,
            "confidence": confidence,
            "provenance": provenance,
            "data": {
                "collection": collection,
                "number": hadith_num,
                "matched_quote": quote.strip()[:200],
                "hadith_text": text.strip()[:500],
            },
        })
        return True

    def _match_and_add(
        quotes: list[str], collection: str, hadith_num: str,
        text: str, provenance: str, confidence: float,
    ) -> int:
        count = 0
        for quote in quotes:
            quote_norm = _normalize(quote)
            for vk in _match_quote(quote_norm, window_index):
                if _add_hadith_edge(vk, collection, hadith_num,
                                     quote, text, provenance, confidence):
                    count += 1
        return count

    # Source 2: Quote detection in plain hadith CSVs
    plain_count = 0
    for csv_path in sorted(HADITH_DIR.glob("*_ahadith.utf8.csv")):
        if "mushakkala" in csv_path.name:
            continue

        m = _COLLECTION_RE.match(csv_path.name)
        collection = m.group(1).replace("-", "_") if m else csv_path.stem

        file_matches = 0
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 2:
                    continue
                hadith_num = row[0].strip()
                text = row[1]
                quotes = _BRACE_RE.findall(text)
                if quotes:
                    n = _match_and_add(quotes, collection, hadith_num,
                                       text, f"quote_detect:{collection}", 0.85)
                    file_matches += n

        if file_matches:
            logger.info("  %s (plain): %d links", collection, file_matches)
        plain_count += file_matches

    # Source 3: Commentary analysis from mushakkala_mufassala CSVs
    comm_count = 0
    for csv_path in sorted(HADITH_DIR.glob("*_mushakkala_mufassala.utf8.csv")):
        m = _COLLECTION_RE.match(csv_path.name)
        collection = m.group(1).replace("-", "_") if m else csv_path.stem

        file_matches = 0
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 3 or not row[2].strip():
                    continue
                hadith_num = row[0].strip()
                hadith_text = row[1].strip()[:500]
                commentary = row[2]

                # High confidence: "قوله تعالى" + quoted text
                quotes = _QAWL_BRACE_RE.findall(commentary)
                quotes += _QAWL_PAREN_RE.findall(commentary)
                if quotes:
                    n = _match_and_add(quotes, collection, hadith_num,
                                       hadith_text, f"commentary_qawl:{collection}", 0.95)
                    file_matches += n

                # Medium confidence: {}-bracketed quotes in commentary
                brace_quotes = _BRACE_RE.findall(commentary)
                if brace_quotes:
                    n = _match_and_add(brace_quotes, collection, hadith_num,
                                       hadith_text, f"commentary_brace:{collection}", 0.80)
                    file_matches += n

        if file_matches:
            logger.info("  %s (commentary): %d links", collection, file_matches)
        comm_count += file_matches

    total = graph_count + plain_count + comm_count
    logger.info("hadith: %d total edges (%d graph + %d plain + %d commentary) across %d verses",
                total, graph_count, plain_count, comm_count, len(result))
    return result
