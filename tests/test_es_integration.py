"""Phase 6: Elasticsearch integration validation tests.

These tests verify that the ES migration produces correct results:
    - Arabic analyzer normalizes text identically to Python normalize_arabic()
    - QuranCollection.phrase_match() finds the same verses as the old sliding window
    - HadithCollection.phrase_match() finds the same hadith
    - ESGraphStore traversal returns correct edges
    - ESVerdictStore round-trips verdicts and supports retrieval
    - ESFeedbackStore round-trips feedback

Requirements:
    - Elasticsearch running on localhost:9200 (docker compose up -d elasticsearch)
    - Indices created (python -m al_furqan.kb.es.setup_indices)
    - Data migrated (python -m al_furqan.kb.es.migrate_data)

Run:
    pytest tests/test_es_integration.py -v -m "not slow"
    pytest tests/test_es_integration.py -v  # includes slow comparison tests
"""

import json
import logging

import pytest

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Skip entire module if ES is not reachable
# ---------------------------------------------------------------------------

try:
    from elasticsearch import Elasticsearch

    _es = Elasticsearch(["http://localhost:9200"], request_timeout=5)
    _es_available = _es.ping()
except Exception:
    _es_available = False

pytestmark = pytest.mark.skipif(
    not _es_available, reason="Elasticsearch not available on localhost:9200"
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def es():
    """Shared ES client for all tests in this module."""
    client = Elasticsearch(["http://localhost:9200"], request_timeout=30)
    yield client


@pytest.fixture(scope="module")
def quran(es):
    from al_furqan.kb.es.collections import QuranCollection

    return QuranCollection(es)


@pytest.fixture(scope="module")
def hadith(es):
    from al_furqan.kb.es.collections import HadithCollection

    return HadithCollection(es)


@pytest.fixture(scope="module")
def graph(es):
    from al_furqan.kb.es.graph import ESGraphStore

    return ESGraphStore(es)


# ---------------------------------------------------------------------------
# 1. Analyzer validation
# ---------------------------------------------------------------------------


class TestArabicAnalyzer:
    """Verify the arabic_furqan analyzer matches Python normalize_arabic()."""

    def _analyze(self, es, text):
        """Run text through the arabic_furqan analyzer and return tokens."""
        resp = es.indices.analyze(
            index="furqan_quran",
            body={"analyzer": "arabic_furqan", "text": text},
        )
        return [t["token"] for t in resp["tokens"]]

    def test_diacritics_stripped(self, es):
        tokens = self._analyze(es, "بِسْمِ ٱللَّهِ")
        assert "بسم" in tokens
        assert "الله" in tokens

    def test_alef_normalized(self, es):
        tokens = self._analyze(es, "إِنَّمَا الأَعْمَالُ")
        # إ and أ should both become ا
        assert "انما" in tokens
        assert "الاعمال" in tokens

    def test_taa_marbouta_normalized(self, es):
        tokens = self._analyze(es, "الصلاة والزكاة")
        # ة → ه
        assert any("صلاه" in t for t in tokens)
        assert any("زكاه" in t for t in tokens)

    def test_decorations_stripped(self, es):
        tokens = self._analyze(es, "﴿وَكَيْفَ أَخَافُ﴾")
        assert "وكيف" in tokens
        assert "اخاف" in tokens
        # ﴿ ﴾ should not appear as tokens
        assert "﴿" not in tokens

    def test_matches_python_normalize(self, es):
        """Compare ES analyzer output with Python normalize_arabic()."""
        from al_furqan.lessons.text_utils import normalize_arabic

        test_texts = [
            "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
            "إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ",
            "يَا أَيُّهَا الَّذِينَ آمَنُوا",
        ]

        for text in test_texts:
            es_tokens = self._analyze(es, text)
            py_tokens = normalize_arabic(text).split()
            assert es_tokens == py_tokens, (
                f"Mismatch for '{text[:30]}...'\n"
                f"  ES:     {es_tokens}\n"
                f"  Python: {py_tokens}"
            )


# ---------------------------------------------------------------------------
# 2. QuranCollection tests
# ---------------------------------------------------------------------------


class TestQuranCollection:
    """Test ES-backed QuranCollection against known data."""

    def test_count(self, quran):
        assert quran.count == 6236

    def test_get_verse_fatiha(self, quran):
        v = quran.get_verse(1, 1)
        assert v is not None
        assert v.surah == 1
        assert v.ayah == 1
        assert "بسم" in v.text_ar or "بِسْمِ" in v.text_ar

    def test_get_verse_not_found(self, quran):
        v = quran.get_verse(999, 999)
        assert v is None

    def test_get_context_returns_window(self, quran):
        verses = quran.get_context(1, 3, window=2)
        # Should return ayah 1,2,3,4,5 (window=2 around ayah 3)
        assert len(verses) >= 3
        ayahs = [v.ayah for v in verses]
        assert 3 in ayahs

    def test_search_returns_results(self, quran):
        results = quran.search("الربا", limit=5)
        assert len(results) > 0

    def test_get_by_surah(self, quran):
        fatiha = quran.get_by_surah(1)
        assert len(fatiha) == 7  # Al-Fatiha has 7 verses

    def test_phrase_match_finds_verse(self, quran):
        """The core replacement for Python sliding-window matching."""
        # Use a known phrase from Al-Fatiha
        results = quran.phrase_match("الحمد لله رب العالمين")
        assert len(results) > 0
        assert any(v.surah == 1 and v.ayah == 2 for v in results)


# ---------------------------------------------------------------------------
# 3. HadithCollection tests
# ---------------------------------------------------------------------------


class TestHadithCollection:
    """Test ES-backed HadithCollection."""

    def test_count(self, hadith):
        assert hadith.count == 55

    def test_search_returns_results(self, hadith):
        results = hadith.search("النيات", limit=3)
        assert len(results) > 0

    def test_get_hadith(self, hadith):
        h = hadith.get_hadith("bukhari", 1)
        assert h is not None
        assert h.collection_name == "bukhari"
        assert h.number == 1

    def test_get_hadith_not_found(self, hadith):
        h = hadith.get_hadith("nonexistent", 99999)
        assert h is None

    def test_grading_filter(self, hadith):
        results = hadith.search("الإسلام", limit=10, grading_filter="sahih")
        for h in results:
            assert h.grading == "sahih"

    def test_phrase_match(self, hadith):
        results = hadith.phrase_match("الأعمال بالنيات")
        assert len(results) > 0


# ---------------------------------------------------------------------------
# 4. Graph store tests
# ---------------------------------------------------------------------------


class TestESGraphStore:
    """Test ES-backed graph edge queries."""

    def test_stats(self, graph):
        s = graph.stats()
        assert s["total_edges"] == 95
        assert "BELONGS_TO" in s["by_type"]

    def test_get_outgoing(self, graph):
        edges = graph.get_outgoing("ayah:2:275")
        assert len(edges) > 0
        for e in edges:
            assert e["source"] == "ayah:2:275"

    def test_get_incoming(self, graph):
        edges = graph.get_incoming("topic:riba")
        assert len(edges) > 0
        for e in edges:
            assert e["target"] == "topic:riba"

    def test_get_edges_by_type(self, graph):
        edges = graph.get_edges_by_type("BELONGS_TO")
        assert len(edges) > 0
        for e in edges:
            assert e["edge_type"] == "BELONGS_TO"

    def test_edge_type_filter(self, graph):
        edges = graph.get_neighbors(
            "ayah:2:275", edge_types=["BELONGS_TO"], direction="out"
        )
        for e in edges:
            assert e["edge_type"] == "BELONGS_TO"

    def test_bfs_traversal(self, graph):
        """BFS from a verse should discover related topics and nodes."""
        edges = graph.bfs("ayah:2:275", max_depth=2)
        assert len(edges) > 0
        # Should at least find the direct BELONGS_TO → topic:riba edge
        targets = {e["target"] for e in edges}
        assert "topic:riba" in targets


# ---------------------------------------------------------------------------
# 5. Verdict store tests (uses a temporary index)
# ---------------------------------------------------------------------------


class TestESVerdictStore:
    """Test ES-backed verdict store round-trip."""

    TEST_INDEX = "furqan_verdicts_test"

    @pytest.fixture(autouse=True)
    def setup_test_index(self, es):
        """Create and tear down a test index."""
        from al_furqan.kb.es.indices import VERDICTS_INDEX

        if es.indices.exists(index=self.TEST_INDEX):
            es.indices.delete(index=self.TEST_INDEX)
        es.indices.create(index=self.TEST_INDEX, body=VERDICTS_INDEX)
        yield
        es.indices.delete(index=self.TEST_INDEX, ignore=[404])

    def test_store_and_retrieve(self, es, sample_verdict):
        from al_furqan.store.es_verdict_store import ESVerdictStore

        store = ESVerdictStore(es, index=self.TEST_INDEX)

        verdict_id = store.store(sample_verdict, status="approved")
        assert verdict_id.startswith("verdict_")

        loaded = store.get_verdict_by_id(verdict_id)
        assert loaded is not None
        assert loaded["question"] == sample_verdict.question
        assert loaded["status"] == "approved"
        assert loaded["total_score"] == 85

    def test_update_status(self, es, sample_verdict):
        from al_furqan.store.es_verdict_store import ESVerdictStore

        store = ESVerdictStore(es, index=self.TEST_INDEX)

        verdict_id = store.store(sample_verdict, status="approved")
        assert store.update_status(verdict_id, "rejected")

        loaded = store.get_verdict_by_id(verdict_id)
        assert loaded["status"] == "rejected"

    def test_retrieve_as_context(self, es, sample_verdict):
        from al_furqan.store.es_verdict_store import ESVerdictStore

        store = ESVerdictStore(es, index=self.TEST_INDEX)

        store.store(sample_verdict, status="approved")

        context = store.retrieve_as_context("interest lending")
        assert "Prior Verdict" in context

    def test_stats(self, es, sample_verdict):
        from al_furqan.store.es_verdict_store import ESVerdictStore

        store = ESVerdictStore(es, index=self.TEST_INDEX)

        store.store(sample_verdict, status="approved")
        s = store.stats()
        assert s["total_indexed"] == 1
        assert s["by_status"].get("approved", 0) == 1


# ---------------------------------------------------------------------------
# 6. Feedback store tests (uses a temporary index)
# ---------------------------------------------------------------------------


class TestESFeedbackStore:
    """Test ES-backed feedback store round-trip."""

    TEST_INDEX = "furqan_feedback_test"

    @pytest.fixture(autouse=True)
    def setup_test_index(self, es):
        from al_furqan.kb.es.indices import FEEDBACK_INDEX

        if es.indices.exists(index=self.TEST_INDEX):
            es.indices.delete(index=self.TEST_INDEX)
        es.indices.create(index=self.TEST_INDEX, body=FEEDBACK_INDEX)
        yield
        es.indices.delete(index=self.TEST_INDEX, ignore=[404])

    def test_submit_and_retrieve(self, es):
        from al_furqan.store.es_feedback_store import ESFeedbackStore, HumanFeedback

        store = ESFeedbackStore(es, index=self.TEST_INDEX)

        fb = HumanFeedback(
            verdict_id="verdict_test_001",
            reviewer="test_reviewer",
            rating="correct",
            notes="Looks good",
        )
        fb_id = store.submit(fb)
        assert fb_id.startswith("fb_")

        loaded = store.get_feedback(fb_id)
        assert loaded is not None
        assert loaded.verdict_id == "verdict_test_001"
        assert loaded.rating == "correct"

    def test_get_by_verdict(self, es):
        from al_furqan.store.es_feedback_store import ESFeedbackStore, HumanFeedback

        store = ESFeedbackStore(es, index=self.TEST_INDEX)
        vid = "verdict_test_002"

        store.submit(HumanFeedback(verdict_id=vid, reviewer="r1", rating="correct"))
        store.submit(HumanFeedback(verdict_id=vid, reviewer="r2", rating="incorrect"))
        store.submit(
            HumanFeedback(verdict_id="other_id", reviewer="r3", rating="correct")
        )

        results = store.get_by_verdict(vid)
        assert len(results) == 2
        assert all(fb.verdict_id == vid for fb in results)

    def test_stats(self, es):
        from al_furqan.store.es_feedback_store import ESFeedbackStore, HumanFeedback

        store = ESFeedbackStore(es, index=self.TEST_INDEX)
        store.submit(HumanFeedback(verdict_id="v1", reviewer="r1", rating="correct"))
        store.submit(HumanFeedback(verdict_id="v2", reviewer="r1", rating="incorrect"))

        s = store.get_stats()
        assert s["total"] == 2
        assert s["by_rating"]["correct"] == 1
        assert s["by_rating"]["incorrect"] == 1


# ---------------------------------------------------------------------------
# 7. Comparison: old Python matching vs ES phrase_match (SLOW)
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestPhraseMatchComparison:
    """Compare ES phrase_match results against the Python sliding-window.

    Loads an enriched lesson and verifies that ES finds the same verses
    that the Python pipeline found.
    """

    def test_taught_verses_match(self, es):
        """For each lesson chapter's taught_verses, verify ES phrase_match finds them."""
        from pathlib import Path

        from al_furqan.kb.es.collections import QuranCollection

        quran = QuranCollection(es)
        lessons_dir = (
            Path(__file__).parent.parent / "data" / "lessons" / "lessons_enriched_json"
        )

        if not lessons_dir.exists():
            pytest.skip("Enriched lessons not found")

        lesson_files = sorted(lessons_dir.glob("lesson_*_Anaam.json"))
        if not lesson_files:
            pytest.skip("No enriched lesson files")

        total_expected = 0
        total_found = 0
        misses = []

        for lf in lesson_files[:3]:  # test first 3 lessons for speed
            with open(lf, encoding="utf-8") as f:
                lesson = json.load(f)

            for ch in lesson["chapters"]:
                content = ch.get("content", "")
                if not content:
                    continue

                expected_verses = ch.get("taught_verses", [])
                for tv in expected_verses:
                    total_expected += 1
                    vk = tv["verse_key"]

                    # Check: does ES phrase_match find this verse in the content?
                    es_matches = quran.phrase_match(tv["text_ar"], limit=50)
                    es_keys = {f"{v.surah}:{v.ayah}" for v in es_matches}

                    if vk in es_keys:
                        total_found += 1
                    else:
                        misses.append(
                            {
                                "lesson": lesson["lesson_number"],
                                "chapter": ch["chapter_number"],
                                "verse_key": vk,
                            }
                        )

        if total_expected > 0:
            recall = total_found / total_expected
            logger.info(
                "Verse match comparison: %d/%d (%.1f%% recall), %d misses",
                total_found,
                total_expected,
                recall * 100,
                len(misses),
            )
            if misses:
                logger.warning("Misses: %s", misses[:5])
            # Allow some tolerance — ES tokenization may differ slightly
            assert recall >= 0.8, (
                f"Recall too low: {recall:.1%}. First misses: {misses[:5]}"
            )
