"""Semantic, logical, and transition analysis for Quranic text.

Level 2B: Semantic meaning expansion
    - Maps roots to semantic fields (what domain of meaning)
    - Maps patterns (wazn) to pattern meanings (how the root meaning is modified)
    - Detects syntactic roles from POS and context

Level 2C: Logical operators and discourse structure
    - Identifies logical connectors (وَ، فَ، ثُمَّ، لٰكِنْ, etc.)
    - Classifies their function in reasoning (conjunction, consequence, restriction)
    - Detects emphasis particles and their scope
    - Identifies argument structure (premise, evidence, conclusion)

Level 3: Idea transitions
    - Detects how the discourse moves from one idea to the next
    - Classifies the transition type (pivot, contrast, escalation, etc.)
    - Tracks semantic field shifts and discourse depth
    - This is the core training signal: smooth logical transitions
"""

from __future__ import annotations

from al_furqan.tokenizer.morphology import MorphAnalysis, clean_word
from al_furqan.tokenizer.schema import (
    LogicToken,
    SemanticToken,
    TransitionToken,
)

# ---------------------------------------------------------------------------
# Root → semantic field mapping
# ---------------------------------------------------------------------------
# Maps common Quranic roots to their primary semantic field.
# This is a curated subset — production would use the full QAC topic data.

_ROOT_SEMANTIC_FIELD: dict[str, str] = {
    # Divinity
    "أ-ل-ه": "divinity",
    "ر-ب-ب": "divinity",
    "ق-د-س": "divinity",
    "س-ب-ح": "divinity",
    "ح-م-د": "divinity",
    "ع-ظ-م": "divinity",
    "ع-ل-و": "divinity",
    "م-ل-ك": "divinity",
    # Mercy
    "ر-ح-م": "mercy",
    "غ-ف-ر": "mercy",
    "ع-ف-و": "mercy",
    "ت-و-ب": "mercy",
    "ر-أ-ف": "mercy",
    # Worship
    "ع-ب-د": "worship",
    "ص-ل-و": "worship",
    "ز-ك-و": "worship",
    "ص-و-م": "worship",
    "ح-ج-ج": "worship",
    "س-ج-د": "worship",
    "ر-ك-ع": "worship",
    "ذ-ك-ر": "worship",
    # Belief
    "أ-م-ن": "belief",
    "ك-ف-ر": "belief",
    "ش-ر-ك": "belief",
    "ش-ه-د": "belief",
    "ي-ق-ن": "belief",
    "غ-ي-ب": "belief",
    # Guidance
    "ه-د-ي": "guidance",
    "ض-ل-ل": "guidance",
    "ص-ر-ط": "guidance",
    "ن-و-ر": "guidance",
    "ظ-ل-م": "guidance",
    # Knowledge
    "ع-ل-م": "knowledge",
    "ف-ق-ه": "knowledge",
    "ع-ق-ل": "knowledge",
    "ف-ك-ر": "knowledge",
    "ح-ك-م": "knowledge",
    "ب-ص-ر": "knowledge",
    # Justice
    "ع-د-ل": "justice",
    "ق-س-ط": "justice",
    "ح-ق-ق": "justice",
    "ج-ز-ي": "justice",
    "ع-ق-ب": "justice",
    "ح-س-ب": "justice",
    # Creation
    # Note: خ-ل-ق maps to both "creation" (خَلَقَ verb) and "morality" (خُلُق noun);
    # diacritics-level disambiguation is not yet supported, so we use the primary domain.
    "خ-ل-ق": "creation",
    "ب-د-ع": "creation",
    "ف-ط-ر": "creation",
    "ج-ع-ل": "creation",
    "س-م-و": "creation",
    "أ-ر-ض": "creation",
    # Legislation
    "ح-ر-م": "legislation",
    "ح-ل-ل": "legislation",
    "أ-م-ر": "legislation",
    "ن-ه-ي": "legislation",
    "ف-ر-ض": "legislation",
    "ش-ر-ع": "legislation",
    # Social
    "ن-ك-ح": "social",
    "ط-ل-ق": "social",
    "ر-ب-و": "social",
    "ب-ي-ع": "social",
    "ك-ت-ب": "social",
    # Eschatology
    "ب-ع-ث": "eschatology",
    "ح-ش-ر": "eschatology",
    "ج-ن-ن": "eschatology",
    "ن-ر-ر": "eschatology",
    "ع-ذ-ب": "eschatology",
    "ح-ي-ي": "eschatology",
    "م-و-ت": "eschatology",
    "ق-ي-م": "eschatology",
    # Morality
    "ص-ب-ر": "morality",
    "ش-ك-ر": "morality",
    "ب-ر-ر": "morality",
    "ت-ق-و": "morality",
    "ص-د-ق": "morality",
    # Narrative
    "ق-ص-ص": "narrative",
    "ن-ب-أ": "narrative",
    "ر-س-ل": "narrative",
    "ن-ب-و": "narrative",
}

# ---------------------------------------------------------------------------
# Pattern (wazn) → meaning modification
# ---------------------------------------------------------------------------

_PATTERN_MEANING: dict[str, str] = {
    "فَعَلَ": "base_action",
    "فَعَّلَ": "intensive",
    "فَاعَلَ": "mutual",
    "أَفْعَلَ": "causative",
    "تَفَعَّلَ": "reflexive",
    "تَفَاعَلَ": "cooperative",
    "اِنْفَعَلَ": "passive_become",
    "اِفْتَعَلَ": "seeking",
    "اِفْعَلَّ": "quality",
    "اِسْتَفْعَلَ": "request",
    "فَاعِل": "agent",
    "مَفْعُول": "patient",
    "مِفْعَال": "instrument",
    "مَفْعَل": "place",
    "فَعِيل": "permanent_quality",
    "فَعَّال": "excessive",
    "أَفْعَل": "comparative",
    "فَعْل": "abstract_noun",
    "فِعْل": "abstract_noun",
    "فُعُول": "abstract_noun",
    "فِعَال": "abstract_noun",
    "فَعِيلَة": "abstract_noun",
    "فَعْلَان": "permanent_quality",
    "فَاعَلِين": "agent",
    "فَعَال": "abstract_noun",
}


# ---------------------------------------------------------------------------
# Logic operator detection
# ---------------------------------------------------------------------------
# Maps surface particles (cleaned) to their logical function.

_LOGIC_OPERATORS: dict[str, tuple[str, str, float]] = {
    # (operator, role_in_argument, emphasis_level)
    # --- Conjunctive ---
    "و": ("conjunction", "connector", 0.0),
    "ف": ("consequence", "connector", 0.0),
    "ثم": ("sequence", "connector", 0.0),
    "او": ("disjunction", "connector", 0.0),
    "لكن": ("adversative", "connector", 0.0),
    "بل": ("adversative", "connector", 0.2),
    # --- Conditional ---
    "ان": ("condition", "condition", 0.0),
    "اذا": ("condition", "condition", 0.0),
    "لو": ("hypothetical", "condition", 0.0),
    "لولا": ("hypothetical", "condition", 0.0),
    # --- Negation ---
    "لا": ("negation", "connector", 0.0),
    "ما": ("negation", "connector", 0.0),
    "لم": ("negation", "connector", 0.1),
    "لن": ("negation", "connector", 0.2),  # emphatic future negation
    "ليس": ("negation", "connector", 0.1),
    # --- Restriction/exception ---
    "الا": ("exception", "exception", 0.0),
    "انما": ("restriction", "emphasis", 0.5),
    # --- Emphasis ---
    # Note: "ان" (إنَّ emphasis) omitted — same stripped form as conditional "إنْ" above;
    # emphasis detection handled by _EMPHASIS_PARTICLES instead.
    "قد": ("emphasis", "evidence", 0.3),
    # --- Interrogative ---
    "هل": ("question", "premise", 0.0),
    "افلا": ("rhetorical_denial", "premise", 0.4),
    "الم": ("rhetorical_denial", "premise", 0.4),
    # --- Purpose/result ---
    "لعل": ("exhortation", "conclusion", 0.1),
    "كي": ("result", "conclusion", 0.0),
    # --- Demonstrative ---
    "ذلك": ("demonstrative", "connector", 0.0),
    "هذا": ("demonstrative", "connector", 0.0),
    "هذه": ("demonstrative", "connector", 0.0),
    "تلك": ("demonstrative", "connector", 0.0),
}

# Emphasis stacking: these particles add to emphasis_level when combined
_EMPHASIS_PARTICLES = {"ان": 0.4, "ل": 0.2, "قد": 0.2, "انما": 0.5, "لن": 0.3}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def analyze_semantics(
    morph: MorphAnalysis,
    position: int,
) -> SemanticToken:
    """Build a semantic token from morphological analysis."""
    # Semantic field from root
    semantic_field = _ROOT_SEMANTIC_FIELD.get(morph.root, "none")

    # Pattern meaning from wazn
    pattern_meaning = _PATTERN_MEANING.get(morph.pattern, "none")

    # Syntactic role from POS (simplified — full i'rab needs parser)
    if morph.pos == "V":
        syntactic_role = "predicate"
    elif morph.pos == "N" and position == 0:
        syntactic_role = "topic"
    elif morph.pos in ("N", "PN", "ADJ"):
        syntactic_role = "subject"
    elif morph.pos in ("PREP", "CONJ", "NEG", "EMPH", "COND"):
        syntactic_role = "connector"
    elif morph.pos == "PRON":
        syntactic_role = "subject"
    else:
        syntactic_role = "none"

    return SemanticToken(
        position=position,
        surface=morph.surface,
        semantic_field=semantic_field,
        pattern_meaning=pattern_meaning,
        syntactic_role=syntactic_role,
    )


def analyze_logic(
    morph: MorphAnalysis,
    position: int,
    words_in_verse: int,
) -> LogicToken:
    """Build a logic token from morphological analysis and context."""
    cleaned = clean_word(morph.surface)

    # Check for known logic operators
    operator_info = _LOGIC_OPERATORS.get(cleaned)

    if operator_info:
        operator, role, emphasis = operator_info
        return LogicToken(
            position=position,
            surface=morph.surface,
            operator=operator,
            role_in_argument=role,
            emphasis_level=emphasis,
        )

    # Check if it's a command (imperative verb)
    if morph.pos == "V" and cleaned and cleaned[0] not in "يتنا":
        # Likely imperative if no imperfect prefix
        return LogicToken(
            position=position,
            surface=morph.surface,
            operator="command",
            role_in_argument="conclusion",
        )

    # Check for emphasis particles in prefixes
    emphasis = 0.0
    for prefix in morph.prefixes:
        prefix_clean = clean_word(prefix)
        if prefix_clean in _EMPHASIS_PARTICLES:
            emphasis += _EMPHASIS_PARTICLES[prefix_clean]

    if emphasis > 0:
        return LogicToken(
            position=position,
            surface=morph.surface,
            operator="emphasis",
            role_in_argument="emphasis",
            emphasis_level=min(emphasis, 1.0),
        )

    # Default: content word, no special logical function
    return LogicToken(
        position=position,
        surface=morph.surface,
        operator="none",
        role_in_argument="",
    )


def analyze_verse_logic(
    morphs: list[MorphAnalysis],
) -> list[LogicToken]:
    """Analyze logic tokens for an entire verse with cross-word awareness.

    Detects multi-word patterns like مَا...إِلَّا (restriction) and
    sets negation_scope and connects_to fields.
    """
    n = len(morphs)
    tokens = [analyze_logic(m, i, n) for i, m in enumerate(morphs)]

    # --- Post-processing: multi-word patterns ---

    # Detect مَا...إِلَّا restriction pattern
    for i, tok in enumerate(tokens):
        if tok.operator == "negation":
            # Look ahead for إلا
            for j in range(i + 1, min(i + 8, n)):
                if clean_word(morphs[j].surface) == "الا":
                    tokens[i].operator = "restriction"
                    tokens[i].role_in_argument = "emphasis"
                    tokens[i].emphasis_level = 0.5
                    tokens[i].connects_to = [j]
                    tokens[j].operator = "restriction"
                    tokens[j].role_in_argument = "exception"
                    tokens[j].connects_to = [i]
                    # Everything between is the negation scope
                    tokens[i].negation_scope = list(range(i + 1, j))
                    break

    # Detect إِنَّ ... لَ emphasis stacking
    for i, tok in enumerate(tokens):
        if tok.operator == "emphasis" and clean_word(morphs[i].surface) in ("ان",):
            # Look for لَ prefix on a later word
            for j in range(i + 1, min(i + 6, n)):
                for prefix in morphs[j].prefixes:
                    if clean_word(prefix) == "ل":
                        tokens[i].emphasis_level = min(tok.emphasis_level + 0.3, 1.0)
                        tokens[i].connects_to = [j]
                        break

    # Detect شرط (condition → response) — إِذَا/إِنْ ... فَ
    for i, tok in enumerate(tokens):
        if tok.operator in ("condition", "hypothetical"):
            for j in range(i + 1, min(i + 15, n)):
                if tokens[j].operator == "consequence":
                    tokens[i].connects_to = [j]
                    tokens[j].role_in_argument = "response"
                    tokens[j].connects_to = [i]
                    break

    return tokens


# ---------------------------------------------------------------------------
# Level 3: Idea transition analysis
# ---------------------------------------------------------------------------

# Operators that signal a topic / idea shift
_PIVOT_OPERATORS = {"consequence", "sequence", "adversative", "result"}
_CONTRAST_OPERATORS = {"adversative", "negation", "restriction", "exception"}
_ESCALATION_OPERATORS = {"emphasis", "oath"}
_QUESTION_OPERATORS = {"question", "rhetorical_denial"}


def analyze_verse_transitions(
    morphs: list[MorphAnalysis],
    semantic_tokens: list[SemanticToken],
    logic_tokens: list[LogicToken],
) -> list[TransitionToken]:
    """Build transition tokens that capture idea-to-idea flow within a verse.

    For each word position, determines:
    - Whether the semantic field changed (idea shift)
    - What kind of transition the logic operator signals
    - The discourse depth (nesting of arguments)
    - Whether an earlier idea is being echoed (callback)
    """
    n = len(morphs)
    if n == 0:
        return []

    transitions: list[TransitionToken] = []
    depth = 0
    seen_fields: dict[str, int] = {}  # semantic_field → first position

    for i in range(n):
        sem = semantic_tokens[i] if i < len(semantic_tokens) else None
        logic = logic_tokens[i] if i < len(logic_tokens) else None
        surface = morphs[i].surface if i < len(morphs) else ""

        cur_field = sem.semantic_field if sem else "none"
        prev_field = (
            semantic_tokens[i - 1].semantic_field
            if i > 0 and i - 1 < len(semantic_tokens)
            else "none"
        )
        prev_operator = (
            logic_tokens[i - 1].operator
            if i > 0 and i - 1 < len(logic_tokens)
            else "none"
        )
        cur_operator = logic.operator if logic else "none"

        # --- Determine transition type ---
        transition_type = "continuation"  # default: same idea continues

        if i == 0:
            transition_type = "none"  # first word — no transition yet
        elif cur_operator in _QUESTION_OPERATORS:
            transition_type = "question_answer"
        elif (
            cur_operator in _CONTRAST_OPERATORS or prev_operator in _CONTRAST_OPERATORS
        ):
            transition_type = "contrast"
        elif cur_operator in _ESCALATION_OPERATORS:
            transition_type = "escalation"
        elif cur_field != "none" and prev_field != "none" and cur_field != prev_field:
            # Semantic field changed — this is an idea shift
            if cur_operator in _PIVOT_OPERATORS:
                transition_type = "pivot"
            else:
                transition_type = "evidence_shift"
        elif cur_operator == "condition" or cur_operator == "hypothetical":
            depth += 1
            transition_type = "parenthetical"
        elif cur_operator == "condition_response":
            depth = max(0, depth - 1)
            transition_type = "conclusion"

        # --- Detect callbacks (echoing an earlier idea) ---
        returns_to = -1
        if (
            cur_field != "none"
            and cur_field in seen_fields
            and seen_fields[cur_field] < i - 2
        ):
            returns_to = seen_fields[cur_field]
            transition_type = "callback"

        # Track first occurrence of each semantic field
        if cur_field != "none" and cur_field not in seen_fields:
            seen_fields[cur_field] = i

        transitions.append(
            TransitionToken(
                position=i,
                surface=surface,
                transition_type=transition_type,
                source_idea=prev_field if i > 0 else "",
                target_idea=cur_field,
                smoothness=1.0,  # Quran ground truth — always perfectly smooth
                discourse_depth=depth,
                returns_to=returns_to,
            )
        )

    return transitions
