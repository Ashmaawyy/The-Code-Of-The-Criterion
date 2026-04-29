"""Tests for Gate 2: Structural Consistency (البنية)."""

import pytest
from al_furqan.engine.gates.structural_consistency import StructuralConsistencyGate
from al_furqan.engine.models import GateResult

# pylint: disable=redefined-outer-name


@pytest.fixture
def gate():
    """Execute gate."""
    return StructuralConsistencyGate()


class TestStructuralConsistencyGate:
    """Test structural consistency scoring with known inputs."""

    def test_no_contradictions_causal_intact_no_gaps(self, gate):
        """Best case: 90 + 10 = 100 → Survive."""
        result = gate.evaluate({
            "contradiction_level": "no_contradictions",
            "causal_chain_intact": True,
            "logical_gaps": False,
        })
        assert result.score == 100
        assert result.result == GateResult.SURVIVE

    def test_no_contradictions_no_causal_with_gaps(self, gate):
        """90 + 0 - 20 = 70 → Survive."""
        result = gate.evaluate({
            "contradiction_level": "no_contradictions",
            "causal_chain_intact": False,
            "logical_gaps": True,
        })
        assert result.score == 70
        assert result.result == GateResult.SURVIVE

    def test_minor_inconsistencies_causal_intact(self, gate):
        """60 + 10 = 70 → Survive."""
        result = gate.evaluate({
            "contradiction_level": "minor_inconsistencies",
            "causal_chain_intact": True,
            "logical_gaps": False,
        })
        assert result.score == 70
        assert result.result == GateResult.SURVIVE

    def test_minor_inconsistencies_gaps(self, gate):
        """60 - 20 = 40 → Fail."""
        result = gate.evaluate({
            "contradiction_level": "minor_inconsistencies",
            "causal_chain_intact": False,
            "logical_gaps": True,
        })
        assert result.score == 40
        assert result.result == GateResult.FAIL

    def test_major_contradictions_all_bad(self, gate):
        """30 + 0 - 20 = 10 → Fail."""
        result = gate.evaluate({
            "contradiction_level": "major_contradictions",
            "causal_chain_intact": False,
            "logical_gaps": True,
        })
        assert result.score == 10
        assert result.result == GateResult.FAIL

    def test_major_contradictions_causal_intact(self, gate):
        """30 + 10 = 40 → Fail."""
        result = gate.evaluate({
            "contradiction_level": "major_contradictions",
            "causal_chain_intact": True,
            "logical_gaps": False,
        })
        assert result.score == 40
        assert result.result == GateResult.FAIL

    def test_default_values(self, gate):
        """Empty dict → major_contradictions, no causal, no gaps = 30 → Fail."""
        result = gate.evaluate({})
        assert result.score == 30
        assert result.result == GateResult.FAIL

    def test_name_and_questions(self, gate):
        """Test name_and_questions."""
        assert "Structural Consistency" in gate.name
        assert len(gate.get_chain_questions()) >= 3
