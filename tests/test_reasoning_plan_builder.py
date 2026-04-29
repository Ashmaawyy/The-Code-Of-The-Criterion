"""Tests for the Reasoning Plan Builder."""

# pylint: disable=redefined-outer-name

import pytest
from al_furqan.kb.tafsir.query_analyzer import analyze_query, QueryType
from al_furqan.engine.tafsir.reasoning_plan_builder import ReasoningPlanBuilder, ReasoningPlan


@pytest.fixture
def builder():
    """Execute builder."""
    return ReasoningPlanBuilder()


class TestPlanBuilding:
    """Test that plans are built correctly for each query type."""
    def test_tafsir_plan(self, builder):
        """Test tafsir_plan."""
        analysis = analyze_query("ما تفسير الآية 6:5؟")
        plan = builder.build(analysis)
        assert isinstance(plan, ReasoningPlan)
        assert plan.template_name == "تفسير آية"
        assert len(plan.axiom_guidelines) > 0
        assert len(plan.gate_checks) > 0
        assert len(plan.reasoning_steps) > 0
    def test_verse_link_plan(self, builder):
        """Test verse_link_plan."""
        analysis = analyze_query("إيه علاقة أول أربع آيات من سورة الأنعام بالآية رقم 5")
        plan = builder.build(analysis)
        assert plan.template_name == "ربط بين آيات"
        assert analysis.query_type == QueryType.VERSE_LINK
    def test_comparison_plan(self, builder):
        """Test comparison_plan."""
        analysis = analyze_query("هل تقدر تجيب لي علاقة شبيهة من سور ثانية؟")
        plan = builder.build(analysis)
        assert plan.template_name == "مقارنة بين سور"
    def test_seerah_plan(self, builder):
        """Test seerah_plan."""
        analysis = analyze_query("ما علاقة الآية بيوم بدر؟")
        plan = builder.build(analysis)
        assert plan.template_name == "ربط بالسيرة"
    def test_istinbat_plan(self, builder):
        """Test istinbat_plan."""
        analysis = analyze_query("ما الدروس المستفادة من الآية 6:5؟")
        plan = builder.build(analysis)
        assert plan.template_name == "استنباط ودروس"
    def test_general_plan(self, builder):
        """Test general_plan."""
        analysis = analyze_query("ما هو الإسلام؟")
        plan = builder.build(analysis)
        assert plan.template_name == "سؤال عام"


class TestSystemPrompt:
    """Test system prompt construction."""
    def test_prompt_has_axioms(self, builder):
        """Test prompt_has_axioms."""
        analysis = analyze_query("ما تفسير الآية 6:5؟")
        plan = builder.build(analysis)
        assert "المسلّمات" in plan.system_prompt
        assert "Axioms" in plan.system_prompt
    def test_prompt_has_gates(self, builder):
        """Test prompt_has_gates."""
        analysis = analyze_query("ما تفسير الآية 6:5؟")
        plan = builder.build(analysis)
        assert "بوابات الجودة" in plan.system_prompt
        assert "Source-Integrity" in plan.system_prompt
    def test_prompt_has_steps(self, builder):
        """Test prompt_has_steps."""
        analysis = analyze_query("ما تفسير الآية 6:5؟")
        plan = builder.build(analysis)
        assert "خطوات التنفيذ" in plan.system_prompt
        assert "search_kb_by_verse" in plan.system_prompt
    def test_prompt_has_kb_rules(self, builder):
        """Test prompt_has_kb_rules."""
        analysis = analyze_query("ما تفسير الآية 6:5؟")
        plan = builder.build(analysis)
        assert "مصدر مساعد" in plan.system_prompt
        assert "الشيخ أحمد السيد" in plan.system_prompt
    def test_verse_ref_resolved_in_steps(self, builder):
        """Test verse_ref_resolved_in_steps."""
        analysis = analyze_query("ما تفسير الآية 6:5؟")
        plan = builder.build(analysis)
        # Steps should have 6:5 not {verse_ref}
        assert "6:5" in plan.system_prompt
        assert "{verse_ref}" not in plan.system_prompt
    def test_topic_resolved_in_steps(self, builder):
        """Test topic_resolved_in_steps."""
        analysis = analyze_query("ما هي السنة الإلهية في سورة الأنعام؟")
        plan = builder.build(analysis)
        assert "السنة الإلهية" in plan.system_prompt


class TestToolDefinitions:
    """Test that plans include proper tool definitions."""
    def test_plan_has_tools(self, builder):
        """Test plan_has_tools."""
        analysis = analyze_query("ما تفسير الآية 6:5؟")
        plan = builder.build(analysis)
        assert len(plan.tool_definitions) == 4
    def test_tool_names(self, builder):
        """Test tool_names."""
        analysis = analyze_query("ما تفسير الآية 6:5؟")
        plan = builder.build(analysis)
        names = {t["function"]["name"] for t in plan.tool_definitions}
        assert "search_kb_by_verse" in names
        assert "search_kb_by_topic" in names
        assert "search_kb_by_relation" in names
        assert "get_verse_context" in names


class TestAxiomGateMapping:
    """Test that correct axioms and gates are selected per query type."""
    def test_tafsir_axioms(self, builder):
        """Test tafsir_axioms."""
        analysis = analyze_query("ما تفسير الآية 6:5؟")
        plan = builder.build(analysis)
        # TAFSIR should have design, network_effect, transcendence
        assert any("ترتيب الآيات" in a for a in plan.axiom_guidelines)  # design
        assert any("مرتبطة بسياقها" in a for a in plan.axiom_guidelines)  # network
    def test_seerah_axioms(self, builder):
        """Test seerah_axioms."""
        analysis = analyze_query("ما علاقة الآية بيوم بدر؟")
        plan = builder.build(analysis)
        # SEERAH should have final_court
        assert any("الوعد والوعيد" in a for a in plan.axiom_guidelines)
    def test_istinbat_gates(self, builder):
        """Test istinbat_gates."""
        analysis = analyze_query("ما الدروس المستفادة من الآية 6:5؟")
        plan = builder.build(analysis)
        # ISTINBAT should have mediation_zeroing gate
        assert any("Mediation-Zeroing" in g for g in plan.gate_checks)
    def test_verse_link_gates(self, builder):
        """Test verse_link_gates."""
        analysis = analyze_query("إيه علاقة أول أربع آيات بالآية 5")
        plan = builder.build(analysis)
        # VERSE_LINK should have structural_consistency
        assert any("Structural-Consistency" in g for g in plan.gate_checks)


# pylint: disable=too-few-public-methods
class TestKBSupplement:
    """Test that KB is always marked as supplement."""

    def test_kb_as_supplement(self, builder):
        """Test kb_as_supplement."""
        analysis = analyze_query("أي سؤال")
        plan = builder.build(analysis)
        assert plan.kb_as_supplement is True


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_query(self, builder):
        """Test empty_query."""
        analysis = analyze_query("")
        plan = builder.build(analysis)
        assert plan.template_name == "سؤال عام"
        assert len(plan.system_prompt) > 0

    def test_no_verse_refs(self, builder):
        """Test no_verse_refs."""
        analysis = analyze_query("ما هو التوحيد؟")
        plan = builder.build(analysis)
        # Should not crash even without verse refs
        assert len(plan.reasoning_steps) > 0
        assert "{verse_ref}" not in plan.system_prompt

    def test_multiple_verse_refs(self, builder):
        """Test multiple_verse_refs."""
        analysis = analyze_query("العلاقة بين 6:1 و 6:2 و 6:3 و 6:4 و 6:5")
        plan = builder.build(analysis)
        # Should use first verse ref in steps
        assert "6:1" in plan.system_prompt
