"""Tests for Gate 4: Origin Aware (الأصل) — Binary Gate."""

import pytest
from al_furqan.engine.gates.origin_aware import OriginAwareGate
from al_furqan.engine.models import GateResult

# pylint: disable=redefined-outer-name


@pytest.fixture
def gate():
    """Execute gate."""
    return OriginAwareGate()


class TestOriginAwareGate:
    """Test binary survive/fail for origin awareness."""

    def test_acknowledges_transcendent(self, gate):
        """Acknowledges → score=100, Survive."""
        result = gate.evaluate({"acknowledges_transcendent": True})
        assert result.score == 100
        assert result.result == GateResult.SURVIVE

    def test_denies_transcendent(self, gate):
        """Denies → score=0, Fail."""
        result = gate.evaluate({"acknowledges_transcendent": False})
        assert result.score == 0
        assert result.result == GateResult.FAIL

    def test_missing_key_defaults_fail(self, gate):
        """Missing key defaults to False → Fail."""
        result = gate.evaluate({})
        assert result.score == 0
        assert result.result == GateResult.FAIL

    def test_empty_dict_fail(self, gate):
        """Empty dict → Fail."""
        result = gate.evaluate({})
        assert result.result == GateResult.FAIL

    def test_binary_no_middle_ground(self, gate):
        """Only two possible scores: 0 or 100."""
        survive = gate.evaluate({"acknowledges_transcendent": True})
        fail = gate.evaluate({"acknowledges_transcendent": False})
        assert survive.score == 100
        assert fail.score == 0
        # No score between 0 and 100 is possible
        assert survive.score != fail.score

    def test_name_and_questions(self, gate):
        """Test name_and_questions."""
        assert "Origin Aware" in gate.name
        assert len(gate.get_chain_questions()) >= 3
