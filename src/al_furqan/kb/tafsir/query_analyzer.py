"""
Query Analyzer — تحليل سؤال المستخدم واستخراج الآيات والمواضيع ونوع السؤال.

Stage ① in the Engine-Guided RAG pipeline.
"""

import re
from dataclasses import dataclass, field
from enum import Enum


class QueryType(str, Enum):
    """نوع السؤال — يحدد أي reasoning template يُستخدم."""

    TAFSIR = "tafsir"  # تفسير آية أو مجموعة آيات
    VERSE_LINK = "verse_link"  # ربط بين آيات
    ISTINBAT = "istinbat"  # استنباط ودروس
    COMPARISON = "comparison"  # مقارنة بين سور أو مواضع
    SEERAH_LINK = "seerah_link"  # ربط بالسيرة
    GENERAL = "general"  # سؤال عام


@dataclass
class QueryAnalysis:
    """نتيجة تحليل سؤال المستخدم."""

    original_query: str
    verse_refs: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    query_type: QueryType = QueryType.GENERAL
    search_keywords_ar: list[str] = field(default_factory=list)
    needs_external_knowledge: bool = False


# --- Verse Reference Extraction ---

# Matches: 6:5, الأنعام:5, سورة الأنعام الآية 5, الآية 5 من سورة الأنعام, etc.
_SURAH_NAMES = {
    "الفاتحة": 1,
    "البقرة": 2,
    "آل عمران": 3,
    "النساء": 4,
    "المائدة": 5,
    "الأنعام": 6,
    "الأعراف": 7,
    "الأنفال": 8,
    "التوبة": 9,
    "يونس": 10,
    "هود": 11,
    "يوسف": 12,
    "الرعد": 13,
    "إبراهيم": 14,
    "الحجر": 15,
    "النحل": 16,
    "الإسراء": 17,
    "الكهف": 18,
    "مريم": 19,
    "طه": 20,
    "الأنبياء": 21,
    "الحج": 22,
    "المؤمنون": 23,
    "النور": 24,
    "الفرقان": 25,
    "الشعراء": 26,
    "النمل": 27,
    "القصص": 28,
    "العنكبوت": 29,
    "الروم": 30,
    "لقمان": 31,
    "السجدة": 32,
    "الأحزاب": 33,
    "سبأ": 34,
    "فاطر": 35,
    "يس": 36,
    "الصافات": 37,
    "ص": 38,
    "الزمر": 39,
    "غافر": 40,
}

# Pattern: surah_number:ayah (e.g., 6:5, 2:255)
_NUMERIC_REF = re.compile(r"\b(\d{1,3}):(\d{1,3})\b")

# Pattern: الآية X / آية X / الآية رقم X
_AYAH_NUMBER = re.compile(r"(?:ال)?آي[ةه]\s*(?:رقم\s*)?(\d{1,3})")

# Pattern: أول X آيات / أول X آية
_FIRST_N = re.compile(r"أول\s+(\d+|أربع|ثلاث|اثنين|خمس|ست|سبع|ثمان|تسع|عشر)\s+آي[اةه]")

# Pattern: سورة X
_SURAH_NAME = re.compile(r"سور[ةه]\s+([\u0600-\u06FF\s]+?)(?:\s|$|،|,|\.|؟|\?)")

_ARABIC_NUMS = {
    "اثنين": 2,
    "ثلاث": 3,
    "أربع": 4,
    "خمس": 5,
    "ست": 6,
    "سبع": 7,
    "ثمان": 8,
    "تسع": 9,
    "عشر": 10,
}


def _extract_verse_refs(query: str, default_surah: int = 6) -> list[str]:
    """Extract verse references from query text."""
    refs = set()

    # 1. Explicit numeric refs: 6:5, 2:255
    for m in _NUMERIC_REF.finditer(query):
        refs.add(f"{m.group(1)}:{m.group(2)}")

    # 2. Detect surah from name
    surah_num = default_surah
    for m in _SURAH_NAME.finditer(query):
        name = m.group(1).strip()
        for sname, snum in _SURAH_NAMES.items():
            if sname in name or name in sname:
                surah_num = snum
                break

    # 3. الآية X → surah:X
    for m in _AYAH_NUMBER.finditer(query):
        ayah = int(m.group(1))
        ref = f"{surah_num}:{ayah}"
        if ref not in refs:
            refs.add(ref)

    # 4. أول N آيات → surah:1, surah:2, ..., surah:N
    for m in _FIRST_N.finditer(query):
        n_str = m.group(1)
        n = _ARABIC_NUMS.get(n_str, None)
        if n is None:
            try:
                n = int(n_str)
            except ValueError:
                n = 4  # default
        for i in range(1, n + 1):
            refs.add(f"{surah_num}:{i}")

    return sorted(refs, key=lambda r: (int(r.split(":")[0]), int(r.split(":")[1])))


# --- Query Type Detection ---

_TYPE_PATTERNS = {
    QueryType.SEERAH_LINK: [
        r"السيرة",
        r"سيرة",
        r"حادثة",
        r"واقعة",
        r"سبب النزول",
        r"نزول",
        r"يوم بدر",
    ],
    QueryType.VERSE_LINK: [
        r"علاقة.*آي",
        r"ربط.*آي",
        r"العلاقة بين",
        r"الربط بين",
        r"إيه العلاقة",
        r"ايه العلاقة",
        r"كيف ترتبط",
        r"الفرق بين.*\d+:\d+",
    ],
    QueryType.COMPARISON: [
        r"مقارن",
        r"قارن",
        r"الفرق بين.*سور",
        r"شبيه.*سور",
        r"من سور ثانية",
        r"من سور أخرى",
        r"في سور مختلفة",
    ],
    QueryType.TAFSIR: [
        r"تفسير",
        r"معنى",
        r"المقصود",
        r"ما المراد",
        r"اشرح",
        r"فسّر",
        r"ما دلالة",
    ],
    QueryType.ISTINBAT: [
        r"استنباط",
        r"الدروس",
        r"العبر",
        r"الفوائد",
        r"ما نتعلم",
        r"ماذا نستفيد",
        r"كيف نطبق",
        r"في واقعنا",
    ],
}


def _detect_query_type(query: str, verse_refs: list[str]) -> QueryType:
    """Detect the type of question based on patterns."""
    query_lower = query.strip()

    for qtype, patterns in _TYPE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, query_lower):
                return qtype

    # Fallback: if multiple verses → VERSE_LINK, single verse → TAFSIR
    if len(verse_refs) > 1:  # pylint: disable=no-else-return
        return QueryType.VERSE_LINK
    elif len(verse_refs) == 1:
        return QueryType.TAFSIR

    return QueryType.GENERAL


# --- Topic Extraction ---

_TOPIC_KEYWORDS = {
    "التوحيد": ["التوحيد", "توحيد", "العبودية", "عبودية"],
    "الشرك": ["الشرك", "شرك", "المشركين", "مشركين", "أشركوا"],
    "السنة الإلهية": ["السنة الإلهية", "سنة الله", "السنن الإلهية"],
    "محاجة المشركين": ["محاجة", "حجة", "حجته", "مجادلة", "جدال"],
    "قصة إبراهيم": ["إبراهيم", "ابراهيم"],
    "يوم بدر": ["بدر", "يوم بدر", "قليب بدر"],
    "العلم الإلهي": ["العلم الإلهي", "يعلم", "علم الله", "إحاطة"],
    "الهداية": ["الهداية", "هداية", "الهدى", "هدى"],
    "الأنعام والتشريع": ["الأنعام", "أنعام", "الذبائح", "الحلال والحرام"],
    "الوعد والوعيد": ["الوعد", "الوعيد", "أنباء", "مستقر", "يستهزئون"],
}


def _extract_topics(query: str) -> list[str]:
    """Extract relevant topics from query."""
    topics = []
    for topic, keywords in _TOPIC_KEYWORDS.items():
        for kw in keywords:
            if kw in query:
                topics.append(topic)
                break
    return topics


# --- Main API ---


def analyze_query(query: str, default_surah: int = 6) -> QueryAnalysis:
    """
    Analyze a user question and extract structured information.

    Args:
        query: The user's question in Arabic or English.
        default_surah: Default surah number when no surah is specified (6 = Al-An'am).

    Returns:
        QueryAnalysis with verse refs, topics, query type, and search keywords.
    """
    verse_refs = _extract_verse_refs(query, default_surah)
    query_type = _detect_query_type(query, verse_refs)
    topics = _extract_topics(query)

    # Search keywords = topics + significant Arabic words
    keywords = list(topics)

    # Check if needs external knowledge (comparison with other surahs, general questions)
    needs_external = query_type in (QueryType.COMPARISON, QueryType.GENERAL)

    return QueryAnalysis(
        original_query=query,
        verse_refs=verse_refs,
        topics=topics,
        query_type=query_type,
        search_keywords_ar=keywords,
        needs_external_knowledge=needs_external,
    )
