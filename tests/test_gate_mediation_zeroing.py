"""Tests for Gate 3: Mediation Zeroing (الوساطة)."""

import pytest
from al_furqan.engine.gates.mediation_zeroing import MediationZeroingGate
from al_furqan.engine.models import GateResult

# pylint: disable=redefined-outer-name


@pytest.fixture
def gate():
    """Execute gate."""
    return MediationZeroingGate()


class TestMediationZeroingGate:
    """Test mediation zeroing scoring with known inputs."""

    def test_non_human_removes_bias_no_relativism(self, gate):
        """Best case: 90 + 10 = 100 → Survive."""
        result = gate.evaluate({
            "foundation_type": "non_human_foundation",
            "removes_bias": True,
            "cultural_relativism": False,
        })
        assert result.score == 100
        assert result.result == GateResult.SURVIVE

    def test_non_human_with_relativism(self, gate):
        """90 - 30 = 60 → Survive."""
        result = gate.evaluate({
            "foundation_type": "non_human_foundation",
            "removes_bias": False,
            "cultural_relativism": True,
        })
        assert result.score == 60
        assert result.result == GateResult.SURVIVE

    def test_mixed_foundation_removes_bias(self, gate):
        """50 + 10 = 60 → Survive."""
        result = gate.evaluate({
            "foundation_type": "mixed_foundation",
            "removes_bias": True,
            "cultural_relativism": False,
        })
        assert result.score == 60
        assert result.result == GateResult.SURVIVE

    def test_mixed_with_relativism(self, gate):
        """50 - 30 = 20 → Fail."""
        result = gate.evaluate({
            "foundation_type": "mixed_foundation",
            "removes_bias": False,
            "cultural_relativism": True,
        })
        assert result.score == 20
        assert result.result == GateResult.FAIL

    def test_pure_human_preference(self, gate):
        """20 + 0 = 20 → Fail."""
        result = gate.evaluate({
            "foundation_type": "pure_human_preference",
            "removes_bias": False,
            "cultural_relativism": False,
        })
        assert result.score == 20
        assert result.result == GateResult.FAIL

    def test_pure_human_with_relativism(self, gate):
        """20 - 30 = -10 → clamped to 0 → Fail."""
        result = gate.evaluate({
            "foundation_type": "pure_human_preference",
            "removes_bias": False,
            "cultural_relativism": True,
        })
        assert result.score == 0
        assert result.result == GateResult.FAIL

    def test_default_values(self, gate):
        """Empty dict → pure_human_preference, no bias removal, no relativism = 20 → Fail."""
        result = gate.evaluate({})
        assert result.score == 20
        assert result.result == GateResult.FAIL

    def test_name_and_questions(self, gate):
        """Test name_and_questions."""
        assert "Mediation Zeroing" in gate.name
        assert len(gate.get_chain_questions()) >= 3
