"""Al-Furqan Evaluation Gates."""

from al_furqan.engine.gates.base import Gate
from al_furqan.engine.gates.source_integrity import SourceIntegrityGate
from al_furqan.engine.gates.structural_consistency import StructuralConsistencyGate
from al_furqan.engine.gates.mediation_zeroing import MediationZeroingGate
from al_furqan.engine.gates.origin_aware import OriginAwareGate
from al_furqan.engine.gates.origin_preservation import OriginPreservationGate

ALL_GATES = [
    SourceIntegrityGate,
    StructuralConsistencyGate,
    MediationZeroingGate,
    OriginAwareGate,
    OriginPreservationGate,
]

__all__ = [
    "Gate",
    "SourceIntegrityGate",
    "StructuralConsistencyGate",
    "MediationZeroingGate",
    "OriginAwareGate",
    "OriginPreservationGate",
    "ALL_GATES",
]
