"""Arabic morphological analyzer for Quranic text.

Two-tier lookup strategy:
    1. **QAC Corpus** (primary) — Expert-annotated morphological data from the
       Quranic Arabic Corpus (corpus.quran.com), extracted from the project's
       PostgreSQL dump via ``qac_extractor.py``.  Provides 100% accurate root,
       lemma, POS, and verb form for every word in the Quran.

    2. **Rule-based fallback** — Algorithmic root extraction for words not
       found in the QAC data (e.g., non-Quranic text, or when QAC data is
       not yet extracted).

QAC data is loaded lazily on first use from ``data/quran/qac_morphology.json``.
Generate it with:  ``python -m al_furqan.tokenizer.qac_extractor``
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Diacritics and normalization
# ---------------------------------------------------------------------------

_DIACRITICS = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670"
    r"\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED]"
)
_ALEF_VARIANTS = re.compile(r"[إأآٱ]")


def strip_diacritics(text: str) -> str:
    """Remove all Arabic diacritical marks."""
    return _DIACRITICS.sub("", text)


def normalize_alef(text: str) -> str:
    """Normalize alef variants to plain alef."""
    return _ALEF_VARIANTS.sub("ا", text)


def clean_word(word: str) -> str:
    """Strip diacritics and normalize for root extraction."""
    w = strip_diacritics(word)
    w = normalize_alef(w)
    w = w.replace("ة", "ه").replace("ى", "ي").replace("\u0640", "")
    # Strip BOM and zero-width characters
    w = w.replace("\ufeff", "").replace("\u200b", "").replace("\u200c", "")
    return w


# ---------------------------------------------------------------------------
# Prefix / suffix stripping
# ---------------------------------------------------------------------------

# Ordered from longest to shortest to avoid partial matches
PREFIXES = [
    "وبال",
    "فبال",
    "وال",
    "فال",
    "بال",
    "كال",
    "لل",
    "وب",
    "فب",
    "ول",
    "فل",
    "وك",
    "فك",
    "ال",
    "و",
    "ف",
    "ب",
    "ل",
    "ك",
    "س",
]

SUFFIXES = [
    "كموها",
    "تموها",
    "وهم",
    "هما",
    "كم",
    "هم",
    "نا",
    "ها",
    "ون",
    "ين",
    "ات",
    "تم",
    "وا",
    "ه",
    "ك",
    "ي",
    "ت",
    "ا",
    "ن",
]

# Arabic stop words (particles that have no root)
STOP_WORDS = {
    "في",
    "من",
    "الى",
    "على",
    "عن",
    "ان",
    "لا",
    "ما",
    "يا",
    "لم",
    "لن",
    "قد",
    "اذا",
    "اذ",
    "ثم",
    "او",
    "بل",
    "هل",
    "كل",
    "هذا",
    "هذه",
    "ذلك",
    "تلك",
    "الذي",
    "التي",
    "الذين",
    "اللذين",
    "هو",
    "هي",
    "هم",
    "هن",
    "نحن",
    "انتم",
    "انت",
    "انا",
    "الا",
}


def strip_prefixes(word: str) -> tuple[list[str], str]:
    """Strip known prefixes. Returns (list of stripped prefixes, stem)."""
    found = []
    for prefix in PREFIXES:
        if word.startswith(prefix) and len(word) - len(prefix) >= 2:
            found.append(prefix)
            word = word[len(prefix) :]
            break  # only strip one layer of prefix
    return found, word


def strip_suffixes(word: str) -> tuple[str, list[str]]:
    """Strip known suffixes. Returns (stem, list of stripped suffixes)."""
    found = []
    for suffix in SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 2:
            found.append(suffix)
            word = word[: -len(suffix)]
            break  # only strip one layer of suffix
    return word, found


# ---------------------------------------------------------------------------
# Root extraction
# ---------------------------------------------------------------------------

# Common trilateral patterns (wazn → root letter positions in the stem)
# Position indices into the stripped stem where root letters appear
_TRILITERAL_PATTERNS = [
    # pattern, wazn_name, stem_template (F=root1, A=root2, L=root3)
    ("FAL", "فَعَلَ", 3),  # basic: 3 letters = root
    ("FAAL", "فَاعَلَ", 4),  # 3rd form: letter 2 is zaa'id
    ("AFAL", "أَفْعَلَ", 4),  # 4th form: initial ا is zaa'id
    ("TAFAL", "تَفَعَّلَ", 5),  # 5th form
    ("ANFAL", "اِنْفَعَلَ", 5),  # 7th form
    ("AFTAL", "اِفْتَعَلَ", 5),  # 8th form
    ("STFAL", "اِسْتَفْعَلَ", 6),  # 10th form
]


# Known irregular words whose roots can't be extracted algorithmically.
# Maps cleaned form → (root_string, root_letters, pattern, pos)
KNOWN_WORDS: dict[str, tuple[str, list[str], str, str]] = {
    "الله": ("أ-ل-ه", ["أ", "ل", "ه"], "فَعَال", "PN"),
    "لله": ("أ-ل-ه", ["أ", "ل", "ه"], "فَعَال", "PN"),
    "بسم": ("س-م-و", ["س", "م", "و"], "فِعْل", "N"),
    "رب": ("ر-ب-ب", ["ر", "ب", "ب"], "فَعّ", "N"),
    "ربك": ("ر-ب-ب", ["ر", "ب", "ب"], "فَعّ", "N"),
    "ربهم": ("ر-ب-ب", ["ر", "ب", "ب"], "فَعّ", "N"),
    "ربنا": ("ر-ب-ب", ["ر", "ب", "ب"], "فَعّ", "N"),
    "الناس": ("ن-و-س", ["ن", "و", "س"], "فَعَل", "N"),
    "ناس": ("ن-و-س", ["ن", "و", "س"], "فَعَل", "N"),
    "الرحمن": ("ر-ح-م", ["ر", "ح", "م"], "فَعْلَان", "ADJ"),
    "الرحيم": ("ر-ح-م", ["ر", "ح", "م"], "فَعِيل", "ADJ"),
    "رحمن": ("ر-ح-م", ["ر", "ح", "م"], "فَعْلَان", "ADJ"),
    "رحيم": ("ر-ح-م", ["ر", "ح", "م"], "فَعِيل", "ADJ"),
    "رحمه": ("ر-ح-م", ["ر", "ح", "م"], "فَعْلَة", "N"),
    "الحمد": ("ح-م-د", ["ح", "م", "د"], "فَعْل", "N"),
    "العلمين": ("ع-ل-م", ["ع", "ل", "م"], "فَاعَلِين", "N"),
}


def extract_root(word: str) -> tuple[str, list[str], str]:
    """Extract the trilateral root from an Arabic word.

    Returns:
        (root_string, root_letters, pattern)
        e.g., ("ك-ت-ب", ["ك", "ت", "ب"], "فَعَلَ")
    """
    cleaned = clean_word(word)

    # Check known irregular words first
    if cleaned in KNOWN_WORDS:
        r, rl, p, _ = KNOWN_WORDS[cleaned]
        return r, rl, p

    # Check if it's a stop word (no root)
    if cleaned in STOP_WORDS:
        return ("", [], "particle")

    # Strip affixes
    _prefixes, stem = strip_prefixes(cleaned)
    stem, _suffixes = strip_suffixes(stem)

    # Remove any remaining alef/waw/yaa that are pattern letters (not root)
    # but only if we still have >3 letters
    if len(stem) > 3:
        # Remove alef wasla at start
        if stem.startswith("ا") and len(stem) > 3:
            stem = stem[1:]
        # Remove taa prefix (form V, VI)
        if stem.startswith("ت") and len(stem) > 3:
            stem = stem[1:]
        # Remove nun prefix (form VII)
        if stem.startswith("ن") and len(stem) > 3:
            stem = stem[1:]

    # Handle doubled middle letter (form II, V): فعّل → فعل
    if len(stem) >= 4:
        for i in range(len(stem) - 1):
            if stem[i] == stem[i + 1]:
                stem = stem[: i + 1] + stem[i + 2 :]
                break

    # Handle weak roots (middle waw/yaa that may have been elided)
    # After all stripping, we should have 3 root letters
    root_letters = list(stem[:3]) if len(stem) >= 3 else list(stem)

    # Determine pattern based on original stem length before stripping
    original_len = len(clean_word(word))
    if original_len <= 3:
        pattern = "فَعَلَ"
    elif original_len == 4:
        pattern = "فَعَّلَ"
    elif original_len <= 6:
        pattern = "تَفَعَّلَ"
    else:
        pattern = "اِسْتَفْعَلَ"

    root_str = "-".join(root_letters) if root_letters else ""
    return root_str, root_letters, pattern


# ---------------------------------------------------------------------------
# Part of speech detection (rule-based)
# ---------------------------------------------------------------------------

_VERB_PREFIXES = {"ي", "ت", "ن", "ا"}  # imperfect verb prefixes
_VERB_SUFFIXES = {"وا", "ون", "ين", "نا", "تم", "ت"}


def detect_pos(word: str, root: str) -> str:
    """Detect part of speech from surface form."""
    cleaned = clean_word(word)

    # Check known words first
    if cleaned in KNOWN_WORDS:
        return KNOWN_WORDS[cleaned][3]

    if cleaned in STOP_WORDS:
        # Distinguish particle subtypes
        if cleaned in {"في", "من", "الى", "على", "عن"}:
            return "PREP"
        if cleaned in {"و", "ف", "ثم", "او", "بل"}:
            return "CONJ"
        if cleaned in {"لا", "لم", "لن", "ما"}:
            return "NEG"
        if cleaned in {"هل", "ا"}:
            return "INT"
        if cleaned in {"ان", "انما"}:
            return "EMPH"
        if cleaned in {"هذا", "هذه", "ذلك", "تلك"}:
            return "DEM"
        if cleaned in {"الذي", "التي", "الذين"}:
            return "REL"
        if cleaned in {"هو", "هي", "هم", "هن", "نحن", "انتم", "انت", "انا"}:
            return "PRON"
        if cleaned == "يا":
            return "VOC"
        if cleaned in {"اذا", "لو", "ان"}:
            return "COND"
        return "PRT"

    # Check for verb markers
    if not root:
        return "UNK"

    # Imperfect verb prefix check
    if cleaned and cleaned[0] in _VERB_PREFIXES:
        stem = cleaned[1:]
        if any(stem.endswith(s) for s in _VERB_SUFFIXES):
            return "V"
        if len(stem) >= 2:
            return "V"

    # Past tense verb suffixes
    if any(cleaned.endswith(s) for s in ["وا", "تم", "نا", "ت"]):
        return "V"

    # Words starting with م often are nouns (مفعول، مكتوب، etc.)
    if cleaned.startswith("م") and len(cleaned) >= 4:
        return "N"

    # Words with ال are typically nouns/adjectives
    if clean_word(word).startswith("ال") or word.startswith("ال"):
        return "N"

    # Default: noun (most common in Quran)
    return "N"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@dataclass
class MorphAnalysis:
    """Result of morphological analysis for a single word."""

    surface: str
    surface_clean: str
    root: str
    root_letters: list[str]
    pattern: str
    pos: str
    prefixes: list[str]
    suffixes: list[str]
    is_stop_word: bool


# ---------------------------------------------------------------------------
# QAC Corpus Lookup (Elasticsearch-backed)
# ---------------------------------------------------------------------------

_QAC_INDEX = "furqan_qac_morphology"

# POS key mapping from QAC tags to our POS enum
_QAC_POS_MAP = {
    "N": "N",
    "PN": "PN",
    "V": "V",
    "P": "PRT",
    "ADJ": "ADJ",
    "PRON": "PRON",
    "DEM": "DEM",
    "REL": "REL",
    "CONJ": "CONJ",
    "INTJ": "INTJ",
    "NEG": "NEG",
    "COND": "COND",
    "INT": "INT",
    "EMPH": "EMPH",
    "VOC": "VOC",
    "DET": "PRT",
    "PREP": "PREP",
}


class QACLookup:
    """Elasticsearch-backed QAC morphological corpus lookup.

    Queries the ``furqan_qac_morphology`` index for verse-level
    word annotations.  Falls back gracefully if ES is unavailable
    or the index doesn't exist.
    """

    def __init__(self, es=None, index: str = _QAC_INDEX) -> None:
        self._es = es
        self._index = index
        self._checked = False
        self._available = False

    def _ensure_client(self) -> bool:
        """Lazily create ES client and check index existence."""
        if self._checked:
            return self._available
        self._checked = True

        if self._es is None:
            try:
                from al_furqan.kb.es.client import create_es_client

                self._es = create_es_client()
            except Exception as exc:
                logger.debug("ES client not available — QAC disabled: %s", exc)
                self._available = False
                return False

        try:
            self._available = self._es.indices.exists(index=self._index)
            if self._available:
                count = self._es.count(index=self._index)["count"]
                logger.info(
                    "QAC corpus available in ES: %s (%d verses)", self._index, count
                )
            else:
                logger.debug(
                    "QAC index %s not found — using rule-based fallback", self._index
                )
        except Exception as exc:
            logger.debug("ES check failed — QAC disabled: %s", exc)
            self._available = False

        return self._available

    @property
    def available(self) -> bool:
        """True if QAC data is available in ES."""
        return self._ensure_client()

    def lookup(self, verse_key: str, position: int) -> MorphAnalysis | None:
        """Look up a word by verse_key and position (1-indexed)."""
        if not self._ensure_client():
            return None

        try:
            doc = self._es.get(index=self._index, id=verse_key)
            words = doc["_source"].get("words", [])
            for w in words:
                if w.get("position") == position:
                    return self._to_morph(w)
        except Exception:
            pass
        return None

    def lookup_verse(self, verse_key: str) -> list[MorphAnalysis]:
        """Return all word annotations for a verse, in order."""
        if not self._ensure_client():
            return []

        try:
            doc = self._es.get(index=self._index, id=verse_key)
            words = doc["_source"].get("words", [])
            return [self._to_morph(w) for w in words]
        except Exception:
            return []

    @staticmethod
    def _to_morph(w: dict) -> MorphAnalysis:
        """Convert a QAC word dict to MorphAnalysis."""
        root = w.get("root", "")
        root_letters = root.split("-") if root else []

        pos_tags = w.get("pos_tags", [])
        pos = "UNK"
        for tag in pos_tags:
            tag_upper = tag.strip().upper()
            if tag_upper in _QAC_POS_MAP:
                pos = _QAC_POS_MAP[tag_upper]
                break
            if tag_upper in ("PREF", "SUFF"):
                continue

        prefixes = []
        suffixes = []
        for seg in w.get("segments", []):
            seg_tags = (seg.get("pos_tags") or "").split(",")
            if "PREF" in seg_tags:
                prefixes.append(seg.get("text", ""))
            elif "SUFF" in seg_tags:
                suffixes.append(seg.get("text", ""))

        is_stop = pos in (
            "PRT",
            "PREP",
            "CONJ",
            "NEG",
            "INT",
            "EMPH",
            "VOC",
            "COND",
            "DEM",
            "REL",
            "PRON",
        )

        return MorphAnalysis(
            surface=w.get("text_uthmani", ""),
            surface_clean=w.get("text_clean", ""),
            root=root,
            root_letters=root_letters,
            pattern=w.get("verb_form", "") or "",
            pos=pos,
            prefixes=prefixes,
            suffixes=suffixes,
            is_stop_word=is_stop,
        )


# Module-level singleton — lazily connects to ES
_qac = QACLookup()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def analyze_word(word: str, verse_key: str = "", position: int = 0) -> MorphAnalysis:
    """Perform full morphological analysis on a single Arabic word.

    Args:
        word: Arabic word (with or without diacritics).
        verse_key: Optional verse reference (e.g., "1:1") for QAC lookup.
        position: Optional 1-indexed word position within the verse.

    If verse_key and position are provided, attempts QAC corpus lookup first.
    Falls back to rule-based extraction if QAC data is unavailable or the
    word is not found.
    """
    # Tier 1: QAC corpus lookup
    if verse_key and position > 0:
        qac_result = _qac.lookup(verse_key, position)
        if qac_result is not None:
            return qac_result

    # Tier 2: Rule-based fallback
    cleaned = clean_word(word)
    root_str, root_letters, pattern = extract_root(word)
    pos = detect_pos(word, root_str)
    is_stop = cleaned in STOP_WORDS

    prefixes, stem = strip_prefixes(cleaned)
    _, suffixes = strip_suffixes(stem)

    return MorphAnalysis(
        surface=word,
        surface_clean=cleaned,
        root=root_str,
        root_letters=root_letters,
        pattern=pattern if not is_stop else "",
        pos=pos,
        prefixes=prefixes,
        suffixes=suffixes,
        is_stop_word=is_stop,
    )


def analyze_verse(verse_key: str, text: str) -> list[MorphAnalysis]:
    """Analyze all words in a verse, using QAC data when available.

    This is the preferred entry point for Quranic text — it passes
    verse_key and position to each word analysis for optimal QAC lookup.
    """
    # Try full QAC verse lookup first
    if _qac.available:
        qac_results = _qac.lookup_verse(verse_key)
        if qac_results:
            return qac_results

    # Fallback: word-by-word rule-based analysis
    import re

    words = [w for w in re.split(r"\s+", text.strip()) if w]
    return [
        analyze_word(w, verse_key=verse_key, position=i + 1)
        for i, w in enumerate(words)
    ]
