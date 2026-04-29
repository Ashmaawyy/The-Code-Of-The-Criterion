"""Tests for DeterministicScorer — determinism is CRITICAL."""

import pytest
from al_furqan.engine.chains.scorer import DeterministicScorer
from al_furqan.engine.gates.source_integrity import SourceIntegrityGate
from al_furqan.engine.gates.structural_consistency import StructuralConsistencyGate
from al_furqan.engine.gates.mediation_zeroing import MediationZeroingGate
from al_furqan.engine.gates.origin_aware import OriginAwareGate
from al_furqan.engine.models import GateResult

# pylint: disable=redefined-outer-name


@pytest.fixture
def scorer():
    """Execute scorer."""
    return DeterministicScorer()


class TestDeterministicScorer:
    """Test that scoring is deterministic and correct."""

    def test_score_single_gate(self, scorer):
        """Score a single gate correctly."""
        gate = SourceIntegrityGate()
        result = scorer.score_gate(gate, {
            "source_type": "divine",
            "verifiable": True,
            "contradicts_primary": False,
        })
        assert result.score == 100
        assert result.result == GateResult.SURVIVE

    def test_score_all_gates(self, scorer):
        """Score all 4 gates at once."""
        gates = [
            SourceIntegrityGate(),
            StructuralConsistencyGate(),
            MediationZeroingGate(),
            OriginAwareGate(),
        ]
        extractions = {
            "Source Integrity (المصدر)": {
                "source_type": "divine",
                "verifiable": True,
                "contradicts_primary": False,
            },
            "Structural Consistency (البنية)": {
                "contradiction_level": "no_contradictions",
                "causal_chain_intact": True,
                "logical_gaps": False,
            },
            "Mediation Zeroing (الوساطة)": {
                "foundation_type": "non_human_foundation",
                "removes_bias": True,
                "cultural_relativism": False,
            },
            "Origin Aware (الأصل)": {
                "acknowledges_transcendent": True,
            },
        }
        results = scorer.score_all_gates(gates, extractions)
        assert len(results) == 4
        assert all(r.result == GateResult.SURVIVE for r in results)

    def test_score_all_gates_mixed_results(self, scorer):
        """Some gates pass, some fail."""
        gates = [SourceIntegrityGate(), OriginAwareGate()]
        extractions = {
            "Source Integrity (المصدر)": {
                "source_type": "unknown",
                "verifiable": False,
                "contradicts_primary": True,
            },
            "Origin Aware (الأصل)": {
                "acknowledges_transcendent": True,
            },
        }
        results = scorer.score_all_gates(gates, extractions)
        assert results[0].result == GateResult.FAIL  # source: 0
        assert results[1].result == GateResult.SURVIVE  # origin: 100

    def test_compute_total_score(self, scorer):
        """Total score is average of gate scores."""
        gates = [SourceIntegrityGate(), OriginAwareGate()]
        extractions = {
            "Source Integrity (المصدر)": {
                "source_type": "divine",
                "verifiable": True,
                "contradicts_primary": False,
            },
            "Origin Aware (الأصل)": {
                "acknowledges_transcendent": True,
            },
        }
        results = scorer.score_all_gates(gates, extractions)
        total = scorer.compute_total_score(results)
        # (90 + 100) // 2 = 95
        assert total == 100

    def test_compute_total_score_empty(self, scorer):
        """Empty list → 0."""
        assert scorer.compute_total_score([]) == 0

    def test_missing_gate_extractions_default(self, scorer):
        """Missing extractions for a gate → use defaults."""
        gate = SourceIntegrityGate()
        result = scorer.score_gate(gate, {})
        assert result.score == 10  # unknown, unverifiable, no contradiction

    def test_determinism_source_integrity(self, scorer):
        """CRITICAL: Same input → same output, 10 times."""
        gate = SourceIntegrityGate()
        extractions = {
            "source_type": "scholarly",
            "verifiable": True,
            "contradicts_primary": False,
        }
        results = [scorer.score_gate(gate, extractions) for _ in range(10)]
        assert all(r.score == results[0].score for r in results)
        assert all(r.result == results[0].result for r in results)

    def test_determinism_all_gates_10x(self, scorer):
        """
        CRITICAL DETERMINISM PROOF:
        Run scoring 10 times with identical inputs.
        Assert ALL 10 results are exactly equal.
        """
        gates = [
            SourceIntegrityGate(),
            StructuralConsistencyGate(),
            MediationZeroingGate(),
            OriginAwareGate(),
        ]
        extractions = {
            "Source Integrity (المصدر)": {
                "source_type": "prophetic",
                "verifiable": True,
                "contradicts_primary": False,
            },
            "Structural Consistency (البنية)": {
                "contradiction_level": "minor_inconsistencies",
                "causal_chain_intact": True,
                "logical_gaps": False,
            },
            "Mediation Zeroing (الوساطة)": {
                "foundation_type": "mixed_foundation",
                "removes_bias": True,
                "cultural_relativism": False,
            },
            "Origin Aware (الأصل)": {
                "acknowledges_transcendent": True,
            },
        }

        all_runs = []
        for _ in range(10):
            results = scorer.score_all_gates(gates, extractions)
            all_runs.append([(r.score, r.result.value, r.name) for r in results])

        # Every run must be identical to the first
        for i in range(1, 10):
            assert all_runs[i] == all_runs[0], (
                f"Run {i} differs from run 0: {all_runs[i]} != {all_runs[0]}"
            )

    def test_determinism_total_score_10x(self, scorer):
        """Total score is also deterministic across 10 runs."""
        gates = [SourceIntegrityGate(), StructuralConsistencyGate()]
        extractions = {
            "Source Integrity (المصدر)": {
                "source_type": "divine",
                "verifiable": True,
                "contradicts_primary": False,
            },
            "Structural Consistency (البنية)": {
                "contradiction_level": "no_contradictions",
                "causal_chain_intact": True,
                "logical_gaps": False,
            },
        }
        totals = []
        for _ in range(10):
            results = scorer.score_all_gates(gates, extractions)
            totals.append(scorer.compute_total_score(results))

        assert all(t == totals[0] for t in totals)
