"""Lesson transcriber — converts audio to JSON via Whisper.

Auto-detects CUDA availability. Falls back to CPU with int8 quantization.

Usage:
    python -m al_furqan.lessons.transcriber input.mp3
    python -m al_furqan.lessons.transcriber input.mp3 -o output.json
    python -m al_furqan.lessons.transcriber input.mp3 --device cuda
"""

import argparse
import json
import logging
from pathlib import Path

from al_furqan.lessons.config import PipelineConfig

logger = logging.getLogger(__name__)


class LessonTranscriber:
    """Transcribes audio lessons into structured JSON format using Whisper."""

    def __init__(self, config: PipelineConfig | None = None) -> None:
        if config is None:
            config = PipelineConfig()

        from faster_whisper import WhisperModel  # pylint: disable=import-outside-toplevel
        self.model = WhisperModel(
            model_size_or_path=config.whisper_model,
            compute_type=config.whisper_compute_type,
            device=config.whisper_device,
        )
        logger.info("Whisper model loaded: %s on %s (%s)",
                     config.whisper_model, config.whisper_device,
                     config.whisper_compute_type)

    def transcribe(self, audio_path: str) -> dict:
        """Transcribe the given audio file and return a structured transcript."""
        segments, info = self.model.transcribe(
            audio_path, language="ar", vad_filter=True, beam_size=5
        )
        transcript = {"segments": []}
        for segment in segments:
            transcript["segments"].append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text,
                "tokens": segment.tokens,
                "language": info.language,
            })
        return transcript

    def save_transcript(self, transcript: dict, output_path: str) -> None:
        """Save the transcript to a JSON file."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(transcript, f, ensure_ascii=False, indent=4)


def main():
    """CLI entry point."""
    from al_furqan.lessons.logging_config import setup_logging
    setup_logging()

    cfg = PipelineConfig()

    parser = argparse.ArgumentParser(description="Transcribe an audio lesson to JSON.")
    parser.add_argument("input", help="Path to the input audio file")
    parser.add_argument("-o", "--output", default=None,
                        help="Output JSON path (default: derived from input)")
    parser.add_argument("--model", default=cfg.whisper_model)
    parser.add_argument("--device", default=cfg.whisper_device,
                        choices=["cpu", "cuda"])
    parser.add_argument("--compute-type", default=cfg.whisper_compute_type)
    args = parser.parse_args()

    cfg.whisper_model = args.model
    cfg.whisper_device = args.device
    cfg.whisper_compute_type = args.compute_type

    output = args.output
    if output is None:
        stem = Path(args.input).stem
        output = str(cfg.lessons_dir / "lessons_json" / f"{stem}_transcript.json")

    transcriber = LessonTranscriber(config=cfg)
    result = transcriber.transcribe(args.input)
    transcriber.save_transcript(result, output)
    logger.info("Transcript saved to %s", output)


if __name__ == "__main__":
    main()
