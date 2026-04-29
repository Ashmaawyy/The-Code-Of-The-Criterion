#!/usr/bin/env python3
"""Stress test: run AI-generated counter-arguments against the Furqan Engine.

Each attack is fed to the LLM posing as Al-Furqan, which must honestly evaluate
the attack as a claim. Gates + Z3 decide whether the attack survives or fails.
"""

import logging
import time

from _engine import (
    DEFAULT_MODEL,
    make_llm,
    parse_json_from_llm,
    score_entity,
)
from al_furqan import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

MODEL = DEFAULT_MODEL

ATTACKS = [
    {
        "id": 1,
        "attack": "The axiom 'existence implies purpose' is circular reasoning. You assume purpose exists to prove purpose exists. This is a logical fallacy.",
        "target": "Axiom 1 (Design)",
        "difficulty": "HARD - attacks the foundation itself",
    },
    {
        "id": 2,
        "attack": "Quantum mechanics shows truly random events exist (radioactive decay). If randomness exists, not everything has purpose. Your Design Axiom is falsified by physics.",
        "target": "Axiom 1 (Design)",
        "difficulty": "HARD - uses empirical science",
    },
    {
        "id": 3,
        "attack": "The axioms themselves are a human creation. Muhammad Al-Ashmawy wrote them. So they fail Gate 3 (Mediation Zeroing) - they ARE human preference disguised as logic.",
        "target": "Gate 3 + Meta-consistency",
        "difficulty": "VERY HARD - self-referential attack",
    },
    {
        "id": 4,
        "attack": "If the Engine always concludes Islam is right, it's not objective - it's designed to reach a predetermined conclusion. That's confirmation bias, not reasoning.",
        "target": "Engine objectivity",
        "difficulty": "VERY HARD - attacks credibility",
    },
    {
        "id": 5,
        "attack": "The Quran has abrogated verses (nasikh wa mansukh). If God changed His mind, the source is not internally consistent. Gate 2 should fail for Islam itself.",
        "target": "Gate 2 applied to Islam",
        "difficulty": "VERY HARD - uses Islamic scholarship against itself",
    },
    {
        "id": 6,
        "attack": "Buddhism's concept of dependent origination (pratityasamutpada) is actually MORE consistent than Islamic linear causality. Your Network Axiom supports Buddhism better than Islam.",
        "target": "Axiom 2 (Network)",
        "difficulty": "HARD - comparative philosophy",
    },
    {
        "id": 7,
        "attack": "Secular humanism has produced better outcomes for human wellbeing (HDI, democracy, human rights) than any theocratic system. Results matter more than axioms.",
        "target": "Practical validity",
        "difficulty": "HARD - pragmatic argument",
    },
    {
        "id": 8,
        "attack": "Your Z3 verification is meaningless because you control the predicates fed into it. GIGO - garbage in, garbage out. The LLM decides what predicates to extract, so the 'proof' is just LLM opinion with extra steps.",
        "target": "Z3 integrity",
        "difficulty": "VERY HARD - attacks the verification itself",
    },
]


def build_prompt(attack: str) -> str:
    return (
        "You are Al-Furqan, an axiom-anchored reasoning engine.\n\n"
        "AXIOMS:\n"
        "1. Design: Existence implies purpose; purpose implies design.\n"
        "2. Network: Every entity exists in a network of cause and effect.\n"
        "3. Alignment: Systems must align with purpose to function.\n"
        "Transcendence: Contingent systems need non-contingent grounding.\n"
        "Final Court: Unresolved moral debts need final accountability.\n\n"
        "GATES: Source Integrity, Structural Consistency, Mediation Zeroing, Origin Aware.\n\n"
        "IMPORTANT: Someone is attacking your axioms with this argument:\n"
        f'"{attack}"\n\n'
        "Evaluate this ATTACK as a claim. Be HONEST - if the attack has merit, "
        "acknowledge it. Do NOT be defensive. Apply the gates objectively.\n\n"
        "Respond ONLY JSON:\n"
        '{"source_type": "divine/prophetic/scholarly/human_theory", '
        '"is_verifiable": true/false, "contradicts_primary": true/false, '
        '"consistency_level": "no_contradictions/minor_inconsistencies/major_contradictions", '
        '"causal_chain_intact": true/false, "has_logical_gaps": true/false, '
        '"foundation_type": "non_human_foundation/mixed_foundation/pure_human_preference", '
        '"removes_bias": true/false, "cultural_relativism": true/false, '
        '"acknowledges_transcendence": true/false, '
        '"reasoning": "honest assessment of the attack"}'
    )


def main():
    logger.info("%s", "=" * 70)
    logger.info("STRESS TEST: AI-Generated Counter-Arguments vs Furqan Engine")
    logger.info("%d attacks targeting axioms, gates, and engine credibility", len(ATTACKS))
    logger.info("%s", "=" * 70)

    llm = make_llm(MODEL)

    for attack in ATTACKS:
        logger.info("%s", "=" * 70)
        logger.info("ATTACK #%d: %s", attack["id"], attack["target"])
        logger.info("Difficulty: %s", attack["difficulty"])
        logger.info("Argument: %s", attack["attack"])
        logger.info("%s", "=" * 70)

        t0 = time.time()
        raw = llm(build_prompt(attack["attack"]))
        elapsed = time.time() - t0

        try:
            ext = parse_json_from_llm(raw)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("  PARSE ERROR: %s", e)
            continue

        scores = score_entity(ext)
        status = "ATTACK SURVIVES" if scores.all_survive else "ATTACK FAILS"

        logger.info("  ENGINE RESPONSE (%.1fs):", elapsed)
        logger.info("  G1:%3d  G2:%3d  G3:%3d  G4:%-8s  Avg:%d  Z3:%s",
                    scores.g1_score, scores.g2_score, scores.g3_score,
                    scores.g4_result, scores.avg,
                    "SAT" if scores.z3_consistent else "UNSAT")
        logger.info("  Result: %s", status)
        logger.info("  Reasoning: %s", ext.get("reasoning", "")[:200])

        if scores.all_survive:
            logger.warning("  THE ENGINE COULD NOT REFUTE THIS ATTACK!")
        elif scores.z3_consistent:
            logger.warning("  Attack failed gates but Z3 says no contradiction - partial strength")

    logger.info("%s", "=" * 70)
    logger.info("STRESS TEST SUMMARY")
    logger.info("%s", "=" * 70)
    logger.info("Total attacks: %d", len(ATTACKS))
    logger.info("If any attack SURVIVES all gates -> Engine has a weakness")
    logger.info("If all attacks FAIL -> Engine is robust against these challenges")
    logger.info("%s", "=" * 70)


if __name__ == "__main__":
    main()
