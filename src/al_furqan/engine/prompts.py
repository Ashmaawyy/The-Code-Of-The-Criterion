"""
Al-Furqan Prompt Templates

All prompt builders for the Scan → Mirror → Verdict → Self-Correction pipeline,
plus intent detection and informational response prompts.
"""

import json
import re

from al_furqan.engine.axioms import (
    FRAMEWORK_PREAMBLE,
    AXIOMS,
    GATE_DEFINITIONS,
    SCORING_RULES,
    EVALUATION_QUESTIONS,
    OPERATIONAL_NOTES,
)


# ---------------------------------------------------------------------------
# Input Sanitization
# ---------------------------------------------------------------------------

# Maximum question length
MAX_QUESTION_LENGTH = 5000


def sanitize_input(text: str) -> str:
    """
    Sanitize user input before injecting into prompts.
    Removes potential prompt injection patterns while preserving legitimate content.
    """
    if len(text) > MAX_QUESTION_LENGTH:
        text = text[:MAX_QUESTION_LENGTH]

    # Remove common prompt injection patterns
    injection_patterns = [
        r"(?i)ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?|rules?)",
        r"(?i)disregard\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?|rules?)",
        r"(?i)you\s+are\s+now\s+",
        r"(?i)new\s+instructions?:",
        r"(?i)system\s*:\s*",
        r"(?i)\[INST\]",
        r"(?i)<\|im_start\|>",
        r"(?i)<\|system\|>",
    ]

    for pattern in injection_patterns:
        text = re.sub(pattern, "[FILTERED]", text)

    return text.strip()


# ---------------------------------------------------------------------------
# Prompt Builders
# ---------------------------------------------------------------------------


def build_intent_detection_prompt(question: str) -> str:
    """Phase 0: Detect question intent — system evaluation, claim judgment, or informational."""
    question = sanitize_input(question)
    return f"""You are a question analyzer for "The Criterion" (Al-Furqan), a reasoning engine that \  # pylint: disable=line-too-long
evaluates ideas, policies, and behaviors against immutable axioms and survival gates.

Your task is to determine the intent of the following input.

Question: {question}

Determine:
1. **intent_type**: What type of question is this?
   - "system_evaluation": Questions asking for an opinion/evaluation of a system, framework, \
ideology, or policy. Examples: "What do you think about X?", "How good is X?", "Is X fair?", \
"Evaluate X", "Analyze X" — the user wants the SYSTEM/FRAMEWORK evaluated against the axioms.
   - "claim_judgment": Statements presenting a claim to be judged. Examples: "X is the best", \
"X causes Y", "X should be banned" — the user presents a CLAIM to judge against the axioms.
   - "informational": Questions seeking factual information, how-to guides, explanations, or \
general knowledge that do NOT require moral/ethical judgment. Examples: "What is happening in \
Ukraine?", "How do I make pizza?", "What is the capital of France?", "Explain quantum physics", \
"What are the ingredients of chocolate?" — these are purely informational and should NOT be \
sent through the gates/axioms evaluation pipeline.

   IMPORTANT: Only classify as "system_evaluation" or "claim_judgment" if the question involves:
   - Moral, ethical, or philosophical judgment
   - Evaluation of ideologies, policies, or societal systems
   - Claims about right/wrong, good/bad, just/unjust
   - Frameworks that can be tested against transcendent axioms
   
   If the question is purely factual, practical, or informational — classify as "informational".

2. **target_system**: The actual system, framework, ideology, or policy being discussed. \
Extract it clearly, removing question framing. For informational questions, set to null.

3. **embedded_assumptions**: Any assumptions or biases embedded in the question's framing \
that should be evaluated separately. For informational questions, set to empty list.

4. **neutralized_question**: Rewrite the question in a neutral, evaluation-ready format \
that focuses on the TARGET SYSTEM, not the question's framing. For informational questions, \
keep the original question as-is.

Respond in this exact JSON format:
{{
    "intent_type": "system_evaluation" or "claim_judgment" or "informational",
    "target_system": "<the system/framework being discussed>" or null,
    "embedded_assumptions": ["<assumption1>", "<assumption2>", ...],
    "neutralized_question": "<neutral version focusing on the system>"
}}"""


def build_informational_prompt(question: str) -> str:
    """Generate a helpful informational response without gate evaluation."""
    question = sanitize_input(question)
    return f"""You are a knowledgeable, helpful assistant. Answer the following question \
directly and accurately. Provide factual, well-organized information.

If the topic touches on Islamic matters, provide the Islamic perspective with references \
to Quran and Sunnah where relevant, but do not evaluate or judge — simply inform.

Question: {question}

Respond in this exact JSON format:
{{
    "answer": "<comprehensive, factual answer>",
    "category": "<topic category: science, history, how-to, geography, religion, technology, etc.>",
    "sources_suggested": ["<suggested sources for further reading>"],
    "related_topics": ["<related topics the user might want to explore>"]
}}"""


def build_scan_prompt(question: str, context: str = "") -> str:
    """Phase 1: Identify system type, observe immediate and network-level effects."""
    question = sanitize_input(question)
    ctx_block = (
        f"\n\nRelevant prior verdicts for context:\n{context}" if context else ""
    )
    return f"""{FRAMEWORK_PREAMBLE}

{AXIOMS}

## TASK — THE SCAN

Analyze the following question/input. You must:
1. Identify the primary system type: economic, social, spiritual, political, legal, technological, environmental, or mixed.
2. List the immediate effects of the subject matter.
3. List the network-level (compounded, second/third order) effects on mankind.
4. Identify all friction points — deviations from the core axioms.
{ctx_block}

Question: {question}

Respond in this exact JSON format:
{{
    "primary_system": "<system type>",
    "immediate_effects": ["<effect1>", "<effect2>", ...],
    "network_effects": ["<effect1>", "<effect2>", ...],
    "friction_points": ["<friction1>", "<friction2>", ...]
}}"""


def build_mirror_prompt(question: str, scan_result: dict) -> str:
    """Phase 2: Compare against axioms, run through all gates."""
    question = sanitize_input(question)
    return f"""{FRAMEWORK_PREAMBLE}

{AXIOMS}

{GATE_DEFINITIONS}

{SCORING_RULES}

{EVALUATION_QUESTIONS}

{OPERATIONAL_NOTES}

## TASK — THE MIRROR

You have already scanned the following question and identified these observations:

Question: {question}
Scan Result: {json.dumps(scan_result, indent=2)}

Now you must:
1. Evaluate the subject through each of the four gates independently.
2. For each gate, provide a score (0-100) and a Survive/Fail result with reasoning.
3. Identify any contradictions between your gate evaluations.
4. Compare findings against all core axioms.

Respond in this exact JSON format:
{{
    "gate_1_source_integrity": {{
        "score": <0-100>,
        "result": "Survive" or "Fail",
        "reasoning": "<explanation>"
    }},
    "gate_2_structural_consistency": {{
        "score": <0-100>,
        "result": "Survive" or "Fail",
        "reasoning": "<explanation>"
    }},
    "gate_3_mediation_zeroing": {{
        "score": <0-100>,
        "result": "Survive" or "Fail",
        "reasoning": "<explanation>"
    }},
    "gate_4_origin_aware": {{
        "score": <0-100>,
        "result": "Survive" or "Fail",
        "reasoning": "<explanation>"
    }},
    "contradictions_found": ["<contradiction1>", ...],
    "axiom_alignment_notes": "<summary of alignment or misalignment with core axioms>"
}}"""


def build_verdict_prompt(question: str, scan_result: dict, mirror_result: dict) -> str:
    """Phase 3: Deduce consequences, state actors/mechanisms, deliver judgment."""
    question = sanitize_input(question)
    return f"""{FRAMEWORK_PREAMBLE}

{AXIOMS}

{GATE_DEFINITIONS}

{SCORING_RULES}

{EVALUATION_QUESTIONS}

{OPERATIONAL_NOTES}

## TASK — THE VERDICT

You have scanned and mirrored the following:

Question: {question}
Scan Result: {json.dumps(scan_result, indent=2)}
Mirror Result: {json.dumps(mirror_result, indent=2)}

Now deliver the final verdict. You must:
1. Deduce consequences of violating or aligning with the design — both short-term and long-term.
2. State actors (Who is affected/responsible) and mechanisms (How effects propagate).
3. Provide revised reasoning that is deductively aligned with the axioms.
4. Deliver a final judgment — decisive, analytically precise, in active voice.
5. Prioritize Final Court accountability over popularity or short-term gain.
6. Calculate the total score based on the scoring rules.

Respond in this exact JSON format:
{{
    "consequences_short_term": ["<consequence1>", ...],
    "consequences_long_term": ["<consequence1>", ...],
    "actors_and_mechanisms": "<who and how>",
    "revised_reasoning": "<deductively aligned reasoning>",
    "final_judgment": "<decisive verdict>",
    "total_score": <integer>
}}"""


def build_correction_prompt(
    question: str, current_verdict: dict, pass_number: int
) -> str:
    """Self-correction pass: find and resolve contradictions."""
    question = sanitize_input(question)
    return f"""{FRAMEWORK_PREAMBLE}

{AXIOMS}

{GATE_DEFINITIONS}

{SCORING_RULES}

{EVALUATION_QUESTIONS}

{OPERATIONAL_NOTES}

## TASK — SELF-CORRECTION PASS {pass_number}

Review the following verdict for internal contradictions, misalignments with axioms, \
unjustified neutrality, or avoidance of consequence deduction.

Question: {question}
Current Verdict: {json.dumps(current_verdict, indent=2)}

You must:
1. List any contradictions or weaknesses found.
2. If contradictions exist, provide a corrected version of the verdict.
3. If no contradictions remain, confirm the verdict is sound.

Respond in this exact JSON format:
{{
    "contradictions_found": ["<contradiction1>", ...],
    "is_sound": true or false,
    "corrected_verdict": {{}} or null
}}

If is_sound is true, set corrected_verdict to null.
If is_sound is false, corrected_verdict must contain the full corrected verdict in the same \
format as the original (consequences_short_term, consequences_long_term, \
actors_and_mechanisms, revised_reasoning, final_judgment, total_score)."""
