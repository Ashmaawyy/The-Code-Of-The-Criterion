"""
Transcript Chunker for Al-Furqan Knowledge Graph Pipeline.

Splits Whisper transcript JSON into overlapping chunks suitable
for LLM-based relationship extraction.
"""

import json
from dataclasses import dataclass


@dataclass
class TranscriptChunk:
    """A chunk of transcript text with timing metadata."""

    chunk_index: int
    text: str
    start_time: float
    end_time: float
    segment_indices: list[int]
    word_count: int


def _format_time(seconds: float) -> str:
    """Convert seconds to MM:SS format."""
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{minutes:02d}:{secs:02d}"


def chunk_transcript(
    transcript_path: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[TranscriptChunk]:
    """
    Load a Whisper transcript JSON and split into overlapping chunks.

    Args:
        transcript_path: Path to the Whisper transcript JSON file.
        chunk_size: Target number of words per chunk (~500).
        overlap: Number of overlapping words between consecutive chunks (~50).

    Returns:
        List of TranscriptChunk objects.
    """
    with open(transcript_path, encoding="utf-8") as f:
        data = json.load(f)

    segments = data.get("segments", [])
    if not segments:
        return []

    return chunk_segments(segments, chunk_size=chunk_size, overlap=overlap)


def chunk_segments(  # pylint: disable=too-many-locals
    segments: list[dict],
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[TranscriptChunk]:
    """
    Split segments into overlapping chunks of approximately `chunk_size` words.

    Each segment has: {"start": float, "end": float, "text": str}

    The overlap is achieved by including trailing segments from the previous
    chunk at the beginning of the next chunk.
    """
    if not segments:
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap must be non-negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be less than chunk_size")

    # Build a flat list of (word, segment_index) pairs
    word_entries: list[tuple] = []  # (word, segment_idx)
    for seg_idx, seg in enumerate(segments):
        text = seg.get("text", "").strip()
        if not text:
            continue
        for word in text.split():
            word_entries.append((word, seg_idx))

    if not word_entries:
        return []

    total_words = len(word_entries)
    step = chunk_size - overlap
    chunks: list[TranscriptChunk] = []
    chunk_idx = 0
    start_word = 0

    while start_word < total_words:
        end_word = min(start_word + chunk_size, total_words)
        chunk_words = word_entries[start_word:end_word]

        # Gather segment indices in this chunk
        seg_indices_set = []
        seen = set()
        for _, si in chunk_words:
            if si not in seen:
                seen.add(si)
                seg_indices_set.append(si)

        # Timing from segments
        first_seg_idx = chunk_words[0][1]
        last_seg_idx = chunk_words[-1][1]
        start_time = segments[first_seg_idx]["start"]
        end_time = segments[last_seg_idx]["end"]

        text = " ".join(w for w, _ in chunk_words)

        chunks.append(
            TranscriptChunk(
                chunk_index=chunk_idx,
                text=text,
                start_time=start_time,
                end_time=end_time,
                segment_indices=seg_indices_set,
                word_count=len(chunk_words),
            )
        )

        chunk_idx += 1
        start_word += step

        # If we've consumed everything, stop
        if end_word >= total_words:
            break

    return chunks


def format_chunk_timestamp(chunk: TranscriptChunk) -> str:
    """Format a chunk's time range as MM:SS - MM:SS."""
    return f"{_format_time(chunk.start_time)} - {_format_time(chunk.end_time)}"
