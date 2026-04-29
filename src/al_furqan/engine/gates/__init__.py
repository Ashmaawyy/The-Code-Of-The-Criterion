"""Al-Furqan Evaluation Gates."""

from al_furqan.engine.gates.base import Gate
from al_furqan.engine.gates.source_integrity import SourceIntegrityGate
from al_furqan.engine.gates.structural_consistency import StructuralConsistencyGate
from al_furqan.engine.gates.mediation_zeroing import MediationZeroingGate
from al_furqan.engine.gates.origin_aware import OriginAwareGate

ALL_GATES = [
    SourceIntegrityGate,
    StructuralConsistencyGate,
    MediationZeroingGate,
    OriginAwareGate,
]

__all__ = [
    "Gate",
    "SourceIntegrityGate",
    "StructuralConsistencyGate",
    "MediationZeroingGate",
    "OriginAwareGate",
    "ALL_GATES",
]
