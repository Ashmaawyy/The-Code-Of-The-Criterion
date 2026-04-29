#!/usr/bin/env python3
"""Evaluate the Islamic preservation challenge: hadith timing, mushaf timing, and the system."""

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
    "You claim Islam is preserved through time. However most of Islamic Hadeeth text "
    "we see now was written about 200 years after the prophet's death, how is that "
    "preserved? Even the Mushaf we have today was written decades after prophet's death."
)

ENTITIES = (
    ("claim_hadith_200_years", "CLAIM: Hadith written 200 years later"),
    ("claim_mushaf_decades", "CLAIM: Mushaf written decades later"),
    ("islamic_preservation_system", "TARGET: Islamic Preservation System"),
)

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
    "- Source Integrity: Does it trace to a verifiable, unaltered, non-contingent source?\n"
    "- Structural Consistency: Is it internally consistent with no contradictions?\n"
    "- Mediation Zeroing: Is it founded on non-human principles?\n"
    "- Origin Aware: Does it acknowledge a transcendent origin?\n\n"
    f'QUESTION: "{QUESTION}"\n\n'
    "IMPORTANT ANALYSIS: This question contains TWO embedded claims that must be separated:\n\n"
    "1. CLAIM A: 'Hadith was written 200 years after the Prophet' - evaluate the ACCURACY of this claim.\n"
    "   Consider: Was hadith ONLY written or also memorized and transmitted orally through verified chains (isnad)?\n"
    "   Was the 200-year gap about compilation into major collections, or about the actual transmission?\n"
    "   What about earlier written compilations (Sahifah of Hammam ibn Munabbih, Muwatta of Malik)?\n\n"
    "2. CLAIM B: 'The Mushaf was written decades after the Prophet's death' - evaluate the ACCURACY.\n"
    "   Consider: Was the Quran memorized by thousands during the Prophet's lifetime?\n"
    "   Were individual surahs written on various materials during his lifetime?\n"
    "   Abu Bakr's compilation was 1-2 years after, Uthman's standardization ~18 years after.\n"
    "   Is 'decades' accurate? Is compilation the same as creation?\n\n"
    "3. TARGET: The actual Islamic preservation system - evaluate how it works.\n"
    "   The dual system: oral memorization (hifz/isnad) + written text.\n"
    "   The isnad system as a verification methodology.\n"
    "   The difference between 'written compilation' and 'preservation'.\n\n"
    "Evaluate ALL THREE separately.\n\n"
    "Respond in this EXACT JSON:\n"
    "{\n"
    '    "claim_hadith_200_years": {\n'
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
    '        "reasoning": "detailed scholarly explanation"\n'
    "    },\n"
    '    "claim_mushaf_decades": { same structure },\n'
    '    "islamic_preservation_system": { same structure }\n'
    "}\n\n"
    "Respond with ONLY the JSON. No markdown. No text outside JSON."
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
    log_thinking(thinking)
    log_json(clean)

    extracted = parse_json_from_llm(raw)

    logger.info("%s", "=" * 70)
    logger.info("[STEP 2] Deterministic Gate Scoring")
    logger.info("%s", "=" * 70)

    results = {}
    for key, label in ENTITIES:
        scores = score_entity(extracted[key])
        results[key] = scores
        log_gate_scores(label, scores, extracted[key].get("reasoning", ""))

    logger.info("%s", "=" * 70)
    logger.info("[STEP 3] COMPARATIVE RESULTS")
    logger.info("%s", "=" * 70)
    logger.info("%-45s %5s %5s %5s %8s %5s %6s %12s",
                "Component", "G1", "G2", "G3", "G4", "Avg", "Z3", "Result")
    logger.info("%s", "-" * 95)
    for key, label in ENTITIES:
        r = results[key]
        logger.info("%-45s %5d %5d %5d %8s %5d %6s %12s",
                    label, r.g1_score, r.g2_score, r.g3_score,
                    r.g4_result, r.avg,
                    "SAT" if r.z3_consistent else "UNSAT",
                    "SURVIVE" if r.all_survive else "FAIL")

    logger.info("%s", "=" * 70)
    logger.info("[STEP 4] LLM Response Generation")
    logger.info("%s", "=" * 70)

    h_data = extracted["claim_hadith_200_years"]
    m_data = extracted["claim_mushaf_decades"]
    p_data = extracted["islamic_preservation_system"]

    response_prompt = (
        f"You are a knowledgeable Islamic studies communicator. Based on verified evaluation results, "
        f"write a clear, scholarly response.\n\n"
        f'QUESTION: "{QUESTION}"\n\n'
        f"EVALUATION RESULTS:\n"
        f"1. The claim 'Hadith written 200 years later': {results['claim_hadith_200_years'].avg}/100\n"
        f"   Analysis: {h_data.get('reasoning', '')[:300]}\n\n"
        f"2. The claim 'Mushaf written decades later': {results['claim_mushaf_decades'].avg}/100\n"
        f"   Analysis: {m_data.get('reasoning', '')[:300]}\n\n"
        f"3. The Islamic preservation system: {results['islamic_preservation_system'].avg}/100\n"
        f"   Analysis: {p_data.get('reasoning', '')[:300]}\n\n"
        f"KEY SCHOLARLY POINTS to address:\n"
        f"- The difference between 'compilation into books' and 'preservation/transmission'\n"
        f"- The isnad (chain of narration) system - the world's first peer-review methodology\n"
        f"- Early written hadith: Sahifah of Hammam ibn Munabbih (~50 years after Prophet)\n"
        f"- Muwatta of Imam Malik (~140 AH) predates the 'major six' collections\n"
        f"- Quran: memorized by thousands DURING the Prophet's lifetime (mass concurrent transmission)\n"
        f"- Abu Bakr's compilation: ~1 year after Prophet's death (not decades)\n"
        f"- Uthman's standardization: ~18 years after (standardizing script, not content)\n"
        f"- The dual preservation system (oral hifz + written) is unique in world history\n\n"
        f"Write naturally. NO technical terms (gates, scores, Z3). Be scholarly but accessible.\n"
        f"Address the specific claims directly. Acknowledge what's true and correct what's inaccurate.\n"
        f"Be respectful - this is a sincere question that deserves a thorough answer."
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
