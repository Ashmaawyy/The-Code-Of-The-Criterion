"""Clean YouTube transcript txt files and convert to structured JSON.

Strips timestamps, merges content into paragraphs, and structures by chapters.

Usage:
    python -m al_furqan.lessons.clean_transcripts                     # default
    python -m al_furqan.lessons.clean_transcripts --input DIR --output DIR
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path

from al_furqan.lessons.text_utils import (
    CHAPTER_PATTERN,
    is_blank,
    is_timestamp,
    to_arabic_ordinal,
)

logger = logging.getLogger(__name__)


def parse_txt_file(filepath: Path) -> dict:
    """Parse a transcript txt file into structured data."""
    with open(filepath, encoding="utf-8") as f:
        raw_lines = f.readlines()

    chapters = []
    current_chapter_title = "مقدمة"
    current_chapter_num = 1
    content_lines = []
    has_explicit_chapters = False

    for line in raw_lines:
        line = line.strip()

        # Check for chapter marker
        m = CHAPTER_PATTERN.match(line)
        if m:
            has_explicit_chapters = True
            # Save previous chapter
            if content_lines:
                text = merge_content_lines(content_lines)
                if text:
                    chapters.append(
                        {
                            "chapter_number": current_chapter_num,
                            "title": current_chapter_title,
                            "content": text,
                        }
                    )

            current_chapter_num = int(m.group(1))
            current_chapter_title = m.group(2).strip()
            content_lines = []
            continue

        # Skip blank lines and timestamps
        if is_blank(line) or is_timestamp(line):
            continue

        # It's content
        if line:
            content_lines.append(line)

    # Save last chapter
    if content_lines:
        text = merge_content_lines(content_lines)
        if text:
            chapters.append(
                {
                    "chapter_number": current_chapter_num,
                    "title": current_chapter_title,
                    "content": text,
                }
            )

    # If no explicit chapters and only one block, mark it
    if not has_explicit_chapters and len(chapters) == 1:
        chapters[0]["chapter_number"] = 1
        chapters[0]["title"] = "مقدمة"

    return {"has_explicit_chapters": has_explicit_chapters, "chapters": chapters}


def merge_content_lines(lines: list[str]) -> str:
    """Merge transcript lines into coherent paragraphs."""
    if not lines:
        return ""
    # Join all lines with space (they're fragments of continuous speech)
    text = " ".join(lines)
    # Clean up multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_line_mapping(filepath: Path) -> dict:
    """Build a mapping from original file line numbers (1-indexed) to
    content-line indices (0-indexed), skipping timestamp lines."""
    with open(filepath, encoding="utf-8") as f:
        raw_lines = f.readlines()

    mapping = {}  # orig_line_num -> content_line_idx
    content_idx = 0
    for i, line in enumerate(raw_lines):
        orig_line_num = i + 1  # 1-indexed
        stripped = line.strip()
        if (
            is_blank(stripped)
            or is_timestamp(stripped)
            or CHAPTER_PATTERN.match(stripped)
        ):
            continue
        mapping[orig_line_num] = content_idx
        content_idx += 1
    return mapping


def find_nearest_content_idx(
    orig_line: int, line_map: dict, max_search: int = 30
) -> int:
    """Find the content-line index closest to the given original line number.

    Args:
        orig_line: 1-indexed line number in the original file.
        line_map: mapping of original line numbers to content-line indices.
        max_search: how many lines forward/backward to probe before falling
                    back to a sorted scan.  The default of 30 handles transcripts
                    where several consecutive timestamp lines separate content.

    Returns:
        0 if *line_map* is empty (empty input file).
    """
    if not line_map:
        return 0
    if orig_line in line_map:
        return line_map[orig_line]
    # Search nearby lines (the marker might point to a timestamp line)
    for offset in range(1, max_search + 1):
        if orig_line + offset in line_map:
            return line_map[orig_line + offset]
        if orig_line - offset in line_map:
            return line_map[orig_line - offset]
    # Fallback: return closest available
    keys = sorted(line_map.keys())
    for k in keys:
        if k >= orig_line:
            return line_map[k]
    return line_map[keys[-1]]


def inject_chapters(
    chapter_markers: list[dict], all_content_lines: list[str], filepath: Path
) -> dict:
    """Re-structure a chapter-less file using provided chapter markers.

    chapter_markers: list of {"line": int, "title": str} where line is 1-indexed
                     into the ORIGINAL file (with timestamps).
    all_content_lines: the cleaned content lines (no timestamps).
    filepath: path to original file for building line mapping.
    """
    line_map = build_line_mapping(filepath)
    chapters = []
    # Sort markers by line number
    markers = sorted(chapter_markers, key=lambda x: x["line"])

    for i, marker in enumerate(markers):
        start_idx = find_nearest_content_idx(marker["line"], line_map)
        if i + 1 < len(markers):
            end_idx = find_nearest_content_idx(markers[i + 1]["line"], line_map)
        else:
            end_idx = len(all_content_lines)

        chunk = all_content_lines[start_idx:end_idx]
        text = merge_content_lines(chunk)
        if text:
            chapters.append(
                {"chapter_number": i + 1, "title": marker["title"], "content": text}
            )

    return {"has_explicit_chapters": True, "chapters": chapters}


def extract_content_lines(filepath: Path) -> list[str]:
    """Extract only content lines (no timestamps, no chapter markers) from a file."""
    with open(filepath, encoding="utf-8") as f:
        raw_lines = f.readlines()

    content = []
    for line in raw_lines:
        line = line.strip()
        if is_blank(line) or is_timestamp(line):
            continue
        if CHAPTER_PATTERN.match(line):
            continue
        if line:
            content.append(line)
    return content


def get_lesson_number(filename: str) -> int:
    """Extract lesson number from filename like 'lesson_01_Anaam.txt'.

    Case-insensitive: handles 'Lesson_01', 'LESSON_01', 'lesson_01'.
    """
    m = re.search(r"lesson[_-]?(\d+)", filename, re.IGNORECASE)
    return int(m.group(1)) if m else 0


def build_json(lesson_num: int, chapters: list[dict]) -> dict:
    """Build the final JSON structure for a lesson."""
    return {
        "lesson_number": lesson_num,
        "surah": "الأنعام",
        "title": f"مدارسة سورة الأنعام - المجلس {to_arabic_ordinal(lesson_num)}",
        "total_chapters": len(chapters),
        "chapters": chapters,
    }


def process_all(lessons_dir: Path, output_dir: Path, chapters_map: dict = None):
    """Process all txt files.

    Args:
        lessons_dir: directory containing lesson_*_Anaam.txt files.
        output_dir: directory to write clean JSON files to.
        chapters_map: dict mapping lesson numbers (int) to list of
                      {"line": int, "title": str} chapter markers
                      for files that don't have built-in chapters.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    txt_files = sorted(lessons_dir.glob("lesson_*_Anaam.txt"))
    if not txt_files:
        logger.warning("No lesson files found in %s", lessons_dir)
        return

    for txt_file in txt_files:
        lesson_num = get_lesson_number(txt_file.name)
        logger.info("Processing lesson %02d...", lesson_num)

        try:
            parsed = parse_txt_file(txt_file)
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Failed to read %s: %s", txt_file.name, exc)
            continue

        if (
            not parsed["has_explicit_chapters"]
            and chapters_map
            and lesson_num in chapters_map
        ):
            # Use provided chapter markers
            content_lines = extract_content_lines(txt_file)
            markers = chapters_map[lesson_num]
            parsed = inject_chapters(markers, content_lines, txt_file)
            logger.info(
                "Injected %d chapters from provided data", len(parsed["chapters"])
            )
        elif parsed["has_explicit_chapters"]:
            logger.info("Found %d existing chapters", len(parsed["chapters"]))
        else:
            logger.warning("No chapters found and no chapter data provided")

        result = build_json(lesson_num, parsed["chapters"])

        out_path = output_dir / f"lesson_{lesson_num:02d}_Anaam.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        total_words = sum(len(ch["content"].split()) for ch in result["chapters"])
        logger.info(
            "%d chapters, ~%d words -> %s",
            len(result["chapters"]),
            total_words,
            out_path.name,
        )

    logger.info("Done! Output in %s", output_dir)


def main():
    """CLI entry point."""
    from al_furqan.lessons.config import PipelineConfig
    from al_furqan.lessons.logging_config import setup_logging

    setup_logging()

    cfg = PipelineConfig()

    parser = argparse.ArgumentParser(
        description="Clean YouTube transcript txt files and convert to structured JSON."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=cfg.lessons_input_dir,
        help="Directory containing lesson txt files",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=cfg.lessons_clean_dir,
        help="Directory to write clean JSON files to",
    )
    parser.add_argument(
        "--chapters",
        type=Path,
        default=cfg.lessons_dir / "chapter_data.json",
        help="Path to chapter_data.json",
    )
    args = parser.parse_args()

    chapter_data = None
    if args.chapters.exists():
        try:
            with open(args.chapters, encoding="utf-8") as file:
                raw = json.load(file)
            chapter_data = {int(k): v for k, v in raw.items()}
            logger.info("Loaded chapter data for %d lessons", len(chapter_data))
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            logger.error("Failed to load chapter data from %s: %s", args.chapters, exc)
            sys.exit(1)

    process_all(args.input, args.output, chapters_map=chapter_data)


if __name__ == "__main__":
    main()
