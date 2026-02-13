from evaluation.gates import (
    source_integrity_gate,
    structural_consistency_gate,
    mediation_zeroing_gate,
    origin_aware_gate
)
from axioms import core_axioms


def scan(query):
    query = query.lower()

    if any(word in query for word in ["economy", "interest", "finance", "money"]):
        return "economic"
    if any(word in query for word in ["family", "marriage", "gender", "lineage"]):
        return "social"
    if any(word in query for word in ["purpose", "meaning", "god", "morality"]):
        return "spiritual"

    return "general"


def mirror(system_type, core_axioms, system):
    frictions = []
    score = 0

    # Economic preservation logic
    if system_type == "economic" and system.get("permits_exploitative_gain"):
        frictions.append("Violates equitable circulation")
        score -= 10

    # Social preservation logic
    if system_type == "social" and system.get("destabilizes_lineage"):
        frictions.append("Compromises lineage preservation")
        score -= 10

    # Transcendence necessity
    if not system.get("acknowledges_transcendent_source"):
        frictions.append("Fails Transcendence Necessity")
        score -= 10

    return frictions, score


def verdict(frictions):
    consequences = []

    for friction in frictions:
        consequences.append(
            f"Design violation detected → Long-term systemic instability: {friction}"
        )

    return consequences


def evaluate(query, system, axioms):
    system_type = scan(query)

    frictions, friction_score = mirror(system_type, axioms, system)

    consequences = verdict(frictions)

    gates = {
        "Source Integrity": source_integrity_gate(system),
        "Structural Consistency": structural_consistency_gate(system),
        "Mediation Zeroing": mediation_zeroing_gate(system),
        "Origin Aware": origin_aware_gate(system),
    }

    # Gate survival logic
    origin_status = "Survive" if gates["Origin Aware"] == 100 else "Fail"

    total_score = friction_score + sum(gates.values())

    survival = all(score > 0 for score in gates.values())

    return {
        "Query": query,
        "Primary System": system_type,
        "Friction Points": frictions,
        "Consequences": consequences,
        "Tri-Axial Gate Scores": gates,
        "Origin-Aware Gate": origin_status,
        "Total Score": total_score,
        "Final Judgment": "Survives The Criterion" if survival else "Fails The Criterion"
    }
