"""Tests for Gate 1: Source Integrity (المصدر)."""

import pytest

from al_furqan.engine.gates.source_integrity import SourceIntegrityGate
from al_furqan.engine.models import GateResult

# pylint: disable=redefined-outer-name


@pytest.fixture
def gate():
    """Execute gate."""
    return SourceIntegrityGate()


class TestSourceIntegrityGate:
    """Test source integrity scoring with known inputs."""

    def test_divine_verifiable(self, gate):
        """Divine + verifiable = 100 → Survive."""
        result = gate.evaluate(
            {
                "source_type": "divine",
                "verifiable": True,
                "contradicts_primary": False,
            }
        )
        assert result.score == 100
        assert result.result == GateResult.SURVIVE

    def test_divine_unverifiable(self, gate):
        """Divine + unverifiable = 100 * 0.5 = 50 → Survive (at threshold)."""
        result = gate.evaluate(
            {
                "source_type": "divine",
                "verifiable": False,
                "contradicts_primary": False,
            }
        )
        assert result.score == 50
        assert result.result == GateResult.SURVIVE

    def test_prophetic_verifiable(self, gate):
        """Prophetic + verifiable = 80 → Survive."""
        result = gate.evaluate(
            {
                "source_type": "prophetic",
                "verifiable": True,
                "contradicts_primary": False,
            }
        )
        assert result.score == 80
        assert result.result == GateResult.SURVIVE

    def test_scholarly_verifiable_contradicts(self, gate):
        """Scholarly + verifiable + contradicts = 60 - 40 = 20 → Fail."""
        result = gate.evaluate(
            {
                "source_type": "scholarly",
                "verifiable": True,
                "contradicts_primary": True,
            }
        )
        assert result.score == 20
        assert result.result == GateResult.FAIL

    def test_human_theory_verifiable(self, gate):
        """Human theory + verifiable = 40 → Fail."""
        result = gate.evaluate(
            {
                "source_type": "human_theory",
                "verifiable": True,
                "contradicts_primary": False,
            }
        )
        assert result.score == 40
        assert result.result == GateResult.FAIL

    def test_unknown_unverifiable(self, gate):
        """Unknown + unverifiable = 20 * 0.5 = 10 → Fail."""
        result = gate.evaluate(
            {
                "source_type": "unknown",
                "verifiable": False,
                "contradicts_primary": False,
            }
        )
        assert result.score == 10
        assert result.result == GateResult.FAIL

    def test_prophetic_unverifiable_contradicts(self, gate):
        """Prophetic + unverifiable + contradicts = 80*0.5 - 40 = 0 → Fail."""
        result = gate.evaluate(
            {
                "source_type": "prophetic",
                "verifiable": False,
                "contradicts_primary": True,
            }
        )
        assert result.score == 0
        assert result.result == GateResult.FAIL

    def test_scholarly_verifiable_no_contradiction(self, gate):
        """Scholarly + verifiable = 60 → Survive."""
        result = gate.evaluate(
            {
                "source_type": "scholarly",
                "verifiable": True,
                "contradicts_primary": False,
            }
        )
        assert result.score == 60
        assert result.result == GateResult.SURVIVE

    def test_default_values(self, gate):
        """Empty dict defaults to unknown/unverifiable/no-contradiction = 10."""
        result = gate.evaluate({})
        assert result.score == 10
        assert result.result == GateResult.FAIL

    def test_score_clamped_to_zero(self, gate):
        """Score never goes below 0."""
        result = gate.evaluate(
            {
                "source_type": "unknown",
                "verifiable": False,
                "contradicts_primary": True,
            }
        )
        # 20 * 0.5 - 40 = -30 → clamped to 0
        assert result.score == 0
        assert result.result == GateResult.FAIL

    def test_name_and_description(self, gate):
        """Test name_and_description."""
        assert "Source Integrity" in gate.name
        assert len(gate.description) > 0

    def test_chain_questions_exist(self, gate):
        """Test chain_questions_exist."""
        questions = gate.get_chain_questions()
        assert len(questions) >= 3
