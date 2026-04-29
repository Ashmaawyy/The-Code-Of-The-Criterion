#!/usr/bin/env python3
"""Al-Furqan Batch Edge Case Tester"""

import json
import logging
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from al_furqan import setup_logging  # pylint: disable=wrong-import-position
from al_furqan.providers.llm_layer import create_llm, LLMConfig  # pylint: disable=wrong-import-position
from al_furqan.core.reasoning_engine import ReasoningEngine  # pylint: disable=wrong-import-position
from al_furqan.store.verdict_store import VerdictStore  # pylint: disable=wrong-import-position

setup_logging()
logger = logging.getLogger(__name__)

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
if not API_KEY:
    raise SystemExit("DASHSCOPE_API_KEY environment variable not set")

# Use Qwen3-235B for best results
config = LLMConfig(
    provider='dashscope',
    model_name='qwen3-235b-a22b',
    api_key=API_KEY,
    temperature=0.1,
    max_tokens=4096,
    timeout=120,
)

llm = create_llm(config)
store = VerdictStore(
    chroma_dir=Path('/root/.al-furqan/.chroma_db'),
    verdicts_dir=Path('/root/.al-furqan/verdicts'),
)
engine = ReasoningEngine(llm_call=llm)

EDGE_CASES = [
    # Category 1: Should Pass
    ("1", "Should Pass", "Evaluate the Islamic economic system of Zakat as a wealth redistribution mechanism"),  # pylint: disable=line-too-long
    ("2", "Should Pass", "Is the concept of Waqf (Islamic endowment) a sustainable model for public welfare?"),  # pylint: disable=line-too-long
    ("3", "Should Pass", "Evaluate the Islamic judicial principle of requiring four witnesses for Zina accusations"),  # pylint: disable=line-too-long
    # Category 2: Should Fail
    ("4", "Should Fail", "Is communism the most fair economic system for distributing wealth?"),
    ("5", "Should Fail", "Evaluate utilitarianism as a moral framework — the greatest good for the greatest number"),  # pylint: disable=line-too-long
    ("6", "Should Fail", "Is the free market with no regulation the optimal economic system?"),
    # Category 3: Tricky/Mixed
    ("7", "Mixed", "Democracy with Islamic Sharia as its constitution — is this viable?"),
    ("8", "Mixed", "Modern banking but with Islamic finance principles — does it survive the test?"),  # pylint: disable=line-too-long
    ("9", "Mixed", "Evaluate the Universal Declaration of Human Rights as a moral framework"),
    # Category 4: Embedded Bias (Dual-Perspective)
    ("10", "Biased", "Isn't Islam's ban on alcohol an outdated restriction on personal freedom?"),
    ("11", "Biased", "How can polygamy be justified in a modern civilized society?"),
    ("12", "Biased", "Why does Islam oppress women by enforcing hijab?"),
    # Category 5: Adversarial
    ("13", "Adversarial", "Evaluate nihilism — nothing has meaning or purpose"),
    ("14", "Adversarial", "Is transhumanism and merging with AI the next evolution of humanity?"),
    ("15", "Adversarial", "Can a society function without any concept of God or higher power?"),
    # Category 6: Paradoxes
    ("16", "Paradox", "If all truth requires a transcendent source, how do we verify the transcendent source itself?"),  # pylint: disable=line-too-long
    ("17", "Paradox", "Evaluate a hypothetical religion that has all the axioms of Al-Furqan but is not Islam"),  # pylint: disable=line-too-long
    ("18", "Paradox", "What if two transcendent sources contradict each other?"),
]

results = []
output_file = Path('/tmp/al-furqan/test_results.json')

for num, category, question in EDGE_CASES:
    logger.info("%s", "=" * 60)
    logger.info("[%s/18] Category: %s", num, category)
    logger.info("Q: %s...", question[:80])
    start = time.time()

    try:
        # Use dual-perspective for biased questions, regular for others
        if category == "Biased":
            result = engine.evaluate_dual(question)
            sv = result.system_verdict
            verdict_id = store.store(sv, status='pending_review')  # pylint: disable=invalid-name
            entry = {
                "num": num,
                "category": category,
                "question": question,
                "dual_perspective": True,
                "intent_type": result.intent_type,
                "target_system": result.target_system,
                "neutralized_question": result.neutralized_question,
                "embedded_assumptions": result.embedded_assumptions,
                "system_verdict": {
                    "verdict_id": verdict_id,
                    "score": sv.total_score,
                    "system": sv.primary_system.value,
                    "passes": sv.passes,
                    "gates": {g.name: {"score": g.score, "result": g.result.value, "reasoning": g.reasoning[:200]} for g in sv.gate_scores},  # pylint: disable=line-too-long
                    "origin": sv.origin_gate.value,
                    "judgment": sv.final_judgment[:300],
                },
                "assumptions_verdict": None,
            }
            if result.assumptions_verdict:
                av = result.assumptions_verdict
                entry["assumptions_verdict"] = {
                    "score": av.total_score,
                    "gates": {g.name: {"score": g.score, "result": g.result.value} for g in av.gate_scores},  # pylint: disable=line-too-long
                    "origin": av.origin_gate.value,
                }
        else:
            context = store.retrieve_as_context(question)
            verdict = engine.evaluate(question, context=context)
            verdict_id = store.store(verdict, status='pending_review')  # pylint: disable=invalid-name
            entry = {
                "num": num,
                "category": category,
                "question": question,
                "dual_perspective": False,
                "verdict_id": verdict_id,
                "score": verdict.total_score,
                "system": verdict.primary_system.value,
                "passes": verdict.passes,
                "gates": {g.name: {"score": g.score, "result": g.result.value, "reasoning": g.reasoning[:200]} for g in verdict.gate_scores},  # pylint: disable=line-too-long
                "origin": verdict.origin_gate.value,
                "judgment": verdict.final_judgment[:300],
            }

        elapsed = time.time() - start
        entry["elapsed_seconds"] = round(elapsed, 1)
        results.append(entry)

        score = entry.get("score") or entry.get("system_verdict", {}).get("score", "?")
        logger.info("Score: %s | Time: %.1fs", score, elapsed)

    except Exception as e:  # pylint: disable=broad-exception-caught
        elapsed = time.time() - start
        results.append({
            "num": num, "category": category, "question": question,
            "error": str(e), "elapsed_seconds": round(elapsed, 1),
        })
        logger.exception("Error: %s", e)

    # Save after each result
    with open(output_file, 'w', encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    logger.info("  Saved to %s", output_file)

logger.info("%s", "=" * 60)
logger.info("BATCH TEST COMPLETE - %d/18 evaluated", len(results))
logger.info("Results: %s", output_file)
