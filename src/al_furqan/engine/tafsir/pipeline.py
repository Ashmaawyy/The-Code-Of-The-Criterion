"""
Tafsir RAG Pipeline — End-to-end Engine-Guided Reasoning.

Orchestrates:
① Query Analyzer → ② Reasoning Plan Builder → ③ LLM + Tools → ④ Human Review

The pipeline builds the plan and manages tool execution.
The LLM does the thinking and searching.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Callable

from al_furqan.kb.tafsir.query_analyzer import analyze_query, QueryAnalysis
from al_furqan.kb.tafsir.kb_tools import TafsirKBTools
from al_furqan.kb.tafsir.tool_executor import (
    ToolExecutor,
    parse_tool_calls_from_response,
)
from al_furqan.engine.tafsir.reasoning_plan_builder import (
    ReasoningPlanBuilder,
    ReasoningPlan,
)
from al_furqan.engine.tafsir.feedback import (  # pylint: disable=unused-import
    TafsirFeedbackStore,
    create_feedback_from_result,
)

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:  # pylint: disable=too-many-instance-attributes
    """Complete result from the Tafsir RAG pipeline."""

    # Input
    question: str
    query_analysis: QueryAnalysis
    reasoning_plan: ReasoningPlan

    # Execution
    llm_response: str
    tool_calls: list[dict] = field(default_factory=list)
    tool_results: list[dict] = field(default_factory=list)

    # Metadata
    total_time_ms: float = 0.0
    llm_calls: int = 0
    model: str = ""

    def summary(self) -> str:
        """Human-readable summary."""
        lines = [
            f"Question: {self.question[:80]}...",
            f"Type: {self.query_analysis.query_type.value}",
            f"Template: {self.reasoning_plan.template_name}",
            f"Verses: {self.query_analysis.verse_refs}",
            f"Topics: {self.query_analysis.topics}",
        ]

        # Show dynamically selected axioms/gates
        sel = self.reasoning_plan.axiom_selection
        if sel:
            ax_names = [a["name"] for a in sel.selected_axioms]
            g_names = [g["name"] for g in sel.selected_gates]
            lines.append(f"Axioms (LLM-selected): {ax_names}")
            lines.append(f"Gates (LLM-selected): {g_names}")

        lines.extend(
            [
                f"Tool calls: {len(self.tool_calls)}",
                f"LLM calls: {self.llm_calls}",
                f"Time: {self.total_time_ms:.0f}ms",
            ]
        )
        return "\n".join(lines) + "\n"


class TafsirPipeline:
    """
    End-to-end Tafsir RAG pipeline.

    Usage:
        pipeline = TafsirPipeline(
            db_path="data_archive/review/proposed_edges.db",
            llm_call=my_llm_function,
        )
        result = pipeline.run("إيه علاقة أول 4 آيات بالآية 5؟")
        print(result.llm_response)
    """

    MAX_TOOL_ROUNDS = 5  # Max rounds of tool calling

    def __init__(
        self,
        db_path: str,
        llm_call: Callable,
        model_name: str = "",
        default_surah: int = 6,
    ):
        """
        Args:
            db_path: Path to proposed_edges.db
            llm_call: Function that calls the LLM.
                      Signature: llm_call(messages, tools=None) -> response_dict
                      response_dict must have: {"content": str, "tool_calls": list|None}
            model_name: Name of the model (for logging)
            default_surah: Default surah for verse extraction
        """
        self.kb_tools = TafsirKBTools(db_path)
        self.tool_executor = ToolExecutor(self.kb_tools)
        self.plan_builder = ReasoningPlanBuilder()
        self.feedback_store = TafsirFeedbackStore()
        self.llm_call = llm_call
        self.model_name = model_name
        self.default_surah = default_surah

    def run(self, question: str) -> PipelineResult:  # pylint: disable=too-many-locals
        """
        Run the full pipeline on a question.

        ① Analyze query
        ② Build reasoning plan
        ③ LLM executes plan with tools
        ④ Return result (for human review)
        """
        start = time.time()
        self.tool_executor.reset_log()

        # ① Query Analyzer
        analysis = analyze_query(question, self.default_surah)
        logger.info(
            "Query type: %s, verses: %s", analysis.query_type, analysis.verse_refs
        )

        # ② Build Reasoning Plan (LLM selects axioms/gates dynamically)
        plan = self.plan_builder.build(analysis, llm_call=self.llm_call)
        logger.info(
            "Template: %s, steps: %d", plan.template_name, len(plan.reasoning_steps)
        )

        # ③ LLM Execution with Tools
        messages = [
            {"role": "system", "content": plan.system_prompt},
            {"role": "user", "content": question},
        ]

        all_tool_calls = []
        all_tool_results = []
        llm_calls = 0
        final_response = ""

        for round_num in range(self.MAX_TOOL_ROUNDS):
            # Call LLM
            llm_calls += 1
            response = self.llm_call(
                messages=messages,
                tools=plan.tool_definitions,
            )

            content = response.get("content", "")
            tool_calls = response.get("tool_calls", None)

            # If LLM made tool calls, execute them and continue
            if tool_calls:
                for tc in tool_calls:
                    tool_name = tc.get("function", {}).get("name", tc.get("name", ""))
                    arguments = tc.get("function", {}).get(
                        "arguments", tc.get("arguments", {})
                    )

                    # Parse arguments if string
                    if isinstance(arguments, str):
                        try:
                            arguments = json.loads(arguments)
                        except json.JSONDecodeError:
                            arguments = {}

                    # Execute tool
                    result = self.tool_executor.execute(tool_name, arguments)

                    all_tool_calls.append({"name": tool_name, "arguments": arguments})
                    all_tool_results.append({"tool": tool_name, "result": result[:500]})

                    # Add to conversation
                    messages.append(
                        {
                            "role": "assistant",
                            "content": content or None,
                            "tool_calls": [tc],
                        }
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "content": result,
                            "tool_call_id": tc.get("id", f"call_{round_num}"),
                        }
                    )

                continue  # Next round — LLM gets tool results

            # No tool calls — LLM gave final answer
            final_response = content

            # Check if the response contains inline tool calls (for non-function-calling models)
            if not all_tool_calls:
                inline_calls = parse_tool_calls_from_response(content)
                if inline_calls:
                    # Execute inline tools and re-prompt
                    tool_results_text = []
                    for ic in inline_calls:
                        result = self.tool_executor.execute(ic["name"], ic["arguments"])
                        all_tool_calls.append(ic)
                        all_tool_results.append(
                            {"tool": ic["name"], "result": result[:500]}
                        )
                        tool_results_text.append(result)

                    messages.append({"role": "assistant", "content": content})
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                "نتائج البحث في قاعدة المعرفة:\n\n"
                                + "\n\n---\n\n".join(tool_results_text)
                                + "\n\nبناءً على هذه النتائج، أكمل إجابتك."
                            ),
                        }
                    )
                    continue

            break  # Got final response

        elapsed = (time.time() - start) * 1000

        return PipelineResult(
            question=question,
            query_analysis=analysis,
            reasoning_plan=plan,
            llm_response=final_response,
            tool_calls=all_tool_calls,
            tool_results=all_tool_results,
            total_time_ms=elapsed,
            llm_calls=llm_calls,
            model=self.model_name,
        )

    def submit_feedback(
        self,
        result: PipelineResult,
        verdict: str,
        reviewer: str = "",
        notes: str = "",
    ) -> str:
        """
        Submit human feedback for a pipeline result.

        Args:
            result: The PipelineResult to review.
            verdict: One of: "correct", "correct_notes", "wrong", "wrong_notes"
            reviewer: Who is reviewing (name or ID).
            notes: Optional notes (required for correct_notes / wrong_notes).

        Returns:
            feedback_id
        """
        feedback = create_feedback_from_result(
            result=result,
            reviewer=reviewer,
            verdict=verdict,
            notes=notes,
        )
        return self.feedback_store.store(feedback)

    def get_feedback_stats(self) -> dict:
        """Get feedback statistics."""
        return self.feedback_store.get_stats()
