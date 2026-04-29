"""Tests for the Output Validator (Sprint 6C)."""

  # pylint: disable=wrong-import-order

from al_furqan.engine.security.output_validator import OutputValidator, ValidationResult
from al_furqan.engine.models import Verdict, GateScore, GateResult, SystemType


def _make_valid_verdict(**overrides) -> Verdict:
    """Create a valid verdict for testing."""
    defaults = dict(  # pylint: disable=use-dict-literal
        question="Test question",
        primary_system=SystemType.SOCIAL,
        friction_points=["point1"],
        gate_scores=[
            GateScore(name="Source Integrity", score=85, result=GateResult.SURVIVE, reasoning="ok"),
            GateScore(name="Structural Consistency", score=80, result=GateResult.SURVIVE, reasoning="ok"),  # pylint: disable=line-too-long
            GateScore(name="Mediation Zeroing", score=75, result=GateResult.SURVIVE, reasoning="ok"),  # pylint: disable=line-too-long
            GateScore(name="Origin Aware", score=90, result=GateResult.SURVIVE, reasoning="ok"),
        ],
        origin_gate=GateResult.SURVIVE,
        consequences_short_term=["c1"],
        consequences_long_term=["c2"],
        revised_reasoning="reasoning",
        final_judgment="This is the judgment.",
        total_score=82,
        passes=1,
    )
    defaults.update(overrides)
    return Verdict(**defaults)


class TestOutputValidator:
    """Test suite for OutputValidator."""

    def setup_method(self):
        """Execute setup_method."""
        self.validator = OutputValidator()  # pylint: disable=attribute-defined-outside-init

    def test_valid_verdict_passes(self):
        """Test valid_verdict_passes."""
        verdict = _make_valid_verdict()
        result = self.validator.validate_verdict(verdict)
        assert result.valid is True
        assert not result.issues

    def test_missing_gates_detected(self):
        """Test missing_gates_detected."""
        verdict = _make_valid_verdict(gate_scores=[
            GateScore(name="Source Integrity", score=85, result=GateResult.SURVIVE, reasoning="ok"),
        ])
        result = self.validator.validate_verdict(verdict)
        assert not result.valid
        assert any("Expected 4 gates" in i for i in result.issues)

    def test_wrong_gate_names_detected(self):
        """Test wrong_gate_names_detected."""
        verdict = _make_valid_verdict(gate_scores=[
            GateScore(name="Source Integrity", score=85, result=GateResult.SURVIVE, reasoning="ok"),
            GateScore(name="Structural Consistency", score=80, result=GateResult.SURVIVE, reasoning="ok"),  # pylint: disable=line-too-long
            GateScore(name="Mediation Zeroing", score=75, result=GateResult.SURVIVE, reasoning="ok"),  # pylint: disable=line-too-long
            GateScore(name="WRONG NAME", score=90, result=GateResult.SURVIVE, reasoning="ok"),
        ])
        result = self.validator.validate_verdict(verdict)
        assert not result.valid
        assert any("Missing gates" in i or "Unexpected gates" in i for i in result.issues)

    def test_score_out_of_range_negative(self):
        """Test score_out_of_range_negative."""
        verdict = _make_valid_verdict(gate_scores=[
            GateScore(name="Source Integrity", score=-5, result=GateResult.FAIL, reasoning="ok"),
            GateScore(name="Structural Consistency", score=80, result=GateResult.SURVIVE, reasoning="ok"),  # pylint: disable=line-too-long
            GateScore(name="Mediation Zeroing", score=75, result=GateResult.SURVIVE, reasoning="ok"),  # pylint: disable=line-too-long
            GateScore(name="Origin Aware", score=90, result=GateResult.SURVIVE, reasoning="ok"),
        ])
        result = self.validator.validate_verdict(verdict)
        assert not result.valid
        assert any("out of range" in i for i in result.issues)

    def test_score_out_of_range_above_100(self):
        """Test score_out_of_range_above_100."""
        verdict = _make_valid_verdict(gate_scores=[
            GateScore(name="Source Integrity", score=85, result=GateResult.SURVIVE, reasoning="ok"),
            GateScore(name="Structural Consistency", score=150, result=GateResult.SURVIVE, reasoning="ok"),  # pylint: disable=line-too-long
            GateScore(name="Mediation Zeroing", score=75, result=GateResult.SURVIVE, reasoning="ok"),  # pylint: disable=line-too-long
            GateScore(name="Origin Aware", score=90, result=GateResult.SURVIVE, reasoning="ok"),
        ])
        result = self.validator.validate_verdict(verdict)
        assert not result.valid

    def test_empty_final_judgment_detected(self):
        """Test empty_final_judgment_detected."""
        verdict = _make_valid_verdict(final_judgment="")
        result = self.validator.validate_verdict(verdict)
        assert not result.valid
        assert any("final_judgment" in i for i in result.issues)

    def test_missing_gate_scores_attribute(self):
        """Object without gate_scores should fail."""
        class FakeVerdict:  # pylint: disable=too-few-public-methods
            """FakeVerdict class."""
            pass  # pylint: disable=unnecessary-pass
        result = self.validator.validate_verdict(FakeVerdict())
        assert not result.valid

    def test_extra_gates_detected(self):
        """Test extra_gates_detected."""
        verdict = _make_valid_verdict(gate_scores=[
            GateScore(name="Source Integrity", score=85, result=GateResult.SURVIVE, reasoning="ok"),
            GateScore(name="Structural Consistency", score=80, result=GateResult.SURVIVE, reasoning="ok"),  # pylint: disable=line-too-long
            GateScore(name="Mediation Zeroing", score=75, result=GateResult.SURVIVE, reasoning="ok"),  # pylint: disable=line-too-long
            GateScore(name="Origin Aware", score=90, result=GateResult.SURVIVE, reasoning="ok"),
            GateScore(name="Extra Gate", score=50, result=GateResult.FAIL, reasoning="ok"),
        ])
        result = self.validator.validate_verdict(verdict)
        assert not result.valid

    # --- Extraction validation ---

    def test_valid_extraction_passes(self):
        """Test valid_extraction_passes."""
        extraction = {
            "source_type": "primary",
            "is_verifiable": True,
            "contradicts_primary": False,
            "consistency_level": "strong",
            "foundation_type": "transcendent",
            "acknowledges_transcendence": True,
        }
        result = self.validator.validate_extraction(extraction)
        assert result.valid

    def test_extraction_missing_field(self):
        """Test extraction_missing_field."""
        extraction = {
            "source_type": "primary",
            "is_verifiable": True,
            # Missing other fields
        }
        result = self.validator.validate_extraction(extraction)
        assert not result.valid
        assert any("Missing required field" in i for i in result.issues)

    def test_extraction_invalid_source_type(self):
        """Test extraction_invalid_source_type."""
        extraction = {
            "source_type": "invalid_type",
            "is_verifiable": True,
            "contradicts_primary": False,
            "consistency_level": "strong",
            "foundation_type": "transcendent",
            "acknowledges_transcendence": True,
        }
        result = self.validator.validate_extraction(extraction)
        assert not result.valid

    def test_extraction_not_dict(self):
        """Test extraction_not_dict."""
        result = self.validator.validate_extraction("not a dict")
        assert not result.valid

    def test_extraction_bool_field_wrong_type(self):
        """Test extraction_bool_field_wrong_type."""
        extraction = {
            "source_type": "primary",
            "is_verifiable": "yes",  # Should be bool
            "contradicts_primary": False,
            "consistency_level": "strong",
            "foundation_type": "transcendent",
            "acknowledges_transcendence": True,
        }
        result = self.validator.validate_extraction(extraction)
        assert not result.valid

    def test_validation_result_dataclass(self):
        """Test validation_result_dataclass."""
        r = ValidationResult(valid=True, issues=[])
        assert r.valid
        assert not r.issues
