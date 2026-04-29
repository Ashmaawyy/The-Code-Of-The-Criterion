"""Unit tests for the Arabic ordinal composition logic."""

from al_furqan.lessons.text_utils import to_arabic_ordinal


class TestArabicOrdinalUnits:
    def test_one(self):
        assert to_arabic_ordinal(1) == "الأول"

    def test_five(self):
        assert to_arabic_ordinal(5) == "الخامس"

    def test_ten(self):
        assert to_arabic_ordinal(10) == "العاشر"


class TestArabicOrdinalTeens:
    def test_eleven(self):
        assert to_arabic_ordinal(11) == "الحادي عشر"

    def test_fifteen(self):
        assert to_arabic_ordinal(15) == "الخامس عشر"

    def test_nineteen(self):
        assert to_arabic_ordinal(19) == "التاسع عشر"


class TestArabicOrdinalTens:
    def test_twenty(self):
        assert to_arabic_ordinal(20) == "العشرون"

    def test_thirty(self):
        assert to_arabic_ordinal(30) == "الثلاثون"

    def test_ninety(self):
        assert to_arabic_ordinal(90) == "التسعون"


class TestArabicOrdinalCompound:
    def test_twenty_one(self):
        assert to_arabic_ordinal(21) == "الأول والعشرون"

    def test_twenty_four(self):
        assert to_arabic_ordinal(24) == "الرابع والعشرون"

    def test_fifty_five(self):
        assert to_arabic_ordinal(55) == "الخامس والخمسون"

    def test_ninety_nine(self):
        assert to_arabic_ordinal(99) == "التاسع والتسعون"


class TestArabicOrdinalHundreds:
    def test_hundred(self):
        assert to_arabic_ordinal(100) == "المائة"

    def test_two_hundred(self):
        assert to_arabic_ordinal(200) == "المائتان"

    def test_three_hundred(self):
        assert to_arabic_ordinal(300) == "الثلاثمائة"

    def test_hundred_one(self):
        assert to_arabic_ordinal(101) == "الأول والمائة"

    def test_hundred_fifteen(self):
        assert to_arabic_ordinal(115) == "الخامس عشر والمائة"

    def test_two_fifty(self):
        assert to_arabic_ordinal(250) == "الخمسون والمائتان"

    def test_three_twenty_one(self):
        assert to_arabic_ordinal(321) == "الأول والعشرون والثلاثمائة"

    def test_nine_ninety_nine(self):
        assert to_arabic_ordinal(999) == "التاسع والتسعون والتسعمائة"


class TestArabicOrdinalEdgeCases:
    def test_zero_returns_string(self):
        assert to_arabic_ordinal(0) == "0"

    def test_negative_returns_string(self):
        assert to_arabic_ordinal(-1) == "-1"

    def test_thousand_returns_string(self):
        assert to_arabic_ordinal(1000) == "1000"

    def test_all_units_are_unique(self):
        results = [to_arabic_ordinal(i) for i in range(1, 11)]
        assert len(results) == len(set(results))

    def test_full_range_no_empty(self):
        """Every number 1-999 produces a non-empty string."""
        for i in range(1, 1000):
            result = to_arabic_ordinal(i)
            assert result, f"Empty result for {i}"
            assert result != str(i), f"Fallback to digit string for {i}"
