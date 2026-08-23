"""
Reasoning Plan Builder — يبني خطة تفكير كاملة للمودل.

Stage ② in the Engine-Guided RAG pipeline.

Takes a QueryAnalysis and builds a ReasoningPlan that includes:
- Axiom guidelines relevant to the question type
- Gate checks the LLM should self-verify against
- Step-by-step reasoning instructions
- KB tool definitions for the LLM to use
"""

from collections.abc import Callable
from dataclasses import dataclass

from al_furqan.engine.tafsir.axiom_selector import (  # pylint: disable=unused-import
    AxiomGateSelection,
    select_axioms_and_gates,
)
from al_furqan.engine.tafsir.reasoning_templates import (
    AXIOM_GUIDELINES,
    GATE_CHECKS,
    KB_USAGE_RULES,
    get_template,
)
from al_furqan.kb.tafsir.kb_tools import TafsirKBTools
from al_furqan.kb.tafsir.query_analyzer import QueryAnalysis


@dataclass
class ReasoningPlan:  # pylint: disable=too-many-instance-attributes
    """A complete reasoning plan for the LLM."""

    query_analysis: QueryAnalysis
    template_name: str
    axiom_guidelines: list[str]
    gate_checks: list[str]
    reasoning_steps: list[str]
    system_prompt: str
    tool_definitions: list[dict]
    axiom_selection: AxiomGateSelection | None = None
    kb_as_supplement: bool = True


class ReasoningPlanBuilder:  # pylint: disable=too-few-public-methods
    """
    Builds a reasoning plan from Axioms + Gates + Template.

    Two modes:
    - Static (default): Uses pre-mapped axioms/gates per query type.
    - Dynamic: LLM selects axioms/gates based on the raw Engine definitions.

    The plan is sent to the LLM along with KB tools.
    The LLM executes the plan and searches the KB itself.
    """

    SYSTEM_PREAMBLE = (
        "أنت عالم متخصص في تفسير القرآن الكريم ولديك معرفة واسعة "
        "بالتفاسير المختلفة وعلوم القرآن والحديث والسيرة.\n\n"
    )

    def build(
        self,
        analysis: QueryAnalysis,
        llm_call: Callable | None = None,
    ) -> ReasoningPlan:
        """
        Build a complete reasoning plan for the given query.

        Args:
            analysis: The analyzed user query.
            llm_call: Optional LLM function for dynamic axiom/gate selection.
                      If None, falls back to static template mapping.

        Returns:
            A ReasoningPlan with system prompt, steps, and tool definitions.
        """
        template = get_template(analysis.query_type)

        # Dynamic selection: LLM chooses axioms and gates
        if llm_call is not None:
            selection = select_axioms_and_gates(analysis.original_query, llm_call)
            axiom_texts = [
                f"{ax['name']}: {ax['description']} (السبب: {ax['reason']})"
                for ax in selection.selected_axioms
            ]
            gate_texts = [
                f"☐ {g['name']}: {g['check']} (السبب: {g['reason']})"
                for g in selection.selected_gates
            ]
        else:
            # Static fallback: use pre-mapped template
            selection = None
            axiom_texts = [
                AXIOM_GUIDELINES[a] for a in template["axioms"] if a in AXIOM_GUIDELINES
            ]
            gate_texts = [GATE_CHECKS[g] for g in template["gates"] if g in GATE_CHECKS]

        # Resolve reasoning steps with variable substitution
        steps = self._resolve_steps(template["steps"], analysis)

        # Build system prompt
        system_prompt = self._build_system_prompt(
            template_name=template["name"],
            axiom_texts=axiom_texts,
            gate_texts=gate_texts,
            steps=steps,
        )

        return ReasoningPlan(
            query_analysis=analysis,
            template_name=template["name"],
            axiom_guidelines=axiom_texts,
            gate_checks=gate_texts,
            reasoning_steps=steps,
            system_prompt=system_prompt,
            tool_definitions=TafsirKBTools.get_tool_definitions(),
            axiom_selection=selection,
        )

    def _resolve_steps(self, steps: list[str], analysis: QueryAnalysis) -> list[str]:
        """Replace {verse_ref} and {topic} placeholders in steps."""
        resolved = []
        for step in steps:
            s = step
            # Replace {verse_ref} with first verse or all verses
            if "{verse_ref}" in s:
                if analysis.verse_refs:
                    s = s.replace("{verse_ref}", analysis.verse_refs[0])
                else:
                    s = s.replace("{verse_ref}", "")

            # Replace {topic} with first topic or query keywords
            if "{topic}" in s:
                if analysis.topics:
                    s = s.replace("{topic}", analysis.topics[0])
                elif analysis.search_keywords_ar:
                    s = s.replace("{topic}", analysis.search_keywords_ar[0])
                else:
                    s = s.replace("{topic}", analysis.original_query[:50])

            resolved.append(s)
        return resolved

    def _build_system_prompt(
        self,
        template_name: str,
        axiom_texts: list[str],
        gate_texts: list[str],
        steps: list[str],
    ) -> str:
        """Build the complete system prompt."""
        sections = [self.SYSTEM_PREAMBLE]

        # Reasoning plan header
        sections.append(f"## خطة التفكير: {template_name}\n")

        # Axiom guidelines
        sections.append("### المسلّمات (Axioms):")
        for ax in axiom_texts:
            sections.append(f"- {ax}")
        sections.append("")

        # Gate checks
        sections.append("### بوابات الجودة (Gates) — تحقق منها قبل الإجابة:")
        for gate in gate_texts:
            sections.append(f"- {gate}")
        sections.append("")

        # Reasoning steps
        sections.append("### خطوات التنفيذ:")
        for i, step in enumerate(steps, 1):
            sections.append(f"{i}. {step}")
        sections.append("")

        # KB usage rules
        sections.append(KB_USAGE_RULES)

        return "\n".join(sections)
