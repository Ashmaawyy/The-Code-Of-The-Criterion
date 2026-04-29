#!/usr/bin/env python3
"""Render Mermaid diagrams in the Architecture v3.0 doc to PNG files.

Replaces ``` ```mermaid ``` ``` code blocks in the markdown with image
references to the rendered PNGs. Destructive: rewrites the source .md in
place, so commit first if you care about the diff.
"""

import logging
import os
import re
import subprocess
import tempfile
from pathlib import Path

from al_furqan import setup_logging

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DOC_PATH = PROJECT_ROOT / "docs" / "active_docs" / "AL-FURQAN-ARCHITECTURE-v3.0.md"
IMG_DIR = PROJECT_ROOT / "docs" / "active_docs" / "images-v3"
IMG_REL_PREFIX = "images-v3"  # path used inside the markdown file (relative to the doc)

MERMAID_PATTERN = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)


def render_one(mermaid_code: str, img_path: Path) -> bool:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as tmp:
        tmp.write(mermaid_code)
        tmp_path = tmp.name
    try:
        result = subprocess.run(  # pylint: disable=subprocess-run-check
            ["mmdc", "-i", tmp_path, "-o", str(img_path), "-b", "white", "-w", "1200",
             "-p", "/dev/stdin"],
            input='{"puppeteerConfig": {"args": ["--no-sandbox", "--disable-setuid-sandbox"]}}',
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return True
        logger.error("  mmdc failed: %s", result.stderr[:100])
        return False
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("  mmdc error: %s", e)
        return False
    finally:
        os.unlink(tmp_path)


def main() -> None:
    setup_logging()

    if not DOC_PATH.exists():
        logger.error("Doc not found: %s", DOC_PATH)
        raise SystemExit(1)

    IMG_DIR.mkdir(parents=True, exist_ok=True)
    content = DOC_PATH.read_text(encoding="utf-8")

    matches = list(MERMAID_PATTERN.finditer(content))
    logger.info("Found %d mermaid diagrams in %s", len(matches), DOC_PATH.name)
    if not matches:
        return

    rendered: dict[int, bool] = {}
    for i, match in enumerate(matches, start=1):
        img_name = f"diagram-{i:02d}.png"
        img_path = IMG_DIR / img_name
        if render_one(match.group(1).strip(), img_path):
            logger.info("  Diagram %d: %s", i, img_name)
            rendered[i] = True
        else:
            logger.error("  Diagram %d: render failed", i)
            rendered[i] = False

    counter = {"i": 0}

    def replace_mermaid(m: re.Match) -> str:
        counter["i"] += 1
        idx = counter["i"]
        if rendered.get(idx):
            return f"![Diagram {idx}]({IMG_REL_PREFIX}/diagram-{idx:02d}.png)"
        return m.group(0)

    content_replaced = MERMAID_PATTERN.sub(replace_mermaid, content)
    DOC_PATH.write_text(content_replaced, encoding="utf-8")

    logger.info("Done! %d diagrams processed.", len(matches))
    logger.info("Images saved to: %s", IMG_DIR)


if __name__ == "__main__":
    main()
