"""Tests for ChainExecutor — with mock LLM."""

from al_furqan.engine.chains.executor import ChainExecutor
from al_furqan.engine.gates.source_integrity import SourceIntegrityGate
from al_furqan.engine.gates.structural_consistency import StructuralConsistencyGate
from al_furqan.engine.gates.origin_aware import OriginAwareGate


class TestChainExecutor:
    """Test chain execution with mock LLM function."""

    def test_execute_chain_calls_llm_per_question(self):
        """LLM is called once per chain question."""
        call_count = 0

        def mock_llm(_prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"Answer {call_count}"

        executor = ChainExecutor(llm_fn=mock_llm)
        gate = SourceIntegrityGate()
        result = executor.execute_chain("Test question", gate)

        assert call_count == len(gate.get_chain_questions())
        assert len(result) == call_count

    def test_execute_chain_returns_dict_with_q_keys(self):
        """Results keyed as q0, q1, q2, etc."""
        def mock_llm(_prompt: str) -> str:
            return "extracted fact"

        executor = ChainExecutor(llm_fn=mock_llm)
        gate = SourceIntegrityGate()
        result = executor.execute_chain("Test", gate)

        for i in range(len(gate.get_chain_questions())):
            assert f"q{i}" in result

    def test_execute_chain_accumulates_context(self):
        """Each subsequent question includes previous answers in prompt."""
        prompts_seen = []

        def mock_llm(prompt: str) -> str:
            prompts_seen.append(prompt)
            return "some answer"

        executor = ChainExecutor(llm_fn=mock_llm)
        gate = StructuralConsistencyGate()
        executor.execute_chain("Test question", gate, context="Some context")

        # First prompt should have context
        assert "Some context" in prompts_seen[0]
        # Later prompts should include previous answers
        if len(prompts_seen) > 1:
            assert "some answer" in prompts_seen[1]

    def test_execute_all_gates(self):
        """Execute chains for multiple gates."""
        def mock_llm(_prompt: str) -> str:
            return "fact"

        executor = ChainExecutor(llm_fn=mock_llm)
        gates = [SourceIntegrityGate(), OriginAwareGate()]
        results = executor.execute_all_gates("Test", gates)

        assert len(results) == 2
        for gate in gates:
            assert gate.name in results

    def test_execute_chain_with_empty_context(self):
        """Works with no additional context."""
        def mock_llm(_prompt: str) -> str:
            return "extracted"

        executor = ChainExecutor(llm_fn=mock_llm)
        gate = OriginAwareGate()
        result = executor.execute_chain("Does Islam acknowledge God?", gate)

        assert len(result) == len(gate.get_chain_questions())

    def test_prompt_contains_question(self):
        """The original question appears in prompts sent to LLM."""
        prompts_seen = []

        def mock_llm(prompt: str) -> str:
            prompts_seen.append(prompt)
            return "answer"

        executor = ChainExecutor(llm_fn=mock_llm)
        gate = OriginAwareGate()
        executor.execute_chain("Is capitalism fair?", gate)

        assert any("Is capitalism fair?" in p for p in prompts_seen)
