"""
Tafsir Feedback — تخزين تقييم المراجع البشري بعد كل response.

After every pipeline response, the system asks for human feedback:
- ✅ صح
- ✅📝 صح مع ملاحظات
- ❌ خطأ
- ❌📝 خطأ مع ملاحظات
"""

import json
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional

from al_furqan.paths import DATA_TAFSIR_FEEDBACK


class FeedbackVerdict(str, Enum):
    """FeedbackVerdict class."""

    CORRECT = "correct"  # ✅ صح
    CORRECT_WITH_NOTES = "correct_notes"  # ✅📝 صح مع ملاحظات
    WRONG = "wrong"  # ❌ خطأ
    WRONG_WITH_NOTES = "wrong_notes"  # ❌📝 خطأ مع ملاحظات


@dataclass
class TafsirFeedback:  # pylint: disable=too-many-instance-attributes
    """A single feedback entry for a pipeline response."""

    # Auto-generated
    feedback_id: str = ""
    timestamp: float = 0.0

    # From PipelineResult
    question: str = ""
    query_type: str = ""
    verse_refs: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    template_name: str = ""
    axioms_selected: list[str] = field(default_factory=list)
    gates_selected: list[str] = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)
    llm_response: str = ""
    llm_calls: int = 0
    total_time_ms: float = 0.0
    model: str = ""

    # Human review
    reviewer: str = ""
    verdict: str = ""  # FeedbackVerdict value
    notes: str = ""  # ملاحظات (for correct_notes / wrong_notes)


class TafsirFeedbackStore:
    """
    Stores and retrieves human feedback on tafsir pipeline responses.
    """

    VALID_VERDICTS = {v.value for v in FeedbackVerdict}

    def __init__(self, storage_dir: str = str(DATA_TAFSIR_FEEDBACK)):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    def _generate_id(self) -> str:
        return str(uuid.uuid4())[:8]

    def _path(self, feedback_id: str) -> str:
        return os.path.join(self.storage_dir, f"{feedback_id}.json")

    def store(self, feedback: TafsirFeedback) -> str:
        """
        Store a feedback entry. Returns feedback_id.
        """
        if feedback.verdict not in self.VALID_VERDICTS:
            raise ValueError(
                f"Invalid verdict: {feedback.verdict}. Must be one of {self.VALID_VERDICTS}"
            )  # pylint: disable=line-too-long

        if not feedback.feedback_id:
            feedback.feedback_id = self._generate_id()
        if not feedback.timestamp:
            feedback.timestamp = time.time()

        path = self._path(feedback.feedback_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(feedback), f, ensure_ascii=False, indent=2)

        return feedback.feedback_id

    def get(self, feedback_id: str) -> Optional[TafsirFeedback]:
        """Get a feedback entry by ID."""
        path = self._path(feedback_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return TafsirFeedback(**data)

    def list_all(self) -> list[TafsirFeedback]:
        """List all feedback entries."""
        entries = []
        for fname in sorted(os.listdir(self.storage_dir)):
            if fname.endswith(".json"):
                path = os.path.join(self.storage_dir, fname)
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                entries.append(TafsirFeedback(**data))
        return entries

    def get_stats(self) -> dict:
        """Get feedback statistics."""
        entries = self.list_all()
        total = len(entries)
        by_verdict = {}
        for e in entries:
            by_verdict[e.verdict] = by_verdict.get(e.verdict, 0) + 1

        correct = by_verdict.get("correct", 0) + by_verdict.get("correct_notes", 0)
        wrong = by_verdict.get("wrong", 0) + by_verdict.get("wrong_notes", 0)

        return {
            "total": total,
            "correct": correct,
            "wrong": wrong,
            "accuracy": round(correct / total * 100, 1) if total > 0 else 0,
            "by_verdict": by_verdict,
        }


def create_feedback_from_result(
    result, reviewer: str = "", verdict: str = "", notes: str = ""
) -> TafsirFeedback:  # pylint: disable=line-too-long
    """
    Create a TafsirFeedback from a PipelineResult.

    Args:
        result: PipelineResult from the pipeline
        reviewer: Who is reviewing
        verdict: FeedbackVerdict value
        notes: Optional notes
    """
    sel = result.reasoning_plan.axiom_selection
    axioms = [a["name"] for a in sel.selected_axioms] if sel else []
    gates = [g["name"] for g in sel.selected_gates] if sel else []

    return TafsirFeedback(
        question=result.question,
        query_type=result.query_analysis.query_type.value,
        verse_refs=result.query_analysis.verse_refs,
        topics=result.query_analysis.topics,
        template_name=result.reasoning_plan.template_name,
        axioms_selected=axioms,
        gates_selected=gates,
        tool_calls=result.tool_calls,
        llm_response=result.llm_response,
        llm_calls=result.llm_calls,
        total_time_ms=result.total_time_ms,
        model=result.model,
        reviewer=reviewer,
        verdict=verdict,
        notes=notes,
    )
