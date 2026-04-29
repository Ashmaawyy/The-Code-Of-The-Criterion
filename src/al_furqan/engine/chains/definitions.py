"""
Chain Definitions — Guided Reasoning Questions per Gate

Each gate has 3-5 questions that build on previous answers.
Questions extract FACTS, not opinions.
"""

# Gate 1: Source Integrity chain questions
SOURCE_INTEGRITY_CHAIN = [
    "What is the primary source of this claim or system? Identify whether it originates from divine revelation, prophetic tradition, scholarly consensus, human theory, or is unknown.",  # pylint: disable=line-too-long
    "Is the source verifiable? Can it be traced through established chains of transmission (isnad), empirical evidence, or rigorous logical proof?",  # pylint: disable=line-too-long
    "Classify the source type as exactly one of: divine, prophetic, scholarly, human_theory, unknown.",  # pylint: disable=line-too-long
    "Does this claim or system contradict any established primary sources (Quran, authenticated Sunnah)? Answer true or false.",  # pylint: disable=line-too-long
    "Is there any reduction, omission, or reinterpretation of established truths for human convenience?",  # pylint: disable=line-too-long
]

# Gate 2: Structural Consistency chain questions
STRUCTURAL_CONSISTENCY_CHAIN = [
    "Does this system or claim contain internal contradictions? Classify as: no_contradictions, minor_inconsistencies, or major_contradictions.",  # pylint: disable=line-too-long
    "Is the causal chain intact — does every stated effect trace back to a clearly identified cause without appealing to luck, chance, or emergent randomness?",  # pylint: disable=line-too-long
    "Are there logical gaps where conclusions are drawn without sufficient premises or supporting evidence?",  # pylint: disable=line-too-long
    "Can the system explain its own stability and order without resorting to emergent randomness or ungrounded assumptions?",  # pylint: disable=line-too-long
]

# Gate 3: Mediation Zeroing chain questions
MEDIATION_ZEROING_CHAIN = [
    "Is this system founded on human preference, evolutionary ethics, or secular humanism — or on principles external to human cognition? Classify as: non_human_foundation, mixed_foundation, or pure_human_preference.",  # pylint: disable=line-too-long
    "Does the system rely on external, non-contingent principles (divine command, natural law from a transcendent source) as its ultimate foundation?",  # pylint: disable=line-too-long
    "Does the framework actively remove or account for human cognitive bias in its methodology and conclusions?",  # pylint: disable=line-too-long
    "Does the system embrace cultural relativism — treating truth as variable across cultures, time periods, or individual preferences?",  # pylint: disable=line-too-long
]

# Gate 4: Origin Aware chain questions
ORIGIN_AWARE_CHAIN = [
    "Does this system or claim explicitly acknowledge a transcendent, non-contingent origin for truth and moral obligation?",  # pylint: disable=line-too-long
    "Does the framework treat truth as emergent from human processes (evolution, consensus, social contract), or as derived from a self-authenticating transcendent source?",  # pylint: disable=line-too-long
    "Does the system deny, ignore, or remain silent on the necessity of a transcendent source for objective truth?",  # pylint: disable=line-too-long
]

# Mapping gate names to their chain definitions
GATE_CHAINS = {
    "Source Integrity (المصدر)": SOURCE_INTEGRITY_CHAIN,
    "Structural Consistency (البنية)": STRUCTURAL_CONSISTENCY_CHAIN,
    "Mediation Zeroing (الوساطة)": MEDIATION_ZEROING_CHAIN,
    "Origin Aware (الأصل)": ORIGIN_AWARE_CHAIN,
}
