"""Tests for the transcript chunker."""

import json
import os
import pytest

from al_furqan.kb.ingestion.transcript_chunker import (
    chunk_transcript,
    chunk_segments,
    format_chunk_timestamp,
    TranscriptChunk,
)


def _make_segments(n_segments, words_per_segment=10):
    """Helper to create test segments."""
    segments = []
    for i in range(n_segments):
        words = " ".join(f"word{i}_{j}" for j in range(words_per_segment))
        segments.append({
            "start": float(i * 2),
            "end": float(i * 2 + 2),
            "text": words,
        })
    return segments


def _write_transcript(segments, tmpdir):
    """Write a transcript JSON file and return path."""
    path = os.path.join(tmpdir, "transcript.json")
    data = {
        "text": " ".join(s["text"] for s in segments),
        "segments": segments,
        "language": "ar",
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


class TestChunkSegments:
    """Test chunk_segments function."""

    def test_basic_chunking(self):
        """Segments are split into chunks of ~chunk_size words."""
        segments = _make_segments(10, words_per_segment=10)  # 100 words total
        chunks = chunk_segments(segments, chunk_size=50, overlap=0)
        assert len(chunks) == 2
        assert chunks[0].word_count == 50
        assert chunks[1].word_count == 50

    def test_overlap(self):
        """Chunks overlap by the specified number of words."""
        segments = _make_segments(10, words_per_segment=10)  # 100 words
        chunks = chunk_segments(segments, chunk_size=50, overlap=10)
        # With step=40, chunks: [0:50], [40:90], [80:100]
        assert len(chunks) == 3
        assert chunks[0].word_count == 50
        assert chunks[1].word_count == 50
        assert chunks[2].word_count == 20  # remaining

    def test_chunk_index_sequential(self):
        """Chunk indices are sequential starting from 0."""
        segments = _make_segments(5, words_per_segment=10)
        chunks = chunk_segments(segments, chunk_size=20, overlap=0)
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    def test_timing(self):
        """Chunks have correct start and end times."""
        segments = _make_segments(4, words_per_segment=10)
        chunks = chunk_segments(segments, chunk_size=20, overlap=0)
        assert chunks[0].start_time == 0.0
        assert chunks[0].end_time == 4.0  # segments 0,1
        assert chunks[1].start_time == 4.0
        assert chunks[1].end_time == 8.0  # segments 2,3

    def test_segment_indices(self):
        """Each chunk tracks which segments it spans."""
        segments = _make_segments(4, words_per_segment=5)
        chunks = chunk_segments(segments, chunk_size=10, overlap=0)
        assert chunks[0].segment_indices == [0, 1]
        assert chunks[1].segment_indices == [2, 3]

    def test_empty_segments(self):
        """Empty segment list returns empty chunks."""
        chunks = chunk_segments([], chunk_size=50, overlap=10)
        assert not chunks

    def test_single_segment(self):
        """A single segment produces one chunk."""
        segments = [{"start": 0.0, "end": 5.0, "text": "hello world"}]
        chunks = chunk_segments(segments, chunk_size=500, overlap=50)
        assert len(chunks) == 1
        assert chunks[0].word_count == 2

    def test_invalid_params(self):
        """Invalid parameters raise ValueError."""
        segments = _make_segments(2)
        with pytest.raises(ValueError):
            chunk_segments(segments, chunk_size=0)
        with pytest.raises(ValueError):
            chunk_segments(segments, chunk_size=10, overlap=-1)
        with pytest.raises(ValueError):
            chunk_segments(segments, chunk_size=10, overlap=10)


class TestChunkTranscript:
    """Test chunk_transcript loading from file."""

    def test_load_and_chunk(self, tmp_path):
        """Load a transcript JSON and chunk it."""
        segments = _make_segments(5, words_per_segment=10)
        path = _write_transcript(segments, str(tmp_path))
        chunks = chunk_transcript(path, chunk_size=25, overlap=5)
        assert len(chunks) >= 2
        total_words = sum(c.word_count for c in chunks)
        # With overlap, total words counted > actual words
        assert total_words >= 50

    def test_real_transcript(self):
        """Test with the actual lesson 01 transcript if available."""
        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data/lessons/lesson_01_transcript.json",
        )
        if not os.path.exists(path):
            pytest.skip("Transcript not available")
        chunks = chunk_transcript(path, chunk_size=500, overlap=50)
        assert len(chunks) > 5  # Should produce many chunks
        for chunk in chunks:
            assert chunk.word_count > 0
            assert chunk.start_time >= 0
            assert chunk.end_time > chunk.start_time


class TestFormatTimestamp:
    """Test timestamp formatting."""

    def test_format(self):
        """Test format."""
        chunk = TranscriptChunk(
            chunk_index=0, text="test", start_time=65.0, end_time=130.0,
            segment_indices=[0], word_count=1,
        )
        assert format_chunk_timestamp(chunk) == "01:05 - 02:10"

    def test_format_zero(self):
        """Test format_zero."""
        chunk = TranscriptChunk(
            chunk_index=0, text="test", start_time=0.0, end_time=59.0,
            segment_indices=[0], word_count=1,
        )
        assert format_chunk_timestamp(chunk) == "00:00 - 00:59"
