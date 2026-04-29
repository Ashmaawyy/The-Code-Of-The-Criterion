"""Extract ayah→lesson edges from enriched lesson JSON files."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from al_furqan.paths import LESSONS_ENRICHED_DIR as LESSONS_DIR
from training.pipeline.extractors.types import ExtractorResult, add_edge

logger = logging.getLogger(__name__)


def extract(**kwargs) -> ExtractorResult:
    result: ExtractorResult = {}

    if not LESSONS_DIR.exists():
        logger.warning("Lessons directory not found: %s", LESSONS_DIR)
        return result

    count = 0
    for lesson_path in sorted(LESSONS_DIR.glob("lesson_*_Anaam.json")):
        try:
            with open(lesson_path, encoding="utf-8") as f:
                lesson = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        lesson_num = lesson.get("lesson_number", 0)
        lesson_title = lesson.get("title", "")
        lesson_surah = lesson.get("surah", "")

        for ch in lesson.get("chapters", []):
            ch_num = ch.get("chapter_number", 0)
            ch_title = ch.get("title", "")
            ch_content = ch.get("content", "")

            for tv in ch.get("taught_verses", []):
                vk = tv.get("verse_key", "")
                if not vk:
                    continue

                add_edge(result, vk, {
                    "edge_type": "lesson",
                    "target_id": f"lesson:{lesson_num:02d}:ch{ch_num}",
                    "weight": 1.0,
                    "confidence": 1.0,
                    "provenance": f"lesson:{lesson_path.stem}",
                    "data": {
                        "lesson_number": lesson_num,
                        "lesson_title": lesson_title,
                        "surah": lesson_surah,
                        "chapter_number": ch_num,
                        "chapter_title": ch_title,
                        "teacher_text": ch_content,
                    },
                })
                count += 1

    logger.info("lesson: %d edges across %d verses", count, len(result))
    return result
