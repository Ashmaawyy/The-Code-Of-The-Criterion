def source_integrity_gate(system):
    """
    Evaluates whether raw truth is preserved without reduction,
    reinterpretation, or convenience distortion.
    """
    score = 0

    if system.get("accepts_raw_truth"):
        score += 50
    if system.get("requires_evidence_or_revelation"):
        score += 50

    return score


def structural_consistency_gate(system):
    """
    Evaluates whether causality and moral order are grounded
    in a non-contingent source rather than chance or emergence.
    """
    score = 0

    if system.get("grounds_causality"):
        score += 50
    if system.get("rejects_random_moral_emergence"):
        score += 50

    return score


def mediation_zeroing_gate(system):
    """
    Evaluates whether human preference is treated as derivative,
    not sovereign over truth.
    """
    score = 0

    if system.get("minimizes_human_projection"):
        score += 50
    if system.get("rejects_secular_humanism"):
        score += 50

    return score


def origin_aware_gate(system):
    """
    Evaluates recognition of a self-authenticating,
    non-contingent transcendent source.
    """
    return 100 if system.get("acknowledges_transcendent_source") else 0
