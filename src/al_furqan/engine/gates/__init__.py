"""Al-Furqan Evaluation Gates."""

from al_furqan.engine.gates.base import Gate
from al_furqan.engine.gates.mediation_zeroing import MediationZeroingGate
from al_furqan.engine.gates.origin_aware import OriginAwareGate
from al_furqan.engine.gates.origin_preservation import OriginPreservationGate
from al_furqan.engine.gates.source_integrity import SourceIntegrityGate
from al_furqan.engine.gates.structural_consistency import StructuralConsistencyGate

ALL_GATES = [
    SourceIntegrityGate,
    StructuralConsistencyGate,
    MediationZeroingGate,
    OriginAwareGate,
    OriginPreservationGate,
]

__all__ = [
    "ALL_GATES",
    "Gate",
    "MediationZeroingGate",
    "OriginAwareGate",
    "OriginPreservationGate",
    "SourceIntegrityGate",
    "StructuralConsistencyGate",
]
