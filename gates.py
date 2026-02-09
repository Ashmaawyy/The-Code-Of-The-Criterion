def source_integrity_gate(system):
    """
    Evaluates whether the framework preserves truth
    without reducing it to metaphor or human convenience.
    """
    return 100 if system.get("accepts_raw_truth") else 0


def structural_consistency_gate(system):
    """
    Evaluates whether causality is grounded or attributed to chance.
    """
    return 100 if system.get("grounds_causality") else 0


def mediation_zeroing_gate(system):
    """
    Evaluates resistance to human projection and subjective ethics.
    """
    return 100 if system.get("minimizes_human_projection") else 0


def origin_aware_gate(system):
    """
    Evaluates whether truth is recognized as non-derivative.
    """
    return 100 if system.get("acknowledges_transcendent_source") else 0
