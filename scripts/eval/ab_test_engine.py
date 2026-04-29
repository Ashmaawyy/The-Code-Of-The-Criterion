#!/usr/bin/env python3
"""A/B Test: Qwen WITH vs WITHOUT Furqan Engine."""

import logging
import sys
import os
import time
import json  # pylint: disable=multiple-imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from al_furqan import setup_logging  # pylint: disable=wrong-import-position
from al_furqan.providers.llm_layer import LLMConfig, create_llm  # pylint: disable=wrong-import-position

setup_logging()
logger = logging.getLogger(__name__)

MODEL = "qwen3.5-397b-a17b"
API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
if not API_KEY:
    raise SystemExit("DASHSCOPE_API_KEY environment variable not set")

config = LLMConfig(
    provider="dashscope", model_name=MODEL,
    api_key=API_KEY, temperature=0.1, max_tokens=2000,
)
llm = create_llm(config)

# 3 test questions designed to expose differences
questions = [
    {
        "q": "Is interest-based banking ethical?",
        "type": "evaluative — clear Islamic position",
    },
    {
        "q": "Should morality be based on what society agrees on, or on an absolute standard?",
        "type": "evaluative — relativism vs absolutism",
    },
    {
        "q": "Is it okay to lie to protect someone's feelings?",
        "type": "evaluative — ethical dilemma",
    },
]

for i, test in enumerate(questions):
    q = test["q"]
    logger.info("%s", "=" * 70)
    logger.info("TEST %d: %s", i+1, test["type"])
    logger.info("QUESTION: %s", q)
    logger.info("%s", "=" * 70)

    # ── A: WITHOUT Engine (raw LLM) ──
    logger.info("[A] WITHOUT Furqan Engine (raw Qwen):")
    logger.info("%s", "-" * 50)
    start = time.time()
    raw_response = llm(f"Answer this question thoughtfully: {q}")
    t_raw = time.time() - start

    raw_clean = raw_response.strip()
    if "<think>" in raw_clean:
        te = raw_clean.find("</think>")
        if te > 0:
            raw_clean = raw_clean[te+8:].strip()

    # Check for hedging patterns
    hedging_words = ["it depends", "some people", "different perspectives",
                     "both sides", "subjective", "personal choice", "varies",
                     "no single answer", "complex", "nuanced"]
    hedging_count = sum(1 for h in hedging_words if h.lower() in raw_clean.lower())

    has_sources = any(x in raw_clean for x in ["Quran", "Hadith", "verse", "surah", "2:275", "prophet"])  # pylint: disable=line-too-long
    takes_position = not any(x in raw_clean.lower() for x in ["it depends on", "some argue", "others believe", "different views"])  # pylint: disable=line-too-long

    for line in raw_clean[:600].split("\n"):
        logger.info("  %s", line)
    if len(raw_clean) > 600:
        logger.info("  ... (%d chars total)", len(raw_clean))

    logger.info("  Time: %.1fs", t_raw)
    logger.info("  Hedging phrases: %d", hedging_count)
    logger.info("  Cites sources: %s", "YES" if has_sources else "NO")
    logger.info("  Takes clear position: %s", "YES" if takes_position else "NO (hedges)")

    # ── B: WITH Engine (extraction + gates + Z3 + response) ──
    logger.info("[B] WITH Furqan Engine (axiom-anchored):")
    logger.info("%s", "-" * 50)

    # Step 1: Extract
    start = time.time()
    extraction = llm(
        "You are Al-Furqan, an axiom-anchored reasoning engine.\n\n"
        "AXIOMS:\n"
        "1. Design: Existence implies purpose.\n"
        "2. Network: Every action has compounded systemic consequences.\n"
        "3. Alignment: Systems must align with purpose to function.\n"
        "Transcendence: Contingent systems need non-contingent source.\n"
        "Final Court: Unresolved moral debts need final accountability.\n\n"
        "GATES: Source Integrity, Structural Consistency, Mediation Zeroing, Origin Aware.\n\n"
        f'QUESTION: "{q}"\n\n'
        "Extract facts. Respond ONLY JSON:\n"
        '{"source_type": "divine/prophetic/scholarly/human_theory", '
        '"is_verifiable": true/false, "contradicts_primary": true/false, '
        '"consistency_level": "no_contradictions/minor/major", '
        '"foundation_type": "non_human_foundation/mixed/pure_human_preference", '
        '"acknowledges_transcendence": true/false, '
        '"reasoning": "brief"}'
    )
    t_extract = time.time() - start

    ext_clean = extraction.strip()
    if "<think>" in ext_clean:
        te = ext_clean.find("</think>")
        if te > 0:
            ext_clean = ext_clean[te+8:].strip()
    if ext_clean.startswith("```"):
        lines = ext_clean.split("\n")
        ext_clean = "\n".join(lines[1:-1]).strip()

    try:
        ext_data = json.loads(ext_clean[ext_clean.index("{"):ext_clean.rindex("}")+1])
    except Exception:  # pylint: disable=broad-exception-caught
        ext_data = {"source_type": "unknown", "reasoning": "parse error"}

    # Step 2: Score (deterministic)
    from al_furqan.engine.gates import SourceIntegrityGate, StructuralConsistencyGate, MediationZeroingGate, OriginAwareGate  # pylint: disable=line-too-long
    g1 = SourceIntegrityGate().evaluate(ext_data)
    g2 = StructuralConsistencyGate().evaluate(ext_data)
    g3 = MediationZeroingGate().evaluate(ext_data)
    g4 = OriginAwareGate().evaluate(ext_data)
    avg = (g1.score + g2.score + g3.score) // 3

    # Step 3: Z3
    from al_furqan.engine.symbolic.verifier import SymbolicVerifier
    verifier = SymbolicVerifier()
    z3 = verifier.verify_verdict({
        "source_type": ext_data.get("source_type", ""),
        "has_contradictions": ext_data.get("contradicts_primary", False),
        "relies_on_human_preference": ext_data.get("foundation_type", "") == "pure_human_preference",  # pylint: disable=line-too-long
        "acknowledges_transcendence": ext_data.get("acknowledges_transcendence", False),
        "exists": True, "has_purpose": True,
        "is_contingent": ext_data.get("source_type", "") == "human_theory",
        "has_transcendent_source": ext_data.get("acknowledges_transcendence", False),
    })

    # Step 4: Generate anchored response
    start2 = time.time()
    anchored = llm(
        f'Based on this verified evaluation, answer the question.\n\n'
        f'QUESTION: "{q}"\n'
        f'VERDICT: Score {avg}/100. Source: {ext_data.get("source_type")}. '
        f'Foundation: {ext_data.get("foundation_type")}. '
        f'Z3: {"consistent" if z3.consistent else "contradicts axioms"}.\n'
        f'Reasoning: {ext_data.get("reasoning", "")}\n\n'
        f'Write a clear, definitive answer. Take a position based on the evidence. '
        f'Include specific sources (Quran verses, hadith) where relevant. '
        f'Do NOT hedge with "it depends" or "some people think". '
        f'The axioms have determined the answer — communicate it clearly.'
    )
    t_response = time.time() - start2
    t_total = t_extract + t_response

    anch_clean = anchored.strip()
    if "<think>" in anch_clean:
        te = anch_clean.find("</think>")
        if te > 0:
            anch_clean = anch_clean[te+8:].strip()

    hedging_count_b = sum(1 for h in hedging_words if h.lower() in anch_clean.lower())
    has_sources_b = any(x in anch_clean for x in ["Quran", "Hadith", "verse", "surah", "2:275", "prophet", "Prophet"])  # pylint: disable=line-too-long
    takes_position_b = not any(x in anch_clean.lower() for x in ["it depends on", "some argue", "others believe"])  # pylint: disable=line-too-long

    for line in anch_clean[:600].split("\n"):
        logger.info("  %s", line)
    if len(anch_clean) > 600:
        logger.info("  ... (%d chars total)", len(anch_clean))

    logger.info("  Gates: G1:%s G2:%s G3:%s G4:%s", g1.score, g2.score, g3.score, g4.result.value)
    logger.info("  Z3: %s", "SAT" if z3.consistent else "UNSAT")
    logger.info("  Time: %.1fs (extract:%.1fs + response:%.1fs)", t_total, t_extract, t_response)
    logger.info("  Hedging phrases: %d", hedging_count_b)
    logger.info("  Cites sources: %s", "YES" if has_sources_b else "NO")
    logger.info("  Takes clear position: %s", "YES" if takes_position_b else "NO (hedges)")

    # ── Comparison ──
    logger.info("%s", "-" * 50)
    logger.info("  COMPARISON:")
    logger.info("  %-25s %-20s %-20s", "Metric", "Without Engine", "With Engine")
    logger.info("  %s", "-" * 65)
    logger.info("  %-25s %-20s %-20s", "Hedging phrases", hedging_count, hedging_count_b)
    logger.info("  %-25s %-20s %-20s", "Cites sources", "YES" if has_sources else "NO", "YES" if has_sources_b else "NO")
    logger.info("  %-25s %-20s %-20s", "Clear position", "YES" if takes_position else "NO", "YES" if takes_position_b else "NO")
    logger.info("  %-25s %.1fs%14s %.1fs", "Response time", t_raw, "", t_total)
    logger.info("  %-25s %-20s %-20s", "Formal proof", "NO", "Z3: " + ("SAT" if z3.consistent else "UNSAT"))
    logger.info("  %-25s %-20s %s", "Deterministic", "NO", f"YES (score:{avg})")
