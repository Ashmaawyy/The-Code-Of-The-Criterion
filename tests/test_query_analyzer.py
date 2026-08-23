"""Tests for the Query Analyzer."""

from al_furqan.kb.tafsir.query_analyzer import (
    QueryType,
    _extract_verse_refs,
    analyze_query,
)


class TestVerseExtraction:
    """Test verse reference extraction from queries."""

    def test_explicit_numeric_ref(self):
        """Test explicit_numeric_ref."""
        refs = _extract_verse_refs("ما تفسير الآية 6:5؟")
        assert "6:5" in refs

    def test_ayah_number_with_default_surah(self):
        """Test ayah_number_with_default_surah."""
        refs = _extract_verse_refs("ما معنى الآية 5؟", default_surah=6)
        assert "6:5" in refs

    def test_ayah_number_raqm(self):
        """Test ayah_number_raqm."""
        refs = _extract_verse_refs("الآية رقم 121", default_surah=6)
        assert "6:121" in refs

    def test_first_n_ayat_arabic(self):
        """Test first_n_ayat_arabic."""
        refs = _extract_verse_refs("أول أربع آيات من سورة الأنعام")
        assert refs == ["6:1", "6:2", "6:3", "6:4"]

    def test_first_n_ayat_numeric(self):
        """Test first_n_ayat_numeric."""
        refs = _extract_verse_refs("أول 4 آيات من سورة الأنعام")
        assert refs == ["6:1", "6:2", "6:3", "6:4"]

    def test_surah_name_detection(self):
        """Test surah_name_detection."""
        refs = _extract_verse_refs("الآية 5 من سورة هود")
        assert "11:5" in refs

    def test_multiple_refs(self):
        """Test multiple_refs."""
        refs = _extract_verse_refs("العلاقة بين 6:1 و 6:5")
        assert "6:1" in refs
        assert "6:5" in refs

    def test_combined_first_n_and_ayah(self):
        """Test combined_first_n_and_ayah."""
        refs = _extract_verse_refs("علاقة أول أربع آيات من سورة الأنعام بالآية رقم 5")
        assert "6:1" in refs
        assert "6:2" in refs
        assert "6:3" in refs
        assert "6:4" in refs
        assert "6:5" in refs

    def test_no_refs(self):
        """Test no_refs."""
        refs = _extract_verse_refs("ما هو التوحيد؟")
        assert refs == []


class TestQueryTypeDetection:
    """Test query type detection."""

    def test_verse_link(self):
        """Test verse_link."""
        result = analyze_query("إيه علاقة أول أربع آيات من سورة الأنعام بالآية رقم 5")
        assert result.query_type == QueryType.VERSE_LINK

    def test_tafsir(self):
        """Test tafsir."""
        result = analyze_query("ما تفسير الآية 6:5؟")
        assert result.query_type == QueryType.TAFSIR

    def test_comparison(self):
        """Test comparison."""
        result = analyze_query("هل تقدر تجيب لي علاقة شبيهة من سور ثانية؟")
        assert result.query_type == QueryType.COMPARISON

    def test_seerah(self):
        """Test seerah."""
        result = analyze_query("ما علاقة الآية 5 بيوم بدر؟")
        assert result.query_type == QueryType.SEERAH_LINK

    def test_istinbat(self):
        """Test istinbat."""
        result = analyze_query("ما الدروس المستفادة من الآية 6:5؟")
        assert result.query_type == QueryType.ISTINBAT

    def test_general(self):
        """Test general."""
        result = analyze_query("ما هو التوحيد؟")
        assert result.query_type == QueryType.GENERAL

    def test_implicit_link_from_multiple_verses(self):
        """Test implicit_link_from_multiple_verses."""
        result = analyze_query("الفرق بين 6:1 و 6:5")
        assert result.query_type == QueryType.VERSE_LINK


class TestTopicExtraction:
    """Test topic extraction."""

    def test_tawhid(self):
        """Test tawhid."""
        result = analyze_query("ما علاقة التوحيد بسورة الأنعام؟")
        assert "التوحيد" in result.topics

    def test_sunnah_ilahiyyah(self):
        """Test sunnah_ilahiyyah."""
        result = analyze_query("ما هي السنة الإلهية في الآية 5؟")
        assert "السنة الإلهية" in result.topics

    def test_badr(self):
        """Test badr."""
        result = analyze_query("علاقة الآية 5 بيوم بدر")
        assert "يوم بدر" in result.topics

    def test_multiple_topics(self):
        """Test multiple_topics."""
        result = analyze_query("محاجة المشركين والتوحيد في سورة الأنعام")
        assert "التوحيد" in result.topics
        assert "محاجة المشركين" in result.topics


class TestFullAnalysis:
    """Test end-to-end query analysis."""

    def test_real_question_1(self):
        """Test real_question_1."""
        result = analyze_query("إيه علاقة أول أربع آيات من سورة الأنعام بالآية رقم 5")
        assert result.query_type == QueryType.VERSE_LINK
        assert len(result.verse_refs) == 5
        assert "6:5" in result.verse_refs

    def test_real_question_2(self):
        """Test real_question_2."""
        result = analyze_query("هل تقدر تجيب لي علاقة شبيهة من سور ثانية؟")
        assert result.query_type == QueryType.COMPARISON
        assert result.needs_external_knowledge is True

    def test_real_question_3(self):
        """Test real_question_3."""
        result = analyze_query("ما معنى لكل نبأ مستقر في الآية 6:67؟")
        assert "6:67" in result.verse_refs
        assert result.query_type == QueryType.TAFSIR
