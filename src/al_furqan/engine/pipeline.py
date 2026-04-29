"""
Al-Furqan Evaluation Pipeline

Core evaluation logic extracted from ReasoningEngine.
Implements Scan → Mirror → Verdict → Self-Correction pipeline.
"""

import json
import logging
import re
from typing import Callable

from al_furqan.engine.models import (
    SystemType,
    GateResult,
    GateScore,
    Verdict,
    DualPerspectiveVerdict,
    InformationalResponse,
)
from al_furqan.engine.prompts import (
    build_scan_prompt,
    build_mirror_prompt,
    build_verdict_prompt,
    build_correction_prompt,
    build_intent_detection_prompt,
    build_informational_prompt,
    sanitize_input,
)

logger = logging.getLogger("al_furqan.engine.pipeline")


class EvaluationPipeline:
    """
    The Criterion evaluation pipeline.

    Accepts an LLM callable with signature:
        llm_call(prompt: str) -> str

    The LLM layer is fully decoupled — any model (local or API) can be plugged in.
    """

    MAX_CORRECTION_PASSES: int = 5

    def __init__(self, llm_call: Callable[[str], str]):
        self.llm_call = llm_call

    def _parse_json(self, raw: str) -> dict:
        """Extract and parse JSON from LLM response, handling various formats."""
        text = raw.strip()

        # Strategy 1: Try to parse as-is
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract from markdown code fences
        fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if fence_match:
            try:
                return json.loads(fence_match.group(1).strip())
            except json.JSONDecodeError:
                # Try to repair common JSON issues
                repaired = self._repair_json(fence_match.group(1).strip())
                if repaired is not None:
                    return repaired

        # Strategy 3: Find JSON object boundaries (outermost braces)
        depth = 0
        start = -1
        for i, ch in enumerate(text):
            if ch == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0 and start != -1:
                    try:
                        return json.loads(text[start : i + 1])
                    except json.JSONDecodeError:
                        repaired = self._repair_json(text[start : i + 1])
                        if repaired is not None:
                            return repaired
                        start = -1
                        continue

        raise json.JSONDecodeError(
            "No valid JSON object found in LLM response", text, 0
        )

    @staticmethod
    def _repair_json(text: str) -> dict | None:
        """Attempt to repair common JSON errors from LLM output."""
        # Fix: missing comma between array items or object keys
        pattern = r'"\s*\n(\s*")'
        replacement = r'",\n\1'
        fixed = re.sub(pattern, replacement, text)
        # Fix: trailing commas before closing brackets
        fixed = re.sub(r",\s*([}\]])", r"\1", fixed)
        # Fix: missing closing brackets
        opens = fixed.count("{") - fixed.count("}")
        fixed += "}" * max(0, opens)
        opens = fixed.count("[") - fixed.count("]")
        fixed += "]" * max(0, opens)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            return None

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

    def self_correct(
        self, question: str, current_verdict: dict, pass_number: int
    ) -> dict:
        """Run one self-correction pass. Returns correction result."""
        prompt = build_correction_prompt(question, current_verdict, pass_number)
        raw = self.llm_call(prompt)
        try:
            return self._parse_json(raw)
        except json.JSONDecodeError:
            logger.warning(
                "Self-correction pass %d returned unparseable response, treating as sound",
                pass_number,
            )  # pylint: disable=line-too-long
            return {
                "is_sound": True,
                "contradictions_found": [],
                "corrected_verdict": None,
            }

    def _build_gate_scores(self, mirror_result: dict) -> list[GateScore]:
        """Convert mirror result into structured GateScore objects."""
        gate_map = {
            "gate_1_source_integrity": "Source-Integrity",
            # pylint: disable=line-too-long
            "gate_2_structural_consistency": "Structural-Consistency",
            "gate_3_mediation_zeroing": "Mediation-Zeroing",
            "gate_4_origin_aware": "Origin-Aware",
        }
        scores = []
        for key, name in gate_map.items():
            gate_data = mirror_result.get(key, {})
            result = (
                GateResult.SURVIVE
                if gate_data.get("result") == "Survive"
                else GateResult.FAIL
            )
            scores.append(
                GateScore(
                    name=name,
                    score=int(gate_data.get("score", 0)),
                    result=result,
                    reasoning=gate_data.get("reasoning", ""),
                )
            )
        return scores

    def _build_verdict_object(  # pylint: disable=too-many-arguments,too-many-positional-arguments
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

    def detect_intent(self, question: str) -> dict:
        """Phase 0: Detect question intent — system evaluation vs claim judgment."""
        prompt = build_intent_detection_prompt(question)
        raw = self.llm_call(prompt)
        try:
            return self._parse_json(raw)
        except json.JSONDecodeError:
            logger.warning(
                "Intent detection returned unparseable response, defaulting to claim_judgment"
            )  # pylint: disable=line-too-long
            return {
                "intent_type": "claim_judgment",
                "target_system": question,
                "embedded_assumptions": [],
                "neutralized_question": question,
            }

    def answer_informational(self, question: str) -> InformationalResponse:
        """Handle informational questions — no gate evaluation needed."""
        prompt = build_informational_prompt(question)
        raw = self.llm_call(prompt)
        try:
            data = self._parse_json(raw)
        except json.JSONDecodeError:
            data = {
                "answer": raw,
                "category": "general",
                "sources_suggested": [],
                "related_topics": [],
            }  # pylint: disable=line-too-long

        return InformationalResponse(
            question=question,
            answer=data.get("answer", raw),
            category=data.get("category", "general"),
            sources_suggested=data.get("sources_suggested", []),
            related_topics=data.get("related_topics", []),
        )

    def evaluate_smart(self, question: str, context: str = ""):
        """
        Smart Evaluation — Routes based on intent detection.

        Returns:
            InformationalResponse | DualPerspectiveVerdict
        """
        question = sanitize_input(question)

        logger.info("Phase 0: Detecting intent...")
        intent = self.detect_intent(question)
        intent_type = intent.get("intent_type", "claim_judgment")

        if intent_type == "informational":
            logger.info("Informational question detected — skipping gates")
            return self.answer_informational(question)

        return self.evaluate_dual(question, context)

    def evaluate_dual(self, question: str, context: str = "") -> DualPerspectiveVerdict:
        """
        Dual-Perspective Evaluation (Solution 3).
        """
        question = sanitize_input(question)

        logger.info("Phase 0: Detecting intent...")
        intent = self.detect_intent(question)
        intent_type = intent.get("intent_type", "claim_judgment")
        target_system = intent.get("target_system", question)
        embedded_assumptions = intent.get("embedded_assumptions", [])
        neutralized_question = intent.get("neutralized_question", question)

        logger.info("Evaluating target system: %s", target_system)
        system_verdict = self.evaluate(neutralized_question, context)

        assumptions_verdict = None
        if embedded_assumptions:
            prefix = "Evaluate the following assumptions as a framework: "
            # pylint: disable=line-too-long
            assumptions_question = prefix + "; ".join(embedded_assumptions)
            logger.info("Evaluating embedded assumptions...")
            try:
                assumptions_verdict = self.evaluate(assumptions_question, context)
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.warning("Assumptions evaluation failed: %s", e)

        # pylint: disable=line-too-long
        return DualPerspectiveVerdict(
            intent_type=intent_type,
            target_system=target_system,
            embedded_assumptions=embedded_assumptions,
            neutralized_question=neutralized_question,
            system_verdict=system_verdict,
            assumptions_verdict=assumptions_verdict,
        )

    def evaluate(self, question: str, context: str = "") -> Verdict:
        """
        Full evaluation pipeline: Scan → Mirror → Verdict → Self-Correction Loop.
        """
        question = sanitize_input(question)

        scan_result = self.scan(question, context)
        mirror_result = self.mirror(question, scan_result)
        verdict_result = self.verdict(question, scan_result, mirror_result)

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
