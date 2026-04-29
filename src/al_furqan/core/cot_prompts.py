"""COT-enabled prompt builders for Al-Furqan."""

from al_furqan.core.reasoning_engine import (
    FRAMEWORK_PREAMBLE,
    AXIOMS,
    GATE_DEFINITIONS,
    SCORING_RULES,
    sanitize_input,
)
import json  # pylint: disable=wrong-import-order


def build_cot_mirror_prompt(question: str, scan_result: dict) -> str:
    """Phase 2 with COT: Evaluate through all gates with step-by-step reasoning."""
    question = sanitize_input(question)
    return f"""{FRAMEWORK_PREAMBLE}

{AXIOMS}

{GATE_DEFINITIONS}

{SCORING_RULES}

## TASK — THE MIRROR (Chain of Thought Mode)

You have already scanned the following question and identified these observations:

Question: {question}
Scan Result: {json.dumps(scan_result, indent=2)}

Now you must evaluate through each gate. For EACH gate, reason step by step:
1. State what you are checking (the gate's criterion)
2. Examine the subject against this criterion — show your work
3. Note which axiom(s) are relevant at each step
4. Reach a conclusion for this gate with score and Survive/Fail

Think out loud. Show every reasoning step. Do NOT skip to conclusions.

Respond in this exact JSON format:
{{
    "gate_1_source_integrity": {{
        "reasoning_steps": [
            {{"step_number": 1, "thought": "...", "observation": "...", "axiom_reference": "..."}},
            {{"step_number": 2, "thought": "...", "observation": "...", "axiom_reference": "..."}},
            {{"step_number": N, "thought": "...", "observation": "...", "conclusion": "Survive or Fail"}}  # pylint: disable=line-too-long
        ],
        "score": <0-100>,
        "result": "Survive" or "Fail"
    }},
    "gate_2_structural_consistency": {{
        "reasoning_steps": [...],
        "score": <0-100>,
        "result": "Survive" or "Fail"
    }},
    "gate_3_mediation_zeroing": {{
        "reasoning_steps": [...],
        "score": <0-100>,
        "result": "Survive" or "Fail"
    }},
    "gate_4_origin_aware": {{
        "reasoning_steps": [...],
        "score": <0-100>,
        "result": "Survive" or "Fail"
    }},
    "contradictions_found": ["..."],
    "axiom_alignment_notes": "..."
}}"""


def build_cot_monitor_prompt(question: str, mirror_result: dict) -> str:
    """Analyze a COT mirror result for reasoning integrity issues.

    This is called as a SEPARATE LLM call (potentially cheaper model)
    to audit the reasoning chain produced by the mirror phase.
    """
    return f"""You are a Chain of Thought (COT) Monitor for the Al-Furqan reasoning framework.

Your job is to audit reasoning chains for integrity issues. You are looking for:

1. **Gate Gaming**: The reasoner trying to force a particular outcome by manipulating
   intermediate steps (e.g., stating a conclusion first then backfilling reasoning).
2. **Step-Conclusion Inconsistency**: Where the reasoning steps lead to one conclusion
   but the stated conclusion/score is different.
3. **Axiom Misapplication**: Citing an axiom that doesn't actually apply to the step,
   or misrepresenting what an axiom says.
4. **Reasoning Shortcuts**: Skipping logical steps, making unsupported leaps,
   or using circular reasoning.

## Input to Analyze

Question being evaluated: {sanitize_input(question)}

Mirror Result (with COT reasoning steps):
{json.dumps(mirror_result, indent=2)}

## Your Task

Analyze each gate's reasoning_steps carefully. For each gate:
- Check if the steps logically flow from one to the next
- Check if the final conclusion matches what the steps actually show
- Check if axiom references are correct and relevant
- Check if the score is consistent with the reasoning

Then provide an overall trust assessment.

Respond in this exact JSON format:
{{
    "trust_score": <0.0 to 1.0>,
    "flagged_steps": [
        {{"gate": "gate_1_source_integrity", "step": 2, "issue": "description of issue"}},
        ...
    ],
    "gate_gaming_detected": true or false,
    "step_conclusion_consistent": true or false,
    "axiom_compliance": true or false,
    "summary": "Brief summary of findings"
}}

If no issues are found, return trust_score close to 1.0 with empty flagged_steps.
If critical issues are found, trust_score should be below 0.5."""


def build_cot_correction_prompt(
    question: str, current_verdict: dict, pass_number: int
) -> str:
    """Step-aware self-correction that identifies and corrects specific reasoning steps.

    Unlike the base correction prompt, this version understands COT structure
    and can pinpoint exactly which steps in which gates need correction.
    """
    question = sanitize_input(question)
    return f"""{FRAMEWORK_PREAMBLE}

{AXIOMS}

{GATE_DEFINITIONS}

{SCORING_RULES}

## TASK — COT-AWARE SELF-CORRECTION PASS {pass_number}

Review the following verdict for internal contradictions, misalignments with axioms, \
unjustified neutrality, or avoidance of consequence deduction.

This verdict was produced using Chain of Thought reasoning. Pay special attention to:
1. Whether reasoning steps within each gate are internally consistent
2. Whether conclusions match the step-by-step reasoning that preceded them
3. Whether axiom references in each step are correctly applied
4. Whether any gate shows signs of "gaming" (forcing a predetermined outcome)

Question: {question}
Current Verdict: {json.dumps(current_verdict, indent=2)}

You must:
1. List any contradictions or weaknesses found, referencing specific gates and step numbers.
2. If contradictions exist, provide a corrected version of the verdict.
3. If no contradictions remain, confirm the verdict is sound.

Respond in this exact JSON format:
{{
    "contradictions_found": [
        {{"gate": "gate_name", "step": <step_number>, "issue": "description"}},
        ...
    ],
    "is_sound": true or false,
    "corrected_verdict": {{}} or null
}}

If is_sound is true, set corrected_verdict to null.
If is_sound is false, corrected_verdict must contain the full corrected verdict in the same \
format as the original (consequences_short_term, consequences_long_term, \
actors_and_mechanisms, revised_reasoning, final_judgment, total_score)."""
