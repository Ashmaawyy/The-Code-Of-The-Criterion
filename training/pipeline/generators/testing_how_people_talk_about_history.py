"""Build the 'how people talk about history' testing JSONL from multiple
long-form interview shows — one event per episode, no chaptering.

Sources:
  data_archive/human_history/youtube_txt/test_how_people_talk_about_history/
    the_tucker_carlson_show_chaptered/*.txt    → source: the_tucker_carlson_show
    pierce_morgan_show_chaptered/*.txt         → source: piers_morgan_show

Output: data_archive/training/testing/model_testing_how_people_talk_about_history.jsonl

Each transcript file is one episode and produces exactly one event document.
Any ``Chapter N: <title>`` headers present in the source (e.g. from the 4
Tucker files that had creator chapters, or from Piers Morgan fetches that
captured YouTube chapter markers) are stripped and the prose is concatenated
into a single continuous text field — fine-tuning evals for this set want
full-episode context, not pre-chunked slices.

Event shape (one line of JSONL, one event per episode):

    {
      "event_id": "tucker:<episode_slug>",
      "source": "the_tucker_carlson_show",
      "source_detail": "<episode filename stem>",
      "name": "<episode title>",
      "year": null,
      "period": "contemporary",
      "country": "US",
      "event_type": "political_commentary",
      "location": "",
      "edges": [{
        "edge_type": "content",
        "data": {
          "title": "<episode title>",
          "text": "<full transcript prose>",
          "char_count": ...,
          "episode_slug": "<slug>"
        }
      }],
      "edge_counts": {"content": 1}
    }

Usage:
    python -m training.pipeline.generators.testing_how_people_talk_about_history
    python -m training.pipeline.generators.testing_how_people_talk_about_history --dry-run
"""
from __future__ import annotations

import argparse
import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

from al_furqan.paths import (
    DATA_HUMAN_HISTORY,
    TESTING_TALK_ABOUT_HISTORY_JSONL as OUTPUT_PATH,
)

_BASE = (
    DATA_HUMAN_HISTORY / "youtube_txt" / "test_how_people_talk_about_history"
)

# (source_dir, source_name, event_id_prefix) — one entry per show.
SHOWS: list[tuple[Path, str, str]] = [
    (_BASE / "the_tucker_carlson_show_chaptered", "the_tucker_carlson_show", "tucker"),
    (_BASE / "pierce_morgan_show_chaptered",      "piers_morgan_show",       "piers"),
]

EVENT_TYPE = "political_commentary"

# Matches "Chapter 12: What Is Pizzagate?" — stripped out when flattening.
_CHAPTER_HEADER_RE = re.compile(r"^\s*Chapter\s+\d+:.*$")

MIN_CHAR_COUNT = 200


def _slugify(text: str, maxlen: int = 50) -> str:
    """Lowercase slug — mirrors the pattern used in human_history.py."""
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:maxlen]


def _flatten_transcript(raw: str) -> str:
    """Strip chapter headers and collapse all prose to one continuous block."""
    kept_lines: list[str] = []
    for line in raw.splitlines():
        if _CHAPTER_HEADER_RE.match(line):
            continue
        stripped = line.strip()
        if stripped:
            kept_lines.append(stripped)
    return re.sub(r"\s+", " ", " ".join(kept_lines)).strip()


def _build_event(txt_path: Path, source_name: str, id_prefix: str) -> dict | None:
    raw = txt_path.read_text(encoding="utf-8", errors="replace")
    text = _flatten_transcript(raw)
    if len(text) < MIN_CHAR_COUNT:
        return None

    episode_name = txt_path.stem.strip()
    episode_slug = _slugify(episode_name)
    event_id = f"{id_prefix}:{episode_slug}"

    return {
        "event_id": event_id,
        "source": source_name,
        "source_detail": txt_path.stem,
        "name": episode_name,
        "year": None,
        "period": "contemporary",
        "country": "US",
        "event_type": EVENT_TYPE,
        "location": "",
        "edges": [{
            "edge_type": "content",
            "data": {
                "title": episode_name,
                "text": text,
                "char_count": len(text),
                "episode_slug": episode_slug,
            },
        }],
        "edge_counts": {"content": 1},
    }


def generate(
    shows: list[tuple[Path, str, str]] = None,
    output_path: Path = OUTPUT_PATH,
    dry_run: bool = False,
) -> dict:
    if shows is None:
        shows = SHOWS

    output_path.parent.mkdir(parents=True, exist_ok=True)

    stats: dict = {
        "episodes": 0,
        "skipped_empty": 0,
        "total_chars": 0,
        "by_source": {},
    }

    out_f = None if dry_run else output_path.open("w", encoding="utf-8")
    try:
        for source_dir, source_name, id_prefix in shows:
            if not source_dir.exists():
                logger.warning("skipping missing source: %s", source_dir)
                continue

            source_count = 0
            for txt_path in sorted(source_dir.glob("*.txt")):
                event = _build_event(txt_path, source_name, id_prefix)
                if event is None:
                    stats["skipped_empty"] += 1
                    continue

                stats["episodes"] += 1
                source_count += 1
                stats["total_chars"] += event["edges"][0]["data"]["char_count"]

                if out_f is not None:
                    out_f.write(json.dumps(event, ensure_ascii=False) + "\n")

            stats["by_source"][source_name] = source_count
    finally:
        if out_f is not None:
            out_f.close()

    logger.info("=" * 60)
    logger.info("output: %s", output_path if not dry_run else "(dry run)")
    logger.info("  %-16s %d", "episodes", stats["episodes"])
    logger.info("  %-16s %d", "skipped_empty", stats["skipped_empty"])
    logger.info("  %-16s %d", "total_chars", stats["total_chars"])
    for src, count in stats["by_source"].items():
        logger.info("  %-16s %d", src, count)
    if not dry_run and output_path.exists():
        logger.info("  %-16s %.2f MB", "file_size", output_path.stat().st_size / 1024 / 1024)
    logger.info("=" * 60)

    return stats


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(
        description="Build testing JSONL from long-form interview transcripts (one event per episode)")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--dry-run", action="store_true",
                        help="Count events without writing the JSONL")
    args = parser.parse_args()

    generate(output_path=args.output, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
