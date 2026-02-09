from evaluation.gates import (
    source_integrity_gate,
    structural_consistency_gate,
    mediation_zeroing_gate,
    origin_aware_gate
)

def scan(query):
    if any(word in query.lower() for word in ["economy", "interest", "money"]):
        return "economic"
    if any(word in query.lower() for word in ["family", "sex", "marriage"]):
        return "social"
    if any(word in query.lower() for word in ["meaning", "purpose", "god"]):
        return "spiritual"
    return "general"


def mirror(system_type, axioms):
    frictions = []

    if system_type == "economic":
        frictions.append("Potential violation of equitable circulation")

    if system_type == "social":
        frictions.append("Potential damage to lineage and stability")

    return frictions


def verdict(frictions):
    consequences = []
    for f in frictions:
        consequences.append(f"Unchecked continuation leads to systemic decay: {f}")
    return consequences


def evaluate(query, system, axioms):
    system_type = scan(query)
    frictions = mirror(system_type, axioms)
    consequences = verdict(frictions)

    gates = {
        "Source Integrity": source_integrity_gate(system),
        "Structural Consistency": structural_consistency_gate(system),
        "Mediation Zeroing": mediation_zeroing_gate(system),
        "Origin Aware": origin_aware_gate(system),
    }

    return {
        "Query": query,
        "System": system_type,
        "Frictions": frictions,
        "Consequences": consequences,
        "Gate Scores": gates
    }
