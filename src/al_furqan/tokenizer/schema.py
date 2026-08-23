"""Token schema definitions for the multi-level Quran tokenizer.

These dataclasses define the output format of the tokenizer.  Every verse
in the mushaf produces one ``VerseTokens`` object containing word-level,
root-level, semantic, logic, and transition token sequences, all scored at
certainty=1.0.

The tokenizer deliberately omits phonetic/tajweed encoding.  The training
signal must teach the LLM *how* the Quran transitions between ideas and
maintains logical robustness — not how it sounds.  Mimicking the Quran's
phonetic form is forbidden; learning its reasoning architecture is the goal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# ---------------------------------------------------------------------------
# Morphological types
# ---------------------------------------------------------------------------


class PartOfSpeech(str, Enum):
    """Arabic part-of-speech tags (aligned with Quranic Arabic Corpus)."""

    NOUN = "N"  # اسم
    PROPER_NOUN = "PN"  # اسم علم
    VERB = "V"  # فعل
    PARTICLE = "PRT"  # حرف
    ADJECTIVE = "ADJ"  # صفة
    PRONOUN = "PRON"  # ضمير
    DEMONSTRATIVE = "DEM"  # اسم إشارة
    RELATIVE = "REL"  # اسم موصول
    PREPOSITION = "PREP"  # حرف جر
    CONJUNCTION = "CONJ"  # حرف عطف
    INTERJECTION = "INTJ"  # اسم فعل
    VOCATIVE = "VOC"  # حرف نداء
    NEGATIVE = "NEG"  # حرف نفي
    CONDITIONAL = "COND"  # أداة شرط
    INTERROGATIVE = "INT"  # أداة استفهام
    EMPHATIC = "EMPH"  # حرف توكيد
    UNKNOWN = "UNK"


class VerbForm(str, Enum):
    """Arabic verb forms (أوزان الفعل)."""

    I = "I"  # فَعَلَ  # noqa: E741
    II = "II"  # فَعَّلَ
    III = "III"  # فَاعَلَ
    IV = "IV"  # أَفْعَلَ
    V = "V"  # تَفَعَّلَ
    VI = "VI"  # تَفَاعَلَ
    VII = "VII"  # اِنْفَعَلَ
    VIII = "VIII"  # اِفْتَعَلَ
    IX = "IX"  # اِفْعَلَّ
    X = "X"  # اِسْتَفْعَلَ
    NONE = "NONE"  # non-verb


class TransitionType(str, Enum):
    """How the Quran moves from one idea to the next."""

    CONTINUATION = "continuation"  # same idea, elaboration (تفصيل)
    PIVOT = "pivot"  # topic shift via connector (انتقال)
    CONTRAST = "contrast"  # opposing idea introduced (مقابلة)
    ESCALATION = "escalation"  # same theme, intensified (تصعيد)
    CONCLUSION = "conclusion"  # wrapping / summarizing (خلاصة)
    EVIDENCE_SHIFT = "evidence_shift"  # from claim to evidence (استدلال)
    PARENTHETICAL = "parenthetical"  # aside, then return (اعتراض)
    CALLBACK = "callback"  # echoing an earlier idea (رد العجز على الصدر)
    NEW_SCENE = "new_scene"  # narrative scene change (مشهد جديد)
    QUESTION_ANSWER = "question_answer"  # rhetorical Q then answer (سؤال وجواب)
    NONE = "none"


class ReasoningPattern(str, Enum):
    """Reasoning patterns found in Quranic discourse."""

    DEDUCTIVE = "deductive"  # premise → conclusion
    REDUCTIO = "reductio"  # assume P → contradiction → ¬P
    ANALOGICAL = "analogical"  # known → mapping → unknown
    SOCRATIC = "socratic"  # question → self-derived answer
    EVIDENCE_FIRST = "evidence_first"  # evidence → conclusion → challenge
    IMPERATIVE = "imperative"  # direct command with rationale
    NARRATIVE = "narrative"  # story → moral extraction
    CONTRAST = "contrast"  # X vs Y → conclusion
    OATH = "oath"  # oath → assertion (قسم)
    RHETORICAL = "rhetorical"  # rhetorical question (استفهام إنكاري)
    CONDITIONAL = "conditional"  # if/when → then (شرط)
    NONE = "none"


class SemanticField(str, Enum):
    """High-level semantic fields for meaning grouping."""

    DIVINITY = "divinity"  # الألوهية — names/attributes of Allah
    WORSHIP = "worship"  # العبادة — prayer, fasting, hajj
    BELIEF = "belief"  # الإيمان — faith, unseen, hereafter
    MORALITY = "morality"  # الأخلاق — character, ethics
    LEGISLATION = "legislation"  # التشريع — laws, rulings
    CREATION = "creation"  # الخلق — natural world, signs
    NARRATIVE = "narrative"  # القصص — prophets, history
    ESCHATOLOGY = "eschatology"  # الآخرة — resurrection, judgment
    SOCIAL = "social"  # المعاملات — family, commerce
    KNOWLEDGE = "knowledge"  # العلم — reason, learning
    MERCY = "mercy"  # الرحمة — compassion, forgiveness
    JUSTICE = "justice"  # العدل — equity, punishment
    GUIDANCE = "guidance"  # الهداية — right path, misguidance
    NONE = "none"


class PatternMeaning(str, Enum):
    """What the morphological pattern (wazn) adds to the root meaning."""

    BASE_ACTION = "base_action"  # فَعَلَ — the root action itself
    INTENSIVE = "intensive"  # فَعَّلَ — intensified / causative
    MUTUAL = "mutual"  # فَاعَلَ — reciprocal / mutual action
    CAUSATIVE = "causative"  # أَفْعَلَ — making someone do the action
    REFLEXIVE = "reflexive"  # تَفَعَّلَ — doing it to oneself
    COOPERATIVE = "cooperative"  # تَفَاعَلَ — doing it together
    PASSIVE_BECOME = "passive_become"  # اِنْفَعَلَ — becoming affected
    SEEKING = "seeking"  # اِفْتَعَلَ — seeking/striving for
    QUALITY = "quality"  # اِفْعَلَّ — acquiring a quality (colors/defects)
    REQUEST = "request"  # اِسْتَفْعَلَ — requesting/considering
    AGENT = "agent"  # فَاعِل — the doer (active participle)
    PATIENT = "patient"  # مَفْعُول — the one acted upon (passive participle)
    INSTRUMENT = "instrument"  # مِفْعَال — tool/instrument
    PLACE = "place"  # مَفْعَل — place of action
    PERMANENT_QUALITY = "permanent_quality"  # فَعِيل — permanent/inherent quality
    EXCESSIVE = "excessive"  # فَعَّال — one who does excessively
    COMPARATIVE = "comparative"  # أَفْعَل — comparative/superlative
    ABSTRACT_NOUN = "abstract_noun"  # فُعُول / فِعَال — abstract concept
    NONE = "none"


class LogicOperator(str, Enum):
    """Logical operators and discourse connectors in Quranic Arabic."""

    # --- Conjunctive ---
    CONJUNCTION = "conjunction"  # وَ — and (simple addition)
    SEQUENCE = "sequence"  # ثُمَّ — then (ordered sequence)
    CONSEQUENCE = "consequence"  # فَ — so/then (cause → effect)
    DISJUNCTION = "disjunction"  # أَوْ — or (alternative)
    ADVERSATIVE = "adversative"  # لٰكِنْ / بَلْ — but/rather (contrast)

    # --- Conditional ---
    CONDITION = "condition"  # إِنْ / إِذَا — if/when
    CONDITION_RESPONSE = "condition_response"  # فَ / جواب الشرط — then (apodosis)
    HYPOTHETICAL = "hypothetical"  # لَوْ — if (counterfactual)

    # --- Scope / quantification ---
    UNIVERSAL = "universal"  # كُلّ — all / every
    RESTRICTION = "restriction"  # إِنَّمَا / مَا...إِلَّا — only / nothing except
    EXCEPTION = "exception"  # إِلَّا — except
    NEGATION = "negation"  # لَا / مَا / لَمْ / لَنْ — not

    # --- Evidential ---
    EMPHASIS = "emphasis"  # إِنَّ / قَدْ / لَ — indeed/certainly
    OATH = "oath"  # وَ (القسم) — I swear by
    RESULT = "result"  # لِذٰلِكَ / إِذًا — therefore

    # --- Rhetorical ---
    QUESTION = "question"  # أ / هَلْ — interrogative
    RHETORICAL_DENIAL = "rhetorical_denial"  # أَفَلَا — do they not...?
    COMMAND = "command"  # imperative verb
    PROHIBITION = "prohibition"  # لَا + jussive — do not
    EXHORTATION = "exhortation"  # لَعَلَّ — perhaps / so that

    # --- Referential ---
    ANAPHORA = "anaphora"  # هُوَ / هُمْ — pronoun reference back
    CATAPHORA = "cataphora"  # forward reference
    DEMONSTRATIVE = "demonstrative"  # ذٰلِكَ / هٰذَا — pointing

    NONE = "none"


class SyntacticRole(str, Enum):
    """Syntactic (i'rab) roles in Quranic Arabic."""

    SUBJECT = "subject"  # فاعل
    OBJECT = "object"  # مفعول به
    PREDICATE = "predicate"  # خبر
    TOPIC = "topic"  # مبتدأ
    ADJUNCT = "adjunct"  # حال
    ADVERBIAL = "adverbial"  # ظرف
    SPECIFICATION = "specification"  # تمييز
    ATTRIBUTE = "attribute"  # نعت/صفة
    APPOSITION = "apposition"  # بدل
    VOCATIVE = "vocative"  # منادى
    EXCEPTION = "exception"  # مستثنى
    GENITIVE = "genitive"  # مضاف إليه
    CONNECTOR = "connector"  # أداة (حرف)
    NONE = "none"


# ---------------------------------------------------------------------------
# Token dataclasses
# ---------------------------------------------------------------------------


@dataclass
class WordToken:
    """Level 1: Word-level token in mushaf order."""

    position: int  # 0-indexed position within the verse
    surface: str  # exact surface form with diacritics
    surface_clean: str  # without diacritics (for matching)
    is_stop_word: bool = False  # particles, prepositions, etc.


@dataclass
class RootToken:
    """Level 2: Morphological root-level token."""

    position: int  # same as WordToken.position
    surface: str  # surface form (reference)
    root: str  # trilateral/quadrilateral root (e.g., "ك-ت-ب")
    root_letters: list[str] = field(default_factory=list)  # ["ك", "ت", "ب"]
    pattern: str = ""  # morphological pattern/wazn (e.g., "فَعَلَ")
    pos: str = "UNK"  # part of speech
    verb_form: str = "NONE"  # verb form (I-X) if applicable
    prefixes: list[str] = field(default_factory=list)  # e.g., ["وَ", "الْ"]
    suffixes: list[str] = field(default_factory=list)  # e.g., ["هُمْ", "ونَ"]
    lemma: str = ""  # dictionary form


@dataclass
class SemanticToken:
    """Level 2B: Semantic meaning expansion token.

    Captures what the morphological form *means* — not just what it's made of.
    This is the layer that teaches the model conceptual consistency and
    meaning density.
    """

    position: int  # same as WordToken.position
    surface: str  # surface form (reference)
    semantic_field: str = "none"  # high-level meaning category (SemanticField)
    pattern_meaning: str = "none"  # what the wazn adds to the root (PatternMeaning)
    syntactic_role: str = "none"  # i'rab role in the sentence (SyntacticRole)
    referent: str = (
        ""  # what a pronoun/demonstrative points to (verse_key:position or "")
    )
    scope: str = ""  # "word" | "clause" | "verse" | "passage" — what this word governs
    meaning_ar: str = ""  # contextual meaning in Arabic (from tafsir)
    meaning_en: str = ""  # contextual meaning in English


@dataclass
class LogicToken:
    """Level 2C: Logical operator and discourse connector token.

    Captures the *reasoning structure* — how words connect logically.
    This is the layer that teaches the model how to reason: what's a premise,
    what's a conclusion, what's a condition, what's an exception.
    """

    position: int  # same as WordToken.position
    surface: str  # surface form
    operator: str = "none"  # LogicOperator type
    role_in_argument: str = ""  # "premise" | "evidence" | "conclusion" | "condition" |
    # "response" | "exception" | "emphasis" | "connector" | ""
    connects_to: list[int] = field(
        default_factory=list
    )  # positions of words this logically links to
    negation_scope: list[int] = field(
        default_factory=list
    )  # positions negated by this word
    emphasis_level: float = 0.0  # 0.0 = neutral, 1.0 = maximum emphasis (إنَّ + لَ + قَد)


@dataclass
class TransitionToken:
    """Level 3: Idea-transition token.

    Captures *how* the discourse moves from one idea to the next.
    This is the layer that teaches the model the Quran's signature smooth
    transitions and logical robustness — the core training signal.
    """

    position: int  # same as WordToken.position
    surface: str  # surface form
    transition_type: str = "none"  # TransitionType — how the idea shifts here
    source_idea: str = ""  # semantic field / topic BEFORE this point
    target_idea: str = ""  # semantic field / topic AFTER this point
    smoothness: float = 1.0  # 0.0 = abrupt, 1.0 = perfectly smooth (Quran always 1.0)
    discourse_depth: int = 0  # nesting level of the current argument/idea
    returns_to: int = -1  # position of an earlier idea this echoes (-1 = none)


# ---------------------------------------------------------------------------
# Verse-level container
# ---------------------------------------------------------------------------


@dataclass
class VerseTokens:
    """Complete three-level tokenization of a single verse."""

    surah: int
    ayah: int
    verse_key: str  # "2:255"
    text_ar: str  # full verse text
    text_en: str = ""  # english translation

    word_tokens: list[WordToken] = field(default_factory=list)
    root_tokens: list[RootToken] = field(default_factory=list)
    semantic_tokens: list[SemanticToken] = field(default_factory=list)
    logic_tokens: list[LogicToken] = field(default_factory=list)
    transition_tokens: list[TransitionToken] = field(default_factory=list)

    # Verse-level metadata
    word_count: int = 0
    unique_roots: int = 0
    reasoning_pattern: str = "none"

    # Certainty — always 1.0 for Quran (ground truth)
    certainty: float = 1.0

    # Mushaf ordering
    juz: int = 0
    page: int = 0
    position_in_surah: int = 0  # 0-indexed ayah position
    position_in_mushaf: int = 0  # global sequential position (0-6235)

    def to_dict(self) -> dict:
        """Serialize to dict for JSON/ES storage."""
        return {
            "surah": self.surah,
            "ayah": self.ayah,
            "verse_key": self.verse_key,
            "text_ar": self.text_ar,
            "text_en": self.text_en,
            "word_tokens": [
                {
                    "position": wt.position,
                    "surface": wt.surface,
                    "surface_clean": wt.surface_clean,
                    "is_stop_word": wt.is_stop_word,
                }
                for wt in self.word_tokens
            ],
            "root_tokens": [
                {
                    "position": rt.position,
                    "surface": rt.surface,
                    "root": rt.root,
                    "root_letters": rt.root_letters,
                    "pattern": rt.pattern,
                    "pos": rt.pos,
                    "verb_form": rt.verb_form,
                    "prefixes": rt.prefixes,
                    "suffixes": rt.suffixes,
                    "lemma": rt.lemma,
                }
                for rt in self.root_tokens
            ],
            "semantic_tokens": [
                {
                    "position": st.position,
                    "surface": st.surface,
                    "semantic_field": st.semantic_field,
                    "pattern_meaning": st.pattern_meaning,
                    "syntactic_role": st.syntactic_role,
                    "referent": st.referent,
                    "scope": st.scope,
                    "meaning_ar": st.meaning_ar,
                    "meaning_en": st.meaning_en,
                }
                for st in self.semantic_tokens
            ],
            "logic_tokens": [
                {
                    "position": lt.position,
                    "surface": lt.surface,
                    "operator": lt.operator,
                    "role_in_argument": lt.role_in_argument,
                    "connects_to": lt.connects_to,
                    "negation_scope": lt.negation_scope,
                    "emphasis_level": lt.emphasis_level,
                }
                for lt in self.logic_tokens
            ],
            "transition_tokens": [
                {
                    "position": tt.position,
                    "surface": tt.surface,
                    "transition_type": tt.transition_type,
                    "source_idea": tt.source_idea,
                    "target_idea": tt.target_idea,
                    "smoothness": tt.smoothness,
                    "discourse_depth": tt.discourse_depth,
                    "returns_to": tt.returns_to,
                }
                for tt in self.transition_tokens
            ],
            "word_count": self.word_count,
            "unique_roots": self.unique_roots,
            "reasoning_pattern": self.reasoning_pattern,
            "certainty": self.certainty,
            "juz": self.juz,
            "page": self.page,
            "position_in_surah": self.position_in_surah,
            "position_in_mushaf": self.position_in_mushaf,
        }
