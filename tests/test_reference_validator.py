"""Tests for the reference validator."""

from al_furqan.kb.ingestion.reference_validator import (
    SURAH_AYAH_COUNTS,
    validate_reference,
    validate_references,
)


class TestValidateReference:
    """TestValidateReference class."""

    def test_valid_simple(self):
        """Valid surah:ayah reference."""
        r = validate_reference("6:1")
        assert r.valid is True
        assert r.surah_number == 6
        assert r.ayah_start == 1
        assert r.surah_name == "الأنعام"

    def test_valid_range(self):
        """Valid surah:ayah-ayah range."""
        r = validate_reference("6:1-5")
        assert r.valid is True
        assert r.ayah_start == 1
        assert r.ayah_end == 5

    def test_valid_last_verse_al_anam(self):
        """Al-Anam has exactly 165 verses."""
        r = validate_reference("6:165")
        assert r.valid is True

    def test_invalid_ayah_beyond_max(self):
        """Ayah number exceeds surah's verse count."""
        r = validate_reference("6:166")
        assert r.valid is False
        assert "165" in r.error

    def test_invalid_surah_zero(self):
        """Surah 0 is invalid."""
        r = validate_reference("0:1")
        assert r.valid is False

    def test_invalid_surah_115(self):
        """Surah 115 is invalid (only 114)."""
        r = validate_reference("115:1")
        assert r.valid is False

    def test_invalid_format(self):
        """Bad format is flagged."""
        r = validate_reference("abc")
        assert r.valid is False
        assert "Invalid format" in r.error

    def test_reversed_range(self):
        """Reversed ayah range is invalid."""
        r = validate_reference("6:10-5")
        assert r.valid is False
        assert "reversed" in r.error

    def test_fatiha(self):
        """Al-Fatiha has 7 verses."""
        r = validate_reference("1:7")
        assert r.valid is True
        r = validate_reference("1:8")
        assert r.valid is False

    def test_validate_batch(self):
        """Batch validation."""
        results = validate_references(["6:1", "6:166", "1:1"])
        assert results[0].valid is True
        assert results[1].valid is False
        assert results[2].valid is True

    def test_surah_ayah_counts_complete(self):
        """All 114 surahs are present in the lookup."""
        assert len(SURAH_AYAH_COUNTS) == 114
        for s in range(1, 115):
            assert s in SURAH_AYAH_COUNTS
