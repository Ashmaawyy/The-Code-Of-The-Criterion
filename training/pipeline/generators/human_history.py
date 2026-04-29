"""Build a unified human history JSONL from reliable sources only.

Sources:
  1. RAND Corporation reports (pre-fetched JSON) — 42+ reports, 316K+ chars
  2. YouTube lesson transcripts (Whisper) — 62 lessons

Output: data_archive/training/human_history.jsonl

Usage:
    python -m training.pipeline.generators.human_history
"""

from __future__ import annotations

import json
import logging
import re
from collections import defaultdict

from al_furqan.paths import DATA_HUMAN_HISTORY as DATA_DIR, HUMAN_HISTORY_JSONL as OUTPUT_PATH

logger = logging.getLogger(__name__)

RAND_PATH = DATA_DIR / "rand_reports.json"
CFR_PATH = DATA_DIR / "cfr_reports.json"
CRS_PATH = DATA_DIR / "crs_reports.json"
WIKI_PATH = DATA_DIR / "wikipedia_articles.json"
GUTENBERG_PATH = DATA_DIR / "gutenberg_books.json"
BROOKINGS_PATH = DATA_DIR / "brookings_reports.json"
TUCKER_DIR = DATA_DIR / "tucker_carlson_show_txt"

CHUNK_CHARS = 6000
BOOK_CHUNK_CHARS = 8000  # larger chunks for books


# ---------------------------------------------------------------------------
# Source 1: RAND Corporation reports
# ---------------------------------------------------------------------------

def _load_rand_reports() -> list[dict]:
    """Load RAND reports and chunk into sections."""
    if not RAND_PATH.exists():
        logger.warning("rand_reports.json not found")
        return []

    with open(RAND_PATH, encoding="utf-8") as f:
        reports = json.load(f)

    events = []
    for report in reports:
        title = report.get("title", "")
        content = report.get("content", "")
        url = report.get("url", "")
        if len(content) < 300:
            continue

        # Chunk large reports
        chunks = []
        for i in range(0, len(content), CHUNK_CHARS):
            chunk = content[i:i + CHUNK_CHARS].strip()
            if len(chunk) > 200:
                chunks.append(chunk)

        for idx, chunk in enumerate(chunks):
            slug = re.sub(r"[^a-z0-9]+", "_", title.lower())[:50]
            event_id = f"rand:{slug}:{idx+1:02d}"

            events.append({
                "event_id": event_id,
                "source": "rand_corporation",
                "source_detail": url,
                "name": title if idx == 0 else f"{title} (part {idx+1})",
                "year": None,
                "period": "contemporary",
                "country": "US",
                "event_type": "policy_analysis",
                "location": "",
                "edges": [{
                    "edge_type": "content",
                    "data": {
                        "title": title,
                        "section": idx + 1,
                        "total_sections": len(chunks),
                        "text": chunk,
                        "char_count": len(chunk),
                        "url": url,
                    },
                }],
            })

    logger.info("RAND reports: %d sections from %d reports", len(events), len(reports))
    return events


# ---------------------------------------------------------------------------
# Source 1b: Council on Foreign Relations (CFR) backgrounders
# ---------------------------------------------------------------------------

def _load_cfr_reports() -> list[dict]:
    """Load CFR backgrounder articles and chunk into sections."""
    if not CFR_PATH.exists():
        logger.warning("cfr_reports.json not found")
        return []

    with open(CFR_PATH, encoding="utf-8") as f:
        articles = json.load(f)

    events = []
    for article in articles:
        title = article.get("title", "")
        content = article.get("content", "")
        url = article.get("url", "")
        if len(content) < 300:
            continue

        chunks = []
        for i in range(0, len(content), CHUNK_CHARS):
            chunk = content[i:i + CHUNK_CHARS].strip()
            if len(chunk) > 200:
                chunks.append(chunk)

        for idx, chunk in enumerate(chunks):
            slug = re.sub(r"[^a-z0-9]+", "_", title.lower())[:50]
            event_id = f"cfr:{slug}:{idx+1:02d}"

            events.append({
                "event_id": event_id,
                "source": "cfr",
                "source_detail": url,
                "name": title if idx == 0 else f"{title} (part {idx+1})",
                "year": None,
                "period": "contemporary",
                "country": "",
                "event_type": "geopolitical_analysis",
                "location": "",
                "edges": [{
                    "edge_type": "content",
                    "data": {
                        "title": title,
                        "section": idx + 1,
                        "total_sections": len(chunks),
                        "text": chunk,
                        "char_count": len(chunk),
                        "url": url,
                    },
                }],
            })

    logger.info("CFR articles: %d sections from %d articles", len(events), len(articles))
    return events


# ---------------------------------------------------------------------------
# Source 2: CRS (Congressional Research Service) reports
# ---------------------------------------------------------------------------

def _iter_json_source(path: Path, source_name: str, event_type: str, chunk_size: int = CHUNK_CHARS):
    """Stream events from a pre-fetched JSON collection. Yields one event at a time."""
    if not path.exists():
        return

    import ijson
    count = 0
    items = 0

    with open(path, "rb") as f:
        for item in ijson.items(f, "item"):
            items += 1
            title = item.get("title", "")
            content = item.get("content", "")
            url = item.get("url", "")
            if len(content) < 300:
                continue

            num_chunks = max(1, (len(content) + chunk_size - 1) // chunk_size)

            for idx in range(num_chunks):
                chunk = content[idx * chunk_size:(idx + 1) * chunk_size].strip()
                if len(chunk) < 200:
                    continue

                slug = re.sub(r"[^a-z0-9]+", "_", title.lower())[:50]
                event_id = f"{source_name}:{slug}:{idx+1:02d}"

                count += 1
                yield {
                    "event_id": event_id,
                    "source": source_name,
                    "source_detail": url,
                    "name": title if idx == 0 else f"{title} (part {idx+1})",
                    "year": None,
                    "period": "contemporary" if source_name != "gutenberg" else "historical",
                    "country": "",
                    "event_type": event_type,
                    "location": "",
                    "edges": [{
                        "edge_type": "content",
                        "data": {
                            "title": title,
                            "section": idx + 1,
                            "total_sections": num_chunks,
                            "text": chunk,
                            "char_count": len(chunk),
                        },
                    }],
                }

    logger.info("%s: %d sections from %d items", source_name, count, items)


# ---------------------------------------------------------------------------
# Source 5: Tucker Carlson Show transcripts (events, not lessons)
# ---------------------------------------------------------------------------

def _load_tucker_transcripts() -> list[dict]:
    """Load Tucker Carlson transcripts as event content."""
    if not TUCKER_DIR.exists():
        return []

    events = []
    for txt_path in sorted(TUCKER_DIR.glob("tucker_carlson_*.txt")):
        content = txt_path.read_text(encoding="utf-8").strip()
        if len(content) < 200:
            continue

        fname = txt_path.stem
        m = re.match(r"tucker_carlson_show_episode_(\d+)(?:_(.+))?", fname)
        if not m:
            continue

        ep_num = int(m.group(1))
        topic = (m.group(2) or "").replace("_", " ").strip()

        # Chunk large transcripts
        chunks = []
        for i in range(0, len(content), CHUNK_CHARS):
            chunk = content[i:i + CHUNK_CHARS].strip()
            if len(chunk) > 200:
                chunks.append(chunk)

        for idx, chunk in enumerate(chunks):
            event_id = f"tucker:{ep_num:03d}:{idx+1:02d}"
            events.append({
                "event_id": event_id,
                "source": "tucker_carlson_show",
                "source_detail": f"episode_{ep_num}",
                "name": f"Tucker Carlson Ep {ep_num} - {topic}" if topic else f"Tucker Carlson Ep {ep_num}",
                "year": None,
                "period": "contemporary",
                "country": "US",
                "event_type": "political_commentary",
                "location": "",
                "edges": [{
                    "edge_type": "content",
                    "data": {
                        "episode": ep_num,
                        "section": idx + 1,
                        "text": chunk,
                        "char_count": len(chunk),
                    },
                }],
            })

    logger.info("Tucker Carlson: %d sections", len(events))
    return events


# ---------------------------------------------------------------------------
# Merge and write
# ---------------------------------------------------------------------------

def _write_event(f, event: dict) -> None:
    """Write a single event to the JSONL file with edge counts."""
    edge_counts: dict[str, int] = {}
    for edge in event.get("edges", []):
        edge_counts[edge["edge_type"]] = edge_counts.get(edge["edge_type"], 0) + 1
    event["edge_counts"] = edge_counts
    f.write(json.dumps(event, ensure_ascii=False) + "\n")


def generate() -> Path:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    sources: dict[str, int] = defaultdict(int)
    total_events = 0
    total_chars = 0

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        # Small sources — load in memory (fine)
        for label, loader in [
            ("RAND reports", _load_rand_reports),
            ("CFR articles", _load_cfr_reports),
            ("Tucker Carlson", _load_tucker_transcripts),
        ]:
            logger.info("Loading %s...", label)
            for event in loader():
                _write_event(f, event)
                sources[event["source"]] += 1
                total_events += 1
                for edge in event.get("edges", []):
                    total_chars += edge.get("data", {}).get("char_count", 0)

        # Large sources — stream from disk
        for label, path, src_name, evt_type, chunk in [
            ("CRS reports", CRS_PATH, "crs", "policy_research", CHUNK_CHARS),
            ("Wikipedia articles", WIKI_PATH, "wikipedia", "encyclopedia", CHUNK_CHARS),
            ("Gutenberg books", GUTENBERG_PATH, "gutenberg", "historical_text", BOOK_CHUNK_CHARS),
            ("Brookings reports", BROOKINGS_PATH, "brookings", "policy_analysis", CHUNK_CHARS),
        ]:
            logger.info("Streaming %s...", label)
            for event in _iter_json_source(path, src_name, evt_type, chunk_size=chunk):
                _write_event(f, event)
                sources[event["source"]] += 1
                total_events += 1
                for edge in event.get("edges", []):
                    total_chars += edge.get("data", {}).get("char_count", 0)

    logger.info("=" * 60)
    logger.info("Human history JSONL: %s", OUTPUT_PATH)
    logger.info("  Total events: %d", total_events)
    logger.info("  Total content: %d chars (~%dK tokens)", total_chars, total_chars // 4000)
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        logger.info("    %-30s %8d", src, count)
    logger.info("  File size: %.0f MB", OUTPUT_PATH.stat().st_size / 1024 / 1024)
    logger.info("=" * 60)

    return OUTPUT_PATH


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    generate()


if __name__ == "__main__":
    main()
