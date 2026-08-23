"""Pipeline configuration — externalizes all hardcoded constants.

All index names, default paths, model settings, and surah defaults are
defined here.  CLI scripts override these via argparse; the values here
are the fallback defaults.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from al_furqan.paths import DATA_ARCHIVE as _DATA_DIR


@dataclass
class PipelineConfig:
    """Central configuration for the lesson processing pipeline."""

    # Elasticsearch
    es_url: str = field(
        default_factory=lambda: os.environ.get(
            "ELASTICSEARCH_URL", "http://localhost:9200"
        )
    )
    es_quran_index: str = "furqan_quran"
    es_hadith_index: str = "furqan_hadith"
    es_index_prefix: str = "furqan"

    # Enrichment
    target_surah: int = 6  # Al-Anaam
    verse_match_slop: int = 2
    verse_match_limit: int = 50
    hadith_match_limit: int = 20

    # Transcription (Whisper)
    whisper_model: str = "large-v3"
    whisper_device: str = field(
        default_factory=lambda: "cuda" if _cuda_available() else "cpu"
    )
    whisper_compute_type: str = "int8"

    # Paths (data dir)
    data_dir: Path = _DATA_DIR
    lessons_dir: Path = field(default_factory=lambda: _DATA_DIR / "lessons")

    @property
    def lessons_input_dir(self) -> Path:
        return self.lessons_dir / "lessons_youtube_txt"

    @property
    def lessons_clean_dir(self) -> Path:
        return self.lessons_dir / "lessons_clean_json"

    @property
    def lessons_enriched_dir(self) -> Path:
        return self.lessons_dir / "lessons_enriched_json"

    @property
    def lessons_mp3_dir(self) -> Path:
        return self.lessons_dir / "lessons_mp3"

    @property
    def training_dir(self) -> Path:
        return self.lessons_dir / "training_pairs"


def _cuda_available() -> bool:
    """Check if CUDA is available without importing torch."""
    try:
        import torch  # pylint: disable=import-outside-toplevel

        return torch.cuda.is_available()
    except ImportError:
        return False
