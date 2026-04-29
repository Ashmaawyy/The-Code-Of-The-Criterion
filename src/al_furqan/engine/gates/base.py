"""
Abstract Gate Base Class

All gates implement this interface. The evaluate() method is PURE PYTHON —
no LLM calls allowed. LLM extraction happens in ChainExecutor; gates only
receive already-extracted facts.
"""

from abc import ABC, abstractmethod
from al_furqan.engine.models import GateScore


class Gate(ABC):
    """Abstract base class for all Al-Furqan evaluation gates."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Gate name identifier."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this gate evaluates."""

    @abstractmethod
    def evaluate(self, chain_results: dict) -> GateScore:
        """
        Deterministic scoring from chain extraction results.

        NO LLM calls here — pure Python logic only.

        Args:
            chain_results: Dictionary of extracted facts from ChainExecutor.

        Returns:
            GateScore with name, score (0-100), result (Survive/Fail), reasoning.
        """

    @abstractmethod
    def get_chain_questions(self) -> list[str]:
        """
        Return guided chain questions for LLM extraction.

        These questions are sent to the LLM to extract structured facts
        from the input text. Each question builds on previous answers.
        """
