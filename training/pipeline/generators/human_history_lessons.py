"""Build structured human history lessons JSONL from YouTube transcripts.

Explanatory lessons about key human life events — structured teaching
content, separate from the abstract event data in human_history.jsonl.

Atom structure: lesson_name, episode, chapter, content

Sources:
  - 100 Questions About History (Arabic) — 62 episodes

Output: data_archive/training/human_lessons.jsonl

Usage:
    python -m training.pipeline.generators.human_lessons
"""

from __future__ import annotations

import json
import logging
import re
from collections import defaultdict

from al_furqan.paths import DATA_HUMAN_HISTORY, HUMAN_LESSONS_JSONL as OUTPUT_PATH

logger = logging.getLogger(__name__)

LESSONS_DIR = DATA_HUMAN_HISTORY / "youtube_txt"

# Timestamp patterns to strip
_TIMESTAMP_PATTERNS = [
    re.compile(r"^\d+:\d{2}:\d{2}$", re.MULTILINE),          # 1:23:45
    re.compile(r"^\d+:\d{2}$", re.MULTILINE),                  # 0:09
    re.compile(r"^\d+\s+seconds?$", re.MULTILINE),              # 9 seconds
    re.compile(r"^\d+\s+minutes?,?\s*\d*\s*seconds?$", re.MULTILINE),  # 1 minute, 10 seconds
    re.compile(r"^\d+\s+hours?,?\s*\d*\s*minutes?", re.MULTILINE),
    re.compile(r"^\[.*?\]$", re.MULTILINE),                     # [موسيقى] etc
]


def _clean_transcript(text: str) -> str:
    """Remove timestamps, duration markers, and music tags from transcript."""
    for pat in _TIMESTAMP_PATTERNS:
        text = pat.sub("", text)
    # Collapse multiple blank lines
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    # Remove leading/trailing whitespace per line
    lines = [l.strip() for l in text.split("\n")]
    # Remove empty lines and rejoin
    lines = [l for l in lines if l]
    return "\n".join(lines)


def _load_lessons() -> list[dict]:
    """Load lesson transcripts, strip timestamps, split by chapters."""
    if not LESSONS_DIR.exists():
        logger.warning("Lessons directory not found: %s", LESSONS_DIR)
        return []

    events = []

    for txt_path in sorted(LESSONS_DIR.glob("lesson_*.txt")):
        raw = txt_path.read_text(encoding="utf-8").strip()
        if len(raw) < 100:
            continue

        # Parse filename
        m = re.match(r"lesson_(\d+)_(.+)\.txt", txt_path.name)
        if not m:
            continue

        episode = int(m.group(1))
        lesson_name = m.group(2).replace("_", " ")

        # Clean timestamps
        content = _clean_transcript(raw)

        # Split into chapters
        chapter_re = re.compile(r"^Chapter\s+(\d+)\s*:\s*(.*)$", re.MULTILINE)
        splits = chapter_re.split(content)

        if len(splits) > 3:
            # Has chapters
            # splits[0] = text before first chapter (intro)
            intro = splits[0].strip()
            if len(intro) > 100:
                events.append({
                    "lesson_name": lesson_name,
                    "episode": episode,
                    "chapter": 0,
                    "chapter_title": "intro",
                    "content": intro,
                    "content_length": len(intro),
                })

            i = 1
            while i < len(splits) - 1:
                ch_num = int(splits[i])
                ch_title = splits[i + 1].strip()
                ch_text = _clean_transcript(splits[i + 2].strip()) if i + 2 < len(splits) else ""
                i += 3

                if len(ch_text) < 50:
                    continue

                events.append({
                    "lesson_name": lesson_name,
                    "episode": episode,
                    "chapter": ch_num,
                    "chapter_title": ch_title,
                    "content": ch_text,
                    "content_length": len(ch_text),
                })
        else:
            # No chapters — single block
            events.append({
                "lesson_name": lesson_name,
                "episode": episode,
                "chapter": 1,
                "chapter_title": "",
                "content": content,
                "content_length": len(content),
            })

    return events


def generate() -> Path:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    events = _load_lessons()

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    total_chars = sum(e["content_length"] for e in events)
    episodes = len(set(e["episode"] for e in events))

    logger.info("=" * 60)
    logger.info("Human lessons JSONL: %s", OUTPUT_PATH)
    logger.info("  Episodes: %d, Sections: %d", episodes, len(events))
    logger.info("  Total content: %d chars (~%dK tokens)", total_chars, total_chars // 4000)

    series = defaultdict(int)
    for e in events:
        series[e["lesson_name"]] += 1
    for name, count in series.items():
        logger.info("    %-40s %4d sections", name, count)
    logger.info("=" * 60)

    return OUTPUT_PATH


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    generate()


if __name__ == "__main__":
    main()
