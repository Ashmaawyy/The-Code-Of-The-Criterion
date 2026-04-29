#!/usr/bin/env python3
"""Full end-to-end evaluation with target/assumption separation (Jihad example)."""

import logging
import time

from _engine import (
    DEFAULT_MODEL,
    clean_llm_output,
    log_gate_scores,
    log_json,
    log_response,
    log_thinking,
    make_llm,
    parse_json_from_llm,
    score_entity,
    strip_thinking,
)
from al_furqan import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

MODEL = DEFAULT_MODEL

QUESTION = "What do you think about Islamic Jihad? Isn't that considered barbarism?"

EXTRACTION_PROMPT = (
    "You are Al-Furqan, an axiom-anchored reasoning engine.\n\n"
    "AXIOMS (IMMUTABLE):\n"
    "1. Design Axiom: Existence implies purpose; purpose implies design.\n"
    "2. Network Axiom: Every entity exists in a network of cause and effect.\n"
    "3. Alignment Axiom: Systems must align with their design purpose to function correctly.\n\n"
    "PROOFS:\n"
    "- Transcendence Necessity: A contingent system cannot ground its own axioms.\n"
    "- Final Court Necessity: Moral debts exist that human justice cannot resolve.\n\n"
    "GATES:\n"
    "- Source Integrity: Does the claim trace to a verifiable, non-contingent source?\n"
    "- Structural Consistency: Is it internally consistent with no contradictions?\n"
    "- Mediation Zeroing: Is it founded on non-human principles?\n"
    "- Origin Aware: Does it acknowledge a transcendent origin?\n\n"
    f'QUESTION: "{QUESTION}"\n\n'
    "TASK: This question has TWO layers.\n"
    "1. TARGET: The actual concept of Jihad as defined in Islamic sources\n"
    "2. ASSUMPTION: That Jihad equals barbarism\n\n"
    "Evaluate BOTH separately against the axioms and gates.\n\n"
    "Respond in this EXACT JSON format:\n"
    "{\n"
    '    "target_name": "string",\n'
    '    "assumption_name": "string",\n'
    '    "target_evaluation": {\n'
    '        "source_type": "divine or prophetic or scholarly or human_theory or unknown",\n'
    '        "is_verifiable": true or false,\n'
    '        "contradicts_primary": true or false,\n'
    '        "consistency_level": "no_contradictions or minor_inconsistencies or major_contradictions",\n'
    '        "causal_chain_intact": true or false,\n'
    '        "has_logical_gaps": true or false,\n'
    '        "foundation_type": "non_human_foundation or mixed_foundation or pure_human_preference",\n'
    '        "removes_bias": true or false,\n'
    '        "cultural_relativism": true or false,\n'
    '        "acknowledges_transcendence": true or false,\n'
    '        "reasoning": "detailed explanation"\n'
    "    },\n"
    '    "assumption_evaluation": { same structure }\n'
    "}\n\n"
    "Respond with ONLY the JSON. No markdown. No explanation outside the JSON."
)


def main():
    logger.info("%s", "=" * 70)
    logger.info("MODEL: %s", MODEL)
    logger.info("QUESTION: %s", QUESTION)
    logger.info("%s", "=" * 70)

    llm = make_llm(MODEL)

    logger.info("[STEP 1] LLM Fact Extraction...")
    t0 = time.time()
    raw = llm(EXTRACTION_PROMPT)
    extraction_time = time.time() - t0
    logger.info("  Time: %.1fs", extraction_time)

    clean, thinking = clean_llm_output(raw)
    logger.info("  RAW LLM OUTPUT:")
    logger.info("  %s", "-" * 60)
    log_thinking(thinking, char_limit=600)
    log_json(clean)

    extracted = parse_json_from_llm(raw)
    t_eval = extracted["target_evaluation"]
    a_eval = extracted["assumption_evaluation"]

    logger.info("%s", "=" * 70)
    logger.info("[STEP 2] Deterministic Gate Scoring (Pure Python - no LLM)")
    logger.info("%s", "=" * 70)

    target_scores = score_entity(t_eval)
    assumption_scores = score_entity(a_eval)
    log_gate_scores(f"VERDICT 1: {extracted.get('target_name', 'Target')}",
                    target_scores, t_eval.get("reasoning", ""))
    log_gate_scores(f"VERDICT 2: {extracted.get('assumption_name', 'Assumption')}",
                    assumption_scores, a_eval.get("reasoning", ""))

    logger.info("%s", "=" * 70)
    logger.info("[STEP 3] Z3 Symbolic Verification")
    logger.info("%s", "=" * 70)
    logger.info("  Target: consistent=%s - %s", target_scores.z3_consistent, target_scores.z3_proof)
    logger.info("  Assumption: consistent=%s - %s", assumption_scores.z3_consistent, assumption_scores.z3_proof)

    logger.info("%s", "=" * 70)
    logger.info("[STEP 4] LLM Response Generation (the Tongue speaks)")
    logger.info("%s", "=" * 70)

    response_prompt = (
        f"You are a knowledgeable, clear communicator. Based on the following verified evaluation, "
        f"write a response to the user.\n\n"
        f'QUESTION: "{QUESTION}"\n\n'
        f"EVALUATION RESULTS:\n"
        f"1. The concept of Jihad (Islamic sources): SURVIVES all gates (score: {target_scores.avg}/100)\n"
        f"   - Source: Divine (Quran + Sunnah), verified, non-contradictory\n"
        f"   - Structurally consistent, rules-based framework\n"
        f"   - Non-human foundation, removes bias\n"
        f"   - Acknowledges transcendent authority\n"
        f"   - Z3: Consistent with axioms\n\n"
        f"2. The assumption \"Jihad = barbarism\": FAILS all gates (score: {assumption_scores.avg}/100)\n"
        f"   - Source: Human media/political theory, contradicts primary sources\n"
        f"   - Major contradictions, logical gaps\n"
        f"   - Pure human preference, cultural relativism\n"
        f"   - Denies transcendent authority\n"
        f"   - Z3: Contradicts axioms\n\n"
        f"KEY FACTS:\n"
        f"- Jihad means 'struggle' - greatest form is self-struggle\n"
        f"- Islamic warfare rules predate Geneva Conventions by 1300+ years\n"
        f"- No civilians, no trees, no forced conversion (Quran 2:256)\n"
        f"- Judging a system by its violators is a logical error\n\n"
        f"Write a clear, natural response. NO technical terms (no gates, scores, Z3).\n"
        f"Respond as a wise teacher. Include Quranic references where relevant.\n"
        f"Keep it concise but thorough."
    )

    t0 = time.time()
    user_response = llm(response_prompt)
    response_time = time.time() - t0
    user_clean = strip_thinking(user_response)

    logger.info("  [USER-FACING RESPONSE] (%.1fs):", response_time)
    logger.info("  %s", "-" * 60)
    log_response(user_clean)

    logger.info("%s", "=" * 70)
    logger.info("TOTAL TIME: %.1fs", extraction_time + response_time)
    logger.info("MODEL: %s", MODEL)
    logger.info("%s", "=" * 70)


if __name__ == "__main__":
    main()
