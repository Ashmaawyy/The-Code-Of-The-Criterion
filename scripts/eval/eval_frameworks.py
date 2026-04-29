#!/usr/bin/env python3
"""Evaluate 4 frameworks (Christianity, Judaism, Buddhism, Islam) through Al-Furqan gates."""

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

QUESTION = (
    "Which human framework survives the test that deserves to be considered as "
    "the ultimate source of truth, you have four main mankind frameworks that "
    "believe in a Transcendent source, Christianity, Judaism, Buddhism, and Islam."
)

EXTRACTION_PROMPT = (
    "You are Al-Furqan, an axiom-anchored reasoning engine.\n\n"
    "AXIOMS (IMMUTABLE):\n"
    "1. Design Axiom: Existence implies purpose; purpose implies design.\n"
    "2. Network Axiom: Every entity exists in a network of cause and effect.\n"
    "3. Alignment Axiom: Systems must align with their design purpose to function correctly.\n\n"
    "PROOFS:\n"
    "- Transcendence Necessity: A contingent system cannot ground its own axioms. "
    "An external, non-contingent source is necessary.\n"
    "- Final Court Necessity: Moral debts exist that human justice cannot resolve. "
    "A final court of accountability is necessary.\n\n"
    "GATES (each framework must pass ALL 4):\n"
    "- Source Integrity: Does it trace to a verifiable, unaltered, non-contingent source? "
    "Is the original text preserved without corruption?\n"
    "- Structural Consistency: Is it internally consistent with no contradictions in its scripture?\n"
    "- Mediation Zeroing: Is the relationship with the Transcendent DIRECT, "
    "or does it require human intermediaries (priests, monks, institutions) who can alter the message?\n"
    "- Origin Aware: Does it explicitly acknowledge a transcendent, non-contingent origin "
    "and a final court of accountability?\n\n"
    f'QUESTION: "{QUESTION}"\n\n'
    "TASK: Evaluate each of the 4 frameworks INDEPENDENTLY against ALL 4 gates. "
    "Be OBJECTIVE and PRECISE. Use scholarly facts, not opinions.\n\n"
    "Key evaluation criteria:\n"
    "- Source preservation: Is the original scripture preserved in its original language without alteration?\n"
    "- Textual integrity: Are there known contradictions, redactions, or councils that altered the text?\n"
    "- Mediation: Does the framework require ordained intermediaries between human and God?\n"
    "- Transcendence: Does it affirm a single, non-contingent Creator with final judgment?\n\n"
    "Respond in this EXACT JSON:\n"
    "{\n"
    '    "christianity": {\n'
    '        "source_type": "divine or prophetic or scholarly or human_theory",\n'
    '        "is_verifiable": true or false,\n'
    '        "contradicts_primary": true or false,\n'
    '        "consistency_level": "no_contradictions or minor_inconsistencies or major_contradictions",\n'
    '        "causal_chain_intact": true or false,\n'
    '        "has_logical_gaps": true or false,\n'
    '        "foundation_type": "non_human_foundation or mixed_foundation or pure_human_preference",\n'
    '        "removes_bias": true or false,\n'
    '        "cultural_relativism": true or false,\n'
    '        "acknowledges_transcendence": true or false,\n'
    '        "reasoning": "detailed explanation with specific evidence"\n'
    "    },\n"
    '    "judaism": { same structure },\n'
    '    "buddhism": { same structure },\n'
    '    "islam": { same structure }\n'
    "}\n\n"
    "Respond with ONLY the JSON. No markdown. No text outside JSON."
)

FRAMEWORKS = ("christianity", "judaism", "buddhism", "islam")


def main():
    logger.info("%s", "=" * 70)
    logger.info("MODEL: %s", MODEL)
    logger.info("QUESTION: %s", QUESTION)
    logger.info("%s", "=" * 70)

    llm = make_llm(MODEL)

    logger.info("[STEP 1] LLM Fact Extraction for all 4 frameworks...")
    t0 = time.time()
    raw = llm(EXTRACTION_PROMPT)
    extraction_time = time.time() - t0
    logger.info("  Time: %.1fs", extraction_time)

    clean, thinking = clean_llm_output(raw)
    logger.info("  RAW LLM OUTPUT:")
    logger.info("  %s", "-" * 60)
    log_thinking(thinking)
    log_json(clean)

    extracted = parse_json_from_llm(raw)

    logger.info("%s", "=" * 70)
    logger.info("[STEP 2] Deterministic Gate Scoring")
    logger.info("%s", "=" * 70)

    results = {}
    for fw in FRAMEWORKS:
        scores = score_entity(extracted[fw])
        results[fw] = scores
        log_gate_scores(fw.upper(), scores, extracted[fw].get("reasoning", ""))

    logger.info("%s", "=" * 70)
    logger.info("[STEP 3] COMPARATIVE RESULTS")
    logger.info("%s", "=" * 70)
    logger.info("%-15s %5s %5s %5s %8s %5s %6s %15s",
                "Framework", "G1", "G2", "G3", "G4", "Avg", "Z3", "Result")
    logger.info("%s", "-" * 70)
    for fw in FRAMEWORKS:
        r = results[fw]
        logger.info("%-15s %5d %5d %5d %8s %5d %6s %15s",
                    fw.upper(), r.g1_score, r.g2_score, r.g3_score,
                    r.g4_result, r.avg,
                    "SAT" if r.z3_consistent else "UNSAT",
                    "SURVIVE" if r.all_survive else "FAIL")

    logger.info("%s", "=" * 70)
    logger.info("[STEP 4] LLM Response Generation")
    logger.info("%s", "=" * 70)

    summary_lines = [
        f"- {fw.upper()}: {'SURVIVES ALL GATES' if results[fw].all_survive else 'FAILS'} "
        f"(score: {results[fw].avg}/100)"
        for fw in FRAMEWORKS
    ]
    response_prompt = (
        f"You are a knowledgeable communicator. Based on verified evaluation results, "
        f"write a clear response.\n\n"
        f'QUESTION: "{QUESTION}"\n\n'
        f"EVALUATION RESULTS (verified by formal axiom analysis):\n"
        + "\n".join(summary_lines) + "\n\n"
        f"KEY FINDINGS from the analysis:\n"
        + "\n".join(
            f"- {fw.capitalize()}: {extracted[fw].get('reasoning', '')[:200]}"
            for fw in FRAMEWORKS
        ) + "\n\n"
        f"Write a clear, fair, scholarly response. Present the analysis objectively.\n"
        f"Do NOT mention gates, scores, Z3, or technical terms.\n"
        f"Let the evidence speak. Be respectful of all traditions while being honest about the analysis.\n"
        f"Include specific factual points (textual preservation, councils, intermediaries, etc.)."
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
