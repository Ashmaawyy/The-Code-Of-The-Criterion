"""
Reference Validator for Quranic verse references.

Validates surah:ayah format references against known verse counts.
"""

import re
from dataclasses import dataclass

# Ayah counts for all 114 surahs
# Source: Standard Uthmani Mushaf
SURAH_AYAH_COUNTS = {
    1: 7,
    2: 286,
    3: 200,
    4: 176,
    5: 120,
    6: 165,
    7: 206,
    8: 75,
    9: 129,
    10: 109,
    11: 123,
    12: 111,
    13: 43,
    14: 52,
    15: 99,
    16: 128,
    17: 111,
    18: 110,
    19: 98,
    20: 135,
    21: 112,
    22: 78,
    23: 118,
    24: 64,
    25: 77,
    26: 227,
    27: 93,
    28: 88,
    29: 69,
    30: 60,
    31: 34,
    32: 30,
    33: 73,
    34: 54,
    35: 45,
    36: 83,
    37: 182,
    38: 88,
    39: 75,
    40: 85,
    41: 54,
    42: 53,
    43: 89,
    44: 59,
    45: 37,
    46: 35,
    47: 38,
    48: 29,
    49: 18,
    50: 45,
    51: 60,
    52: 49,
    53: 62,
    54: 55,
    55: 78,
    56: 96,
    57: 29,
    58: 22,
    59: 24,
    60: 13,
    61: 14,
    62: 11,
    63: 11,
    64: 18,
    65: 12,
    66: 12,
    67: 30,
    68: 52,
    69: 52,
    70: 44,
    71: 28,
    72: 28,
    73: 20,
    74: 56,
    75: 40,
    76: 31,
    77: 50,
    78: 40,
    79: 46,
    80: 42,
    81: 29,
    82: 19,
    83: 36,
    84: 25,
    85: 22,
    86: 17,
    87: 19,
    88: 26,
    89: 30,
    90: 20,
    91: 15,
    92: 21,
    93: 11,
    94: 8,
    95: 8,
    96: 19,
    97: 5,
    98: 8,
    99: 8,
    100: 11,
    101: 11,
    102: 8,
    103: 3,
    104: 9,
    105: 5,
    106: 4,
    107: 7,
    108: 3,
    109: 6,
    110: 3,
    111: 5,
    112: 4,
    113: 5,
    114: 6,
}

SURAH_NAMES = {
    1: "الفاتحة",
    2: "البقرة",
    3: "آل عمران",
    4: "النساء",
    5: "المائدة",
    6: "الأنعام",
    7: "الأعراف",
    8: "الأنفال",
    9: "التوبة",
    10: "يونس",
    11: "هود",
    12: "يوسف",
    13: "الرعد",
    14: "إبراهيم",
    15: "الحجر",
    16: "النحل",
    17: "الإسراء",
    18: "الكهف",
    19: "مريم",
    20: "طه",
    21: "الأنبياء",
    22: "الحج",
    23: "المؤمنون",
    24: "النور",
    25: "الفرقان",
    26: "الشعراء",
    27: "النمل",
    28: "القصص",
    29: "العنكبوت",
    30: "الروم",
    31: "لقمان",
    32: "السجدة",
    33: "الأحزاب",
    34: "سبأ",
    35: "فاطر",
    36: "يس",
    37: "الصافات",
    38: "ص",
    39: "الزمر",
    40: "غافر",
    41: "فصلت",
    42: "الشورى",
    43: "الزخرف",
    44: "الدخان",
    45: "الجاثية",
    46: "الأحقاف",
    47: "محمد",
    48: "الفتح",
    49: "الحجرات",
    50: "ق",
    51: "الذاريات",
    52: "الطور",
    53: "النجم",
    54: "القمر",
    55: "الرحمن",
    56: "الواقعة",
    57: "الحديد",
    58: "المجادلة",
    59: "الحشر",
    60: "الممتحنة",
    61: "الصف",
    62: "الجمعة",
    63: "المنافقون",
    64: "التغابن",
    65: "الطلاق",
    66: "التحريم",
    67: "الملك",
    68: "القلم",
    69: "الحاقة",
    70: "المعارج",
    71: "نوح",
    72: "الجن",
    73: "المزمل",
    74: "المدثر",
    75: "القيامة",
    76: "الإنسان",
    77: "المرسلات",
    78: "النبأ",
    79: "النازعات",
    80: "عبس",
    81: "التكوير",
    82: "الانفطار",
    83: "المطففين",
    84: "الانشقاق",
    85: "البروج",
    86: "الطارق",
    87: "الأعلى",
    88: "الغاشية",
    89: "الفجر",
    90: "البلد",
    91: "الشمس",
    92: "الليل",
    93: "الضحى",
    94: "الشرح",
    95: "التين",
    96: "العلق",
    97: "القدر",
    98: "البينة",
    99: "الزلزلة",
    100: "العاديات",
    101: "القارعة",
    102: "التكاثر",
    103: "العصر",
    104: "الهمزة",
    105: "الفيل",
    106: "قريش",
    107: "الماعون",
    108: "الكوثر",
    109: "الكافرون",
    110: "النصر",
    111: "المسد",
    112: "الإخلاص",
    113: "الفلق",
    114: "الناس",
}

# Pattern for surah:ayah references
_REF_PATTERN = re.compile(r"(\d+):(\d+)(?:-(\d+))?")


@dataclass
class ValidationResult:
    """Result of validating a reference."""

    reference: str
    valid: bool
    error: str | None = None
    surah_number: int | None = None
    ayah_start: int | None = None
    ayah_end: int | None = None
    surah_name: str | None = None


def validate_reference(ref: str) -> ValidationResult:  # pylint: disable=too-many-return-statements
    """
    Validate a Quranic verse reference in surah:ayah or surah:ayah-ayah format.

    Examples:
        "6:1"       -> valid (Al-Anam, verse 1)
        "6:1-5"     -> valid (Al-Anam, verses 1-5)
        "6:166"     -> invalid (Al-Anam only has 165 verses)
        "115:1"     -> invalid (only 114 surahs)
    """
    ref = ref.strip()
    match = _REF_PATTERN.fullmatch(ref)
    if not match:
        return ValidationResult(
            reference=ref,
            valid=False,
            error=f"Invalid format: '{ref}'. Expected surah:ayah or surah:ayah_start-ayah_end",
        )

    surah = int(match.group(1))
    ayah_start = int(match.group(2))
    ayah_end = int(match.group(3)) if match.group(3) else ayah_start

    # Check surah range
    if surah < 1 or surah > 114:
        return ValidationResult(
            reference=ref,
            valid=False,
            error=f"Invalid surah number {surah}. Must be 1-114.",
            surah_number=surah,
        )

    max_ayah = SURAH_AYAH_COUNTS[surah]
    surah_name = SURAH_NAMES.get(surah, "")

    # Check ayah range
    if ayah_start < 1:
        return ValidationResult(
            reference=ref,
            valid=False,
            error=f"Ayah number must be >= 1, got {ayah_start}.",
            surah_number=surah,
            surah_name=surah_name,
        )

    if ayah_start > max_ayah:
        return ValidationResult(
            reference=ref,
            valid=False,
            error=f"Surah {surah} ({surah_name}) has {max_ayah} ayahs, but got ayah {ayah_start}.",
            surah_number=surah,
            ayah_start=ayah_start,
            surah_name=surah_name,
        )

    if ayah_end > max_ayah:
        return ValidationResult(
            reference=ref,
            valid=False,
            error=f"Surah {surah} ({surah_name}) has {max_ayah} ayahs, but got ayah {ayah_end}.",
            surah_number=surah,
            ayah_start=ayah_start,
            ayah_end=ayah_end,
            surah_name=surah_name,
        )

    if ayah_end < ayah_start:
        return ValidationResult(
            reference=ref,
            valid=False,
            error=f"Ayah range is reversed: {ayah_start}-{ayah_end}.",
            surah_number=surah,
            ayah_start=ayah_start,
            ayah_end=ayah_end,
            surah_name=surah_name,
        )

    return ValidationResult(
        reference=ref,
        valid=True,
        surah_number=surah,
        ayah_start=ayah_start,
        ayah_end=ayah_end,
        surah_name=surah_name,
    )


def validate_references(refs: list[str]) -> list[ValidationResult]:
    """Validate a list of references."""
    return [validate_reference(r) for r in refs]


def extract_references_from_text(text: str) -> list[str]:
    """Extract potential surah:ayah references from free text."""
    return _REF_PATTERN.findall(text)
