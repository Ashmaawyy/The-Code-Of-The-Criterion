"""Shared text processing utilities for lesson pipeline scripts.

Centralizes Arabic normalization, timestamp detection, and chapter
pattern matching so that clean_transcripts.py, enrich_lessons.py,
and pipeline.py all use the same definitions.
"""

import re

# ---------------------------------------------------------------------------
# Timestamp patterns
# ---------------------------------------------------------------------------
# Covers YouTube's human-readable timestamps and common SRT/VTT numeric formats.

TIMESTAMP_PATTERNS = [
    # YouTube human-readable: "0:08", "12:30", "1:05:30"
    re.compile(r'^\d{1,2}:\d{2}(:\d{2})?$'),
    # YouTube descriptive: "8 seconds", "1 minute, 30 seconds", "2 hours, 5 minutes"
    re.compile(
        r'^\d+\s+(?:hours?|minutes?|seconds?)'
        r'(?:,?\s+\d+\s+(?:hours?|minutes?|seconds?))*$'
    ),
    # SRT / VTT numeric: "00:01:23,456" or "00:01:23.456"
    re.compile(r'^\d{2}:\d{2}:\d{2}[,.]\d{3}$'),
    # Bare seconds often seen in auto-captions: "83" — require at least
    # two digits to avoid matching simple line numbers like "1" or "2".
    re.compile(r'^\d{2,6}$'),
]

# ---------------------------------------------------------------------------
# Chapter heading pattern
# ---------------------------------------------------------------------------
# Accepts "Chapter 1: Title" and common variants like
# "chapter 1 - Title" or "CHAPTER 01: Title".

CHAPTER_PATTERN = re.compile(r'^[Cc]hapter\s+(\d+)\s*[:–—\-]\s*(.+)$')

# ---------------------------------------------------------------------------
# Arabic diacritics / decoration removal
# ---------------------------------------------------------------------------
# Pre-compiled for performance — these run thousands of times during matching.

_RE_DIACRITICS = re.compile(
    r'[\u0610-\u061A\u064B-\u065F\u0670'
    r'\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED]'
)
_RE_ALEF_VARIANTS = re.compile(r'[إأآٱ]')
_RE_DECORATIONS = re.compile(r'[﴿﴾۝۞\u06DD\uFD3E\uFD3F]')
_RE_WHITESPACE = re.compile(r'\s+')


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def is_blank(line: str) -> bool:
    """Return True if the line is empty or whitespace-only."""
    return not line.strip()


def is_timestamp(line: str) -> bool:
    """Return True if the line matches a known YouTube timestamp pattern."""
    line = line.strip()
    if not line:
        return False
    return any(pat.match(line) for pat in TIMESTAMP_PATTERNS)


def normalize_arabic(text: str) -> str:
    """Normalize Arabic text for fuzzy comparison.

    - Removes diacritics (tashkeel)
    - Normalizes alef variants → plain alef
    - Normalizes taa marbouta → haa, alef maqsura → yaa
    - Strips tatweel and Quranic decoration marks
    - Collapses whitespace
    """
    if not text:
        return ""
    text = _RE_DIACRITICS.sub('', text)
    text = _RE_ALEF_VARIANTS.sub('ا', text)
    text = text.replace('ة', 'ه').replace('ى', 'ي').replace('\u0640', '')
    text = _RE_DECORATIONS.sub('', text)
    return _RE_WHITESPACE.sub(' ', text).strip()


def extract_words(text: str) -> list[str]:
    """Extract Arabic words (length > 1) from text after normalization."""
    return [w for w in normalize_arabic(text).split() if len(w) > 1]


# ---------------------------------------------------------------------------
# Arabic ordinal composition
# ---------------------------------------------------------------------------
# Arabic ordinals are composed from a fixed vocabulary of 28 atomic words.
# Every number 1–999 is a grammatical combination of these atoms:
#   - units (1-10): "الأول" ... "العاشر"
#   - teens (11-19): "الحادي عشر" ... "التاسع عشر"
#   - tens  (20-90): "العشرون" ... "التسعون"
#   - hundreds (100-900): "المائة" ... "التسعمائة"
# Composition rule: ones و tens و hundreds  (right-to-left reading order)

_ORDINAL_UNITS = [
    "", "الأول", "الثاني", "الثالث", "الرابع", "الخامس",
    "السادس", "السابع", "الثامن", "التاسع", "العاشر",
]
_ORDINAL_TEENS = [
    "", "الحادي عشر", "الثاني عشر", "الثالث عشر", "الرابع عشر",
    "الخامس عشر", "السادس عشر", "السابع عشر", "الثامن عشر", "التاسع عشر",
]
_ORDINAL_TENS = [
    "", "", "العشرون", "الثلاثون", "الأربعون", "الخمسون",
    "الستون", "السبعون", "الثمانون", "التسعون",
]
_ORDINAL_HUNDREDS = [
    "", "المائة", "المائتان", "الثلاثمائة", "الأربعمائة", "الخمسمائة",
    "الستمائة", "السبعمائة", "الثمانمائة", "التسعمائة",
]


def to_arabic_ordinal(n: int) -> str:
    """Convert a positive integer to Arabic ordinal text.

    Composes any number 1–999 from atomic ordinal words using standard
    Arabic grammar.  Numbers outside that range fall back to digit strings.

    Examples:
        1   → "الأول"
        15  → "الخامس عشر"
        21  → "الحادي والعشرون"
        100 → "المائة"
        315 → "الخامس عشر والثلاثمائة"
    """
    if n <= 0 or n >= 1000:
        return str(n)

    hundreds, remainder = divmod(n, 100)
    tens, ones = divmod(remainder, 10)

    parts: list[str] = []

    # Ones + teens are mutually exclusive
    if tens == 1 and ones > 0:
        # 11-19
        parts.append(_ORDINAL_TEENS[ones])
    else:
        if ones > 0:
            parts.append(_ORDINAL_UNITS[ones])
        if tens >= 2:
            parts.append(_ORDINAL_TENS[tens])

    # Exact 10 (العاشر)
    if tens == 1 and ones == 0:
        parts.append(_ORDINAL_UNITS[10])

    if hundreds > 0:
        parts.append(_ORDINAL_HUNDREDS[hundreds])

    return " و".join(parts)
