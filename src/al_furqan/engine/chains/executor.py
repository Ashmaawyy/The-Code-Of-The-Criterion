"""
Chain Executor — Runs guided reasoning chains through an LLM.

The LLM is used ONLY to extract structured facts from input text.
Scoring is done separately by the DeterministicScorer.
"""

from collections.abc import Callable

from al_furqan.engine.gates.base import Gate


class ChainExecutor:
    """
    Executes guided chain questions through an LLM function.

    The LLM extracts facts; it does NOT score or judge.
    """

    def __init__(self, llm_fn: Callable[[str], str]):
        """
        Args:
            llm_fn: A callable that takes a prompt string and returns the LLM's
                     text response. This is the ONLY place LLM calls happen.
        """
        self.llm_fn = llm_fn

    def execute_chain(
        self,
        question: str,
        gate: Gate,
        context: str = "",
    ) -> dict:
        """
        Execute guided chain questions for a gate through the LLM.

        Sends each chain question to the LLM with accumulated context,
        then returns structured extraction results.

        Args:
            question: The original question/claim being evaluated.
            gate: The Gate instance whose chain questions to execute.
            context: Additional context about the system being evaluated.

        Returns:
            Dictionary with extracted facts keyed by question index.
        """
        chain_questions = gate.get_chain_questions()
        extractions: dict = {}
        accumulated_context = []

        if context:
            accumulated_context.append(f"Context: {context}")
        accumulated_context.append(f"Question being evaluated: {question}")

        for i, cq in enumerate(chain_questions):
            prompt = self._build_prompt(cq, accumulated_context)
            response = self.llm_fn(prompt)
            extractions[f"q{i}"] = response
            accumulated_context.append(f"Q{i}: {cq}\nA{i}: {response}")

        return extractions

    def execute_all_gates(
        self,
        question: str,
        gates: list[Gate],
        context: str = "",
    ) -> dict:
        """
        Execute chains for all gates.

        Returns:
            Dictionary mapping gate names to their extraction results.
        """
        all_extractions = {}
        for gate in gates:
            all_extractions[gate.name] = self.execute_chain(question, gate, context)
        return all_extractions

    @staticmethod
    def _build_prompt(chain_question: str, accumulated_context: list[str]) -> str:
        """Build a prompt for the LLM with accumulated context."""
        parts = [
            "You are a fact extraction engine. Answer the following question "
            "based ONLY on the provided context. Extract facts, not opinions.",
            "",
        ]
        parts.extend(accumulated_context)
        parts.append("")
        parts.append(f"Question: {chain_question}")
        parts.append("")
        parts.append("Answer concisely with extracted facts only:")
        return "\n".join(parts)
