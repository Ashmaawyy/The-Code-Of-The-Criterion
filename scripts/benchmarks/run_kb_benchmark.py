#!/usr/bin/env python3
"""
KB Impact Benchmark — مدارسة سورة الأنعام
Measures the impact of Sheikh Ahmad Al-Sayyid's tafsir KB on model understanding.

Run A: Zero-shot (no KB)
Run B: KB-augmented (with extracted entries)
Scoring: LLM-as-judge on accuracy, depth, alignment (1-5 each)
"""

import json
import logging
import os
import sys
import time
import sqlite3  # pylint: disable=multiple-imports
from pathlib import Path

# Add project source to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from al_furqan import setup_logging  # pylint: disable=wrong-import-position
from al_furqan.providers import LLMConfig, create_llm  # pylint: disable=wrong-import-position

logger = logging.getLogger(__name__)

# --- Config ---
API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
if not API_KEY:
    raise SystemExit("DASHSCOPE_API_KEY environment variable not set")
MODEL = "qwen3.5-397b-a17b"

BENCHMARK_PATH = Path(__file__).parent.parent.parent / "data" / "benchmark" / "kb_impact_benchmark_v1.json"
DB_PATH = Path(__file__).parent.parent.parent / "data" / "review" / "proposed_edges.db"
RESULTS_PATH = Path(__file__).parent.parent.parent / "data" / "benchmark" / "results_v1.json"


def make_llm(system_prompt: str = ""):
    """Execute make_llm."""
    config = LLMConfig(
        provider="dashscope",
        model_name=MODEL,
        api_key=API_KEY,
        temperature=0.3,
        max_tokens=1500,
        system_prompt=system_prompt,
    )
    return create_llm(config)


def load_kb_entries():
    """Load all 67 KB entries from the proposed_edges DB."""
    db = sqlite3.connect(str(DB_PATH))
    cur = db.cursor()
    cur.execute("""
        SELECT source_node, target_node, edge_type, provenance, llm_reasoning, llm_confidence
        FROM proposed_edges ORDER BY ROWID
    """)
    rows = cur.fetchall()
    db.close()

    entries = []
    for r in rows:
        entries.append({
            "source": r[0],
            "target": r[1],
            "type": r[2],
            "provenance": r[3],
            "reasoning": r[4],
            "confidence": r[5],
        })
    return entries


def format_kb_context(entries):
    """Format KB entries as context for the model."""
    lines = ["# قاعدة معرفة تفسيرية — مدارسة سورة الأنعام (الشيخ أحمد السيد)\n"]
    for i, e in enumerate(entries, 1):
        lines.append(f"## [{i}] {e['source']} → {e['target']} ({e['type']})")
        lines.append(f"الثقة: {e['confidence']}")
        lines.append(f"التفسير: {e['reasoning']}")
        lines.append("")
    return "\n".join(lines)


def ask_model(question: str, kb_context: str = None) -> str:
    """Ask the model a question, optionally with KB context."""
    if kb_context:
        system = (
            "أنت عالم متخصص في تفسير القرآن الكريم. "
            "استخدم قاعدة المعرفة التفسيرية المرفقة (من دروس الشيخ أحمد السيد في مدارسة سورة الأنعام) للإجابة. "  # pylint: disable=line-too-long
            "أجب بالعربية الفصحى. كن دقيقاً ومفصلاً.\n\n"
            + kb_context
        )
    else:
        system = (
            "أنت عالم متخصص في تفسير القرآن الكريم. "
            "أجب بالعربية الفصحى. كن دقيقاً ومفصلاً."
        )

    llm = make_llm(system_prompt=system)
    return llm.generate(question)


def judge_answer(question: str, answer: str, ground_truth: str) -> dict:
    """Use LLM-as-judge to score an answer."""
    prompt = f"""أنت حَكَم محايد. قيّم الإجابة التالية مقارنة بالإجابة المرجعية (من تفسير الشيخ أحمد السيد).  # pylint: disable=line-too-long

السؤال: {question}

الإجابة المرجعية (الشيخ أحمد السيد): {ground_truth}

الإجابة المُقيَّمة: {answer}

قيّم على 3 محاور (1-5 لكل محور):
1. **الدقة** — هل الإجابة صحيحة علمياً وشرعياً؟
2. **العمق** — هل فيها تفصيل وتحليل أم سطحية؟
3. **التوافق** — هل تتوافق مع منهج الشيخ أحمد السيد في التفسير؟

أجب بـ JSON فقط بهذا الشكل:
{{"accuracy": X, "depth": X, "alignment": X, "notes": "ملاحظة قصيرة"}}"""

    llm = make_llm()
    text = llm.generate(prompt).strip()

    # Extract JSON from response
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    import re  # pylint: disable=import-outside-toplevel
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{[^}]+\}', text)
        if match:
            try:
                return json.loads(match.group())
            except Exception:  # pylint: disable=broad-exception-caught
                pass
        return {"accuracy": 0, "depth": 0, "alignment": 0, "notes": f"Parse error: {text[:200]}"}


def main():  # pylint: disable=too-many-locals, too-many-statements
    """Execute main."""
    setup_logging()
    logger.info("=" * 60)
    logger.info("KB Impact Benchmark - مدارسة سورة الأنعام")
    logger.info("=" * 60)

    # Load benchmark
    with open(BENCHMARK_PATH) as f:  # pylint: disable=unspecified-encoding
        benchmark = json.load(f)

    questions = benchmark["questions"]
    logger.info("Questions: %d", len(questions))

    # Load KB
    kb_entries = load_kb_entries()
    kb_context = format_kb_context(kb_entries)
    logger.info("KB entries: %d", len(kb_entries))
    logger.info("KB context size: %d chars", len(kb_context))

    results = {
        "benchmark": benchmark["benchmark_name"],
        "model": MODEL,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "questions": [],
        "summary": {},
    }

    total_a = {"accuracy": 0, "depth": 0, "alignment": 0}
    total_b = {"accuracy": 0, "depth": 0, "alignment": 0}

    for i, q in enumerate(questions):  # pylint: disable=unused-variable
        qid = q["id"]
        logger.info("%s", "-" * 50)
        logger.info("[%s] (%s) %s...", qid, q["level"], q["question"][:60])

        # --- Run A: Zero-shot ---
        logger.info("  Run A (zero-shot)...")
        answer_a = ask_model(q["question"])
        time.sleep(2)  # Rate limit
        score_a = judge_answer(q["question"], answer_a, q["kb_ground_truth"])
        time.sleep(2)
        logger.info("  Run A done: acc=%s dep=%s ali=%s", score_a.get("accuracy", 0), score_a.get("depth", 0), score_a.get("alignment", 0))

        # --- Run B: KB-augmented ---
        logger.info("  Run B (KB-augmented)...")
        answer_b = ask_model(q["question"], kb_context=kb_context)
        time.sleep(2)
        score_b = judge_answer(q["question"], answer_b, q["kb_ground_truth"])
        time.sleep(2)
        logger.info("  Run B done: acc=%s dep=%s ali=%s", score_b.get("accuracy", 0), score_b.get("depth", 0), score_b.get("alignment", 0))

        # Track totals
        for k in ["accuracy", "depth", "alignment"]:
            total_a[k] += score_a.get(k, 0)
            total_b[k] += score_b.get(k, 0)

        results["questions"].append({
            "id": qid,
            "level": q["level"],
            "verse_ref": q["verse_ref"],
            "question": q["question"],
            "ground_truth": q["kb_ground_truth"],
            "run_a": {"answer": answer_a, "scores": score_a},
            "run_b": {"answer": answer_b, "scores": score_b},
        })

    # Summary
    n = len(questions)
    summary = {
        "total_questions": n,
        "run_a_avg": {k: round(v / n, 2) for k, v in total_a.items()},
        "run_b_avg": {k: round(v / n, 2) for k, v in total_b.items()},
        "improvement": {
            k: round((total_b[k] - total_a[k]) / max(total_a[k], 1) * 100, 1)
            for k in ["accuracy", "depth", "alignment"]
        },
    }
    results["summary"] = summary

    # Save
    os.makedirs(RESULTS_PATH.parent, exist_ok=True)
    with open(RESULTS_PATH, "w") as f:  # pylint: disable=unspecified-encoding
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Print summary
    logger.info("%s", "=" * 60)
    logger.info("النتائج")
    logger.info("%s", "=" * 60)
    logger.info("%-15s %10s %10s %10s", "المحور", "بدون KB", "مع KB", "التحسن %")
    logger.info("%s", "-" * 50)
    for k, label in [("accuracy", "الدقة"), ("depth", "العمق"), ("alignment", "التوافق")]:
        a = summary["run_a_avg"][k]
        b = summary["run_b_avg"][k]
        imp = summary["improvement"][k]
        logger.info("%-15s %10.2f %10.2f %+9.1f%%", label, a, b, imp)

    overall_a = sum(summary["run_a_avg"].values()) / 3
    overall_b = sum(summary["run_b_avg"].values()) / 3
    overall_imp = round((overall_b - overall_a) / max(overall_a, 0.01) * 100, 1)
    logger.info("%s", "-" * 50)
    logger.info("%-15s %10.2f %10.2f %+9.1f%%", "الإجمالي", overall_a, overall_b, overall_imp)

    logger.info("Results saved: %s", RESULTS_PATH)


if __name__ == "__main__":
    main()
