"""Tests for Tafsir Feedback system."""

# pylint: disable=redefined-outer-name

import os
import shutil
import tempfile

import pytest

from al_furqan.engine.tafsir.feedback import (
    TafsirFeedback,
    TafsirFeedbackStore,
)
from al_furqan.engine.tafsir.pipeline import TafsirPipeline

DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "review", "proposed_edges.db"
)


@pytest.fixture
def temp_store():
    """Execute temp_store."""
    tmpdir = tempfile.mkdtemp()
    store = TafsirFeedbackStore(storage_dir=tmpdir)
    yield store
    shutil.rmtree(tmpdir)


@pytest.fixture
def sample_feedback():
    """Execute sample_feedback."""
    return TafsirFeedback(
        question="إيه علاقة أول أربع آيات بالآية 5؟",
        query_type="verse_link",
        verse_refs=["6:1", "6:2", "6:3", "6:4", "6:5"],
        template_name="ربط بين آيات",
        llm_response="العلاقة هي مقدمة ونتيجة...",
        reviewer="muhammad",
        verdict="correct",
    )


class TestFeedbackStore:
    """TestFeedbackStore class."""

    def test_store_correct(self, temp_store, sample_feedback):
        """Test store_correct."""
        fid = temp_store.store(sample_feedback)
        assert fid != ""
        assert os.path.exists(temp_store._path(fid))  # pylint: disable=protected-access

    def test_store_correct_with_notes(self, temp_store):
        """Test store_correct_with_notes."""
        fb = TafsirFeedback(
            question="test",
            llm_response="test response",
            reviewer="muhammad",
            verdict="correct_notes",
            notes="كويس بس ممكن يضيف حديث ابن مسعود",
        )
        fid = temp_store.store(fb)
        retrieved = temp_store.get(fid)
        assert retrieved.verdict == "correct_notes"
        assert "ابن مسعود" in retrieved.notes

    def test_store_wrong(self, temp_store):
        """Test store_wrong."""
        fb = TafsirFeedback(
            question="test",
            llm_response="test",
            reviewer="muhammad",
            verdict="wrong",
        )
        fid = temp_store.store(fb)
        retrieved = temp_store.get(fid)
        assert retrieved.verdict == "wrong"

    def test_store_wrong_with_notes(self, temp_store):
        """Test store_wrong_with_notes."""
        fb = TafsirFeedback(
            question="test",
            llm_response="test",
            reviewer="muhammad",
            verdict="wrong_notes",
            notes="الآية مش مرتبطة بيوم بدر",
        )
        fid = temp_store.store(fb)
        retrieved = temp_store.get(fid)
        assert retrieved.verdict == "wrong_notes"

    def test_invalid_verdict(self, temp_store):
        """Test invalid_verdict."""
        fb = TafsirFeedback(verdict="invalid")
        with pytest.raises(ValueError):
            temp_store.store(fb)

    def test_get_nonexistent(self, temp_store):
        """Test get_nonexistent."""
        result = temp_store.get("nonexistent")
        assert result is None

    def test_list_all(self, temp_store):
        """Test list_all."""
        fb1 = TafsirFeedback(
            question="q1", llm_response="r1", reviewer="m", verdict="correct"
        )
        fb2 = TafsirFeedback(
            question="q2", llm_response="r2", reviewer="m", verdict="wrong"
        )
        temp_store.store(fb1)
        temp_store.store(fb2)
        entries = temp_store.list_all()
        assert len(entries) == 2

    def test_auto_id_and_timestamp(self, temp_store, sample_feedback):
        """Test auto_id_and_timestamp."""
        fid = temp_store.store(sample_feedback)
        retrieved = temp_store.get(fid)
        assert retrieved.feedback_id != ""
        assert retrieved.timestamp > 0


class TestFeedbackStats:
    """TestFeedbackStats class."""

    def test_stats_empty(self, temp_store):
        """Test stats_empty."""
        stats = temp_store.get_stats()
        assert stats["total"] == 0
        assert stats["accuracy"] == 0

    def test_stats_mixed(self, temp_store):
        """Test stats_mixed."""
        for v in ["correct", "correct_notes", "wrong", "correct"]:
            fb = TafsirFeedback(question="q", llm_response="r", reviewer="m", verdict=v)
            temp_store.store(fb)
        stats = temp_store.get_stats()
        assert stats["total"] == 4
        assert stats["correct"] == 3  # 2 correct + 1 correct_notes
        assert stats["wrong"] == 1
        assert stats["accuracy"] == 75.0


class TestPipelineFeedback:
    """TestPipelineFeedback class."""

    def test_submit_feedback(self):
        """Test submit_feedback."""
        if not os.path.exists(DB_PATH):
            pytest.skip("proposed_edges.db not found")

        def mock_llm(_messages, _tools=None):
            return {"content": "إجابة تجريبية", "tool_calls": None}

        tmpdir = tempfile.mkdtemp()
        pipeline = TafsirPipeline(DB_PATH, mock_llm, model_name="mock")
        pipeline.feedback_store = TafsirFeedbackStore(storage_dir=tmpdir)

        result = pipeline.run("ما تفسير الآية 6:5؟")
        fid = pipeline.submit_feedback(
            result=result,
            verdict="correct_notes",
            reviewer="muhammad",
            notes="كويس بس ناقص ربط بالسيرة",
        )

        assert fid != ""
        fb = pipeline.feedback_store.get(fid)
        assert fb.verdict == "correct_notes"
        assert fb.reviewer == "muhammad"
        assert fb.question == "ما تفسير الآية 6:5؟"
        assert "6:5" in fb.verse_refs

        shutil.rmtree(tmpdir)

    def test_feedback_stats(self):
        """Test feedback_stats."""
        if not os.path.exists(DB_PATH):
            pytest.skip("proposed_edges.db not found")

        def mock_llm(_messages, _tools=None):
            return {"content": "test", "tool_calls": None}

        tmpdir = tempfile.mkdtemp()
        pipeline = TafsirPipeline(DB_PATH, mock_llm)
        pipeline.feedback_store = TafsirFeedbackStore(storage_dir=tmpdir)

        result = pipeline.run("test")
        pipeline.submit_feedback(result, "correct", "reviewer1")
        pipeline.submit_feedback(result, "wrong_notes", "reviewer2", "غلط")

        stats = pipeline.get_feedback_stats()
        assert stats["total"] == 2
        assert stats["correct"] == 1
        assert stats["wrong"] == 1

        shutil.rmtree(tmpdir)
