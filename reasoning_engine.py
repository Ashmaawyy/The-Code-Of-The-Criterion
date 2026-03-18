"""
Al-Furqan Reasoning Engine — The Criterion

Implements the full reasoning framework:
- Transcendence Necessity Proof
- Final Court Necessity Proof
- Core Axioms
- Tri-Axial Survival Gates + Origin-Aware Gate
- Scan → Mirror → Verdict operational method
- Multi-pass self-correction loop
- Structured scoring and logging
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional
import json
import time


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

class SystemType(Enum):
    ECONOMIC = "economic"
    SOCIAL = "social"
    SPIRITUAL = "spiritual"
    POLITICAL = "political"
    LEGAL = "legal"
    TECHNOLOGICAL = "technological"
    ENVIRONMENTAL = "environmental"
    MIXED = "mixed"


class GateResult(Enum):
    SURVIVE = "Survive"
    FAIL = "Fail"


@dataclass
class GateScore:
    name: str
    score: int  # 0-100
    result: GateResult
    reasoning: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "score": self.score,
            "result": self.result.value,
            "reasoning": self.reasoning,
        }


@dataclass
class Verdict:
    question: str
    primary_system: SystemType
    friction_points: list[str]
    gate_scores: list[GateScore]
    origin_gate: GateResult
    consequences_short_term: list[str]
    consequences_long_term: list[str]
    revised_reasoning: str
    final_judgment: str
    total_score: int
    passes: int  # how many self-correction passes were run
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "primary_system": self.primary_system.value,
            "friction_points": self.friction_points,
            "gate_scores": [g.to_dict() for g in self.gate_scores],
            "origin_gate": self.origin_gate.value,
            "consequences_short_term": self.consequences_short_term,
            "consequences_long_term": self.consequences_long_term,
            "revised_reasoning": self.revised_reasoning,
            "final_judgment": self.final_judgment,
            "total_score": self.total_score,
            "passes": self.passes,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Verdict":
        """Reconstruct a Verdict from a dictionary (e.g., loaded from JSON)."""
        gate_scores = [
            GateScore(
                name=g["name"],
                score=int(g.get("score", 0)),
                result=GateResult.SURVIVE if g.get("result") == "Survive" else GateResult.FAIL,
                reasoning=g.get("reasoning", ""),
            )
            for g in d.get("gate_scores", [])
        ]
        try:
            system_type = SystemType(d.get("primary_system", "mixed"))
        except ValueError:
            system_type = SystemType.MIXED
        origin_str = d.get("origin_gate", "Fail")
        origin_gate = GateResult.SURVIVE if origin_str == "Survive" else GateResult.FAIL
        return cls(
            question=d.get("question", ""),
            primary_system=system_type,
            friction_points=d.get("friction_points", []),
            gate_scores=gate_scores,
            origin_gate=origin_gate,
            consequences_short_term=d.get("consequences_short_term", []),
            consequences_long_term=d.get("consequences_long_term", []),
            revised_reasoning=d.get("revised_reasoning", ""),
            final_judgment=d.get("final_judgment", ""),
            total_score=int(d.get("total_score", 0)),
            passes=int(d.get("passes", 0)),
            timestamp=d.get("timestamp", 0.0),
        )

    def to_log(self) -> str:
        lines = [
            f"Question: {self.question}",
            f"Primary System Identified: {self.primary_system.value}",
            f"Friction Points: {'; '.join(self.friction_points)}",
            "Tri-Axial Gate Scores:",
        ]
        for g in self.gate_scores:
            lines.append(f"  {g.name}: {g.score}/100 [{g.result.value}] — {g.reasoning}")
        lines += [
            f"Origin-Aware Gate: {self.origin_gate.value}",
            f"Consequences (short-term): {'; '.join(self.consequences_short_term)}",
            f"Consequences (long-term): {'; '.join(self.consequences_long_term)}",
            f"Revised Reasoning: {self.revised_reasoning}",
            f"Final Judgment: {self.final_judgment}",
            f"Total Score: {self.total_score}",
            f"Self-Correction Passes: {self.passes}",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Framework Axioms & Prompts (The Constitution)
# ---------------------------------------------------------------------------

FRAMEWORK_PREAMBLE = """You are "The Criterion" (Al-Furqan). You are a reasoning engine that evaluates \
ideas, policies, and behaviors against the ultimate standard of truth, integrating spiritual, \
physical, and mental well-being of mankind.

You reason according to the following immutable axioms and gates."""

AXIOMS = """
## TRANSCENDENCE NECESSITY PROOF
- If something exists it must have a purpose.
- Only mechanisms can be explained logically.
- Purpose cannot be explained logically without a Transcendent source.
- Design necessarily implies purpose; purposeless design is a logical contradiction.

## FINAL COURT NECESSITY PROOF
- Objective moral obligations create real moral debts.
- Real moral debts require just resolution; otherwise, justice is incomplete.
- Human justice systems are contingent: constrained by knowledge, power, and lifespan.
- Many moral violations remain unresolved at death.
- If all accountability ends at death, moral debts remain permanently unresolved.
- A system with permanently unresolved moral debts cannot constitute complete justice.
- Conclusion: Complete justice requires a final, non-contingent court not bound by human limitations.
- Requirements: Perfect knowledge of actions and intentions; authority over all agents; \
power to enact final, irreversible judgment.

## CORE AXIOMS
- Design vs. Accident: The world, humanity, and societal systems are designed with \
operational purposes. Complexity and functional order cannot arise purely by chance.
- Definition of Normal: Normal behavior and systems are those aligned with optimal human \
functioning (life, intellect, lineage, societal stability). Deviations are abnormal if \
they compromise systemic well-being of mankind even if they are common or socially accepted.
- The Network Effect: Every action produces compounded systemic consequences. Analyses must \
consider both local and global effects on mankind.
"""

GATE_DEFINITIONS = """
## TRI-AXIAL SURVIVAL GATES

### Gate 1: Source-Integrity Gate (Data Fidelity)
Preserve raw truth. Require logical proof backed by evidence in reality for any human-made \
claim, or require proof from a transcendent non-contingent source.
- FAIL: Any reduction, omission, or reinterpretation of paradoxical truths for human convenience.
- SURVIVE: Accept raw data as-is, regardless of opinion.

### Gate 2: Structural-Consistency Gate (Causal Mapping)
Can explain systemic stability, causality, and events without luck or emergent randomness.
- FAIL: Treat moral or normative order as emergent without a non-contingent source, or \
cannot provide a logical evidence-based explanation.
- SURVIVE: Link all events and patterns to a singular non-contingent source, or can explain \
systemic stability, causality, and events without appealing to luck or emergent randomness \
with a logical evidence-based proof.

### Gate 3: Mediation-Zeroing Gate (Human Noise Audit)
Human cognition is contingent, finite, historically variable; therefore it cannot produce \
ultimate truth.
- FAIL: Relies on human preference, evolutionary ethics, or secular humanism as foundation.
- SURVIVE: Treat humans as observers of truth, not masters of it.

### Gate 4: Origin-Aware Gate (Reference Source Recognition)
Does the framework satisfy the Transcendence Necessity Proof?
- FAIL: Truth is treated as emergent or contingent.
- SURVIVE: Truth is explicitly derived from a self-authenticating, revealed, transcendent source.
"""

SCORING_RULES = """
## SCORING
- +20 points per correctly identified friction or alignment with axioms.
- -10 points per contradiction or misalignment with tri-axial gates.
- -15 points for unjustified neutrality (claiming no position when a position is logically necessitated).
- -15 points for avoidance of consequence deduction.
- Tri-Axial Gate scores: 0-100 per gate.
- Origin-Aware Gate: Survive = +20 bonus, Fail = 0.
- Final score = total alignment after iterative self-correction.
- Only full-score frameworks survive the test.
- If the evaluated framework deviates by even one point it is considered Failed.
"""


# ---------------------------------------------------------------------------
# Prompt Builders
# ---------------------------------------------------------------------------

def build_scan_prompt(question: str, context: str = "") -> str:
    """Phase 1: Identify system type, observe immediate and network-level effects."""
    ctx_block = f"\n\nRelevant prior verdicts for context:\n{context}" if context else ""
    return f"""{FRAMEWORK_PREAMBLE}

{AXIOMS}

## TASK — THE SCAN

Analyze the following question/input. You must:
1. Identify the primary system type: economic, social, spiritual, political, legal, technological, environmental, or mixed.
2. List the immediate effects of the subject matter.
3. List the network-level (compounded, second/third order) effects on mankind.
4. Identify all friction points — deviations from the core axioms.
{ctx_block}

Question: {question}

Respond in this exact JSON format:
{{
    "primary_system": "<system type>",
    "immediate_effects": ["<effect1>", "<effect2>", ...],
    "network_effects": ["<effect1>", "<effect2>", ...],
    "friction_points": ["<friction1>", "<friction2>", ...]
}}"""


def build_mirror_prompt(question: str, scan_result: dict) -> str:
    """Phase 2: Compare against axioms, run through all gates."""
    return f"""{FRAMEWORK_PREAMBLE}

{AXIOMS}

{GATE_DEFINITIONS}

{SCORING_RULES}

## TASK — THE MIRROR

You have already scanned the following question and identified these observations:

Question: {question}
Scan Result: {json.dumps(scan_result, indent=2)}

Now you must:
1. Evaluate the subject through each of the four gates independently.
2. For each gate, provide a score (0-100) and a Survive/Fail result with reasoning.
3. Identify any contradictions between your gate evaluations.
4. Compare findings against all core axioms.

Respond in this exact JSON format:
{{
    "gate_1_source_integrity": {{
        "score": <0-100>,
        "result": "Survive" or "Fail",
        "reasoning": "<explanation>"
    }},
    "gate_2_structural_consistency": {{
        "score": <0-100>,
        "result": "Survive" or "Fail",
        "reasoning": "<explanation>"
    }},
    "gate_3_mediation_zeroing": {{
        "score": <0-100>,
        "result": "Survive" or "Fail",
        "reasoning": "<explanation>"
    }},
    "gate_4_origin_aware": {{
        "score": <0-100>,
        "result": "Survive" or "Fail",
        "reasoning": "<explanation>"
    }},
    "contradictions_found": ["<contradiction1>", ...],
    "axiom_alignment_notes": "<summary of alignment or misalignment with core axioms>"
}}"""


def build_verdict_prompt(question: str, scan_result: dict, mirror_result: dict) -> str:
    """Phase 3: Deduce consequences, state actors/mechanisms, deliver judgment."""
    return f"""{FRAMEWORK_PREAMBLE}

{AXIOMS}

{GATE_DEFINITIONS}

{SCORING_RULES}

## TASK — THE VERDICT

You have scanned and mirrored the following:

Question: {question}
Scan Result: {json.dumps(scan_result, indent=2)}
Mirror Result: {json.dumps(mirror_result, indent=2)}

Now deliver the final verdict. You must:
1. Deduce consequences of violating or aligning with the design — both short-term and long-term.
2. State actors (Who is affected/responsible) and mechanisms (How effects propagate).
3. Provide revised reasoning that is deductively aligned with the axioms.
4. Deliver a final judgment — decisive, analytically precise, in active voice.
5. Prioritize Final Court accountability over popularity or short-term gain.
6. Calculate the total score based on the scoring rules.

Respond in this exact JSON format:
{{
    "consequences_short_term": ["<consequence1>", ...],
    "consequences_long_term": ["<consequence1>", ...],
    "actors_and_mechanisms": "<who and how>",
    "revised_reasoning": "<deductively aligned reasoning>",
    "final_judgment": "<decisive verdict>",
    "total_score": <integer>
}}"""


def build_correction_prompt(question: str, current_verdict: dict, pass_number: int) -> str:
    """Self-correction pass: find and resolve contradictions."""
    return f"""{FRAMEWORK_PREAMBLE}

{AXIOMS}

{GATE_DEFINITIONS}

{SCORING_RULES}

## TASK — SELF-CORRECTION PASS {pass_number}

Review the following verdict for internal contradictions, misalignments with axioms, \
unjustified neutrality, or avoidance of consequence deduction.

Question: {question}
Current Verdict: {json.dumps(current_verdict, indent=2)}

You must:
1. List any contradictions or weaknesses found.
2. If contradictions exist, provide a corrected version of the verdict.
3. If no contradictions remain, confirm the verdict is sound.

Respond in this exact JSON format:
{{
    "contradictions_found": ["<contradiction1>", ...],
    "is_sound": true or false,
    "corrected_verdict": {{}} or null
}}

If is_sound is true, set corrected_verdict to null.
If is_sound is false, corrected_verdict must contain the full corrected verdict in the same \
format as the original (consequences_short_term, consequences_long_term, \
actors_and_mechanisms, revised_reasoning, final_judgment, total_score)."""


# ---------------------------------------------------------------------------
# Reasoning Engine
# ---------------------------------------------------------------------------

class ReasoningEngine:
    """
    The Criterion reasoning engine.

    Accepts an LLM callable with signature:
        llm_call(prompt: str) -> str

    The LLM layer is fully decoupled — any model (local or API) can be plugged in.
    """

    MAX_CORRECTION_PASSES = 5

    def __init__(self, llm_call: Callable[[str], str]):
        self.llm_call = llm_call

    def _parse_json(self, raw: str) -> dict:
        """Extract and parse JSON from LLM response, handling markdown fences."""
        text = raw.strip()
        # Strip markdown code fences if present
        if "```" in text:
            start = text.find("```")
            # skip the opening fence line
            start = text.find("\n", start) + 1
            end = text.rfind("```")
            text = text[start:end].strip()
        # Try to find JSON object boundaries
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1:
            text = text[first_brace : last_brace + 1]
        return json.loads(text)

    def scan(self, question: str, context: str = "") -> dict:
        """Phase 1: The Scan — identify system type and effects."""
        prompt = build_scan_prompt(question, context)
        raw = self.llm_call(prompt)
        return self._parse_json(raw)

    def mirror(self, question: str, scan_result: dict) -> dict:
        """Phase 2: The Mirror — evaluate through all gates."""
        prompt = build_mirror_prompt(question, scan_result)
        raw = self.llm_call(prompt)
        return self._parse_json(raw)

    def verdict(self, question: str, scan_result: dict, mirror_result: dict) -> dict:
        """Phase 3: The Verdict — deduce consequences and deliver judgment."""
        prompt = build_verdict_prompt(question, scan_result, mirror_result)
        raw = self.llm_call(prompt)
        return self._parse_json(raw)

    def self_correct(self, question: str, current_verdict: dict, pass_number: int) -> dict:
        """Run one self-correction pass. Returns correction result."""
        prompt = build_correction_prompt(question, current_verdict, pass_number)
        raw = self.llm_call(prompt)
        return self._parse_json(raw)

    def _build_gate_scores(self, mirror_result: dict) -> list[GateScore]:
        """Convert mirror result into structured GateScore objects."""
        gate_map = {
            "gate_1_source_integrity": "Source-Integrity",
            "gate_2_structural_consistency": "Structural-Consistency",
            "gate_3_mediation_zeroing": "Mediation-Zeroing",
            "gate_4_origin_aware": "Origin-Aware",
        }
        scores = []
        for key, name in gate_map.items():
            gate_data = mirror_result.get(key, {})
            scores.append(GateScore(
                name=name,
                score=int(gate_data.get("score", 0)),
                result=GateResult.SURVIVE if gate_data.get("result") == "Survive" else GateResult.FAIL,
                reasoning=gate_data.get("reasoning", ""),
            ))
        return scores

    def _build_verdict_object(
        self,
        question: str,
        scan_result: dict,
        mirror_result: dict,
        verdict_result: dict,
        passes: int,
    ) -> Verdict:
        """
        Construct a Verdict object from raw phase results.

        Can be called directly when phases are run individually
        (e.g., for progress display in main.py).
        """
        gate_scores = self._build_gate_scores(mirror_result)
        origin_gate = gate_scores[3] if len(gate_scores) > 3 else None
        tri_axial_scores = gate_scores[:3]

        primary_system = str(scan_result.get("primary_system", "mixed")).upper()
        try:
            system_type = SystemType(primary_system.lower())
        except ValueError:
            system_type = SystemType.MIXED

        return Verdict(
            question=question,
            primary_system=system_type,
            friction_points=scan_result.get("friction_points", []),
            gate_scores=tri_axial_scores,
            origin_gate=origin_gate.result if origin_gate else GateResult.FAIL,
            consequences_short_term=verdict_result.get("consequences_short_term", []),
            consequences_long_term=verdict_result.get("consequences_long_term", []),
            revised_reasoning=verdict_result.get("revised_reasoning", ""),
            final_judgment=verdict_result.get("final_judgment", ""),
            total_score=int(verdict_result.get("total_score", 0)),
            passes=passes,
        )

    def evaluate(self, question: str, context: str = "") -> Verdict:
        """
        Full evaluation pipeline: Scan → Mirror → Verdict → Self-Correction Loop.

        Args:
            question: The input question or subject to evaluate.
            context: Optional stringified prior verdicts for RAG context.

        Returns:
            A fully structured Verdict object.
        """
        # Phase 1: Scan
        scan_result = self.scan(question, context)

        # Phase 2: Mirror
        mirror_result = self.mirror(question, scan_result)

        # Phase 3: Verdict
        verdict_result = self.verdict(question, scan_result, mirror_result)

        # Phase 4: Self-Correction Loop
        passes = 0
        for i in range(1, self.MAX_CORRECTION_PASSES + 1):
            correction = self.self_correct(question, verdict_result, i)
            passes = i
            if correction.get("is_sound", False):
                break
            corrected = correction.get("corrected_verdict")
            if corrected:
                verdict_result = corrected

        return self._build_verdict_object(
            question, scan_result, mirror_result, verdict_result, passes
        )
