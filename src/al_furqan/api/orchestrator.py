"""
Al-Furqan Orchestrator

The CENTRAL piece that connects Engine + KB + Graph + Z3 + Storage.
This is the only component that knows about all layers.
"""
# pylint: disable=logging-fstring-interpolation
# pylint: disable=broad-exception-caught

import hashlib
import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field

from al_furqan.engine.models import (
    DualPerspectiveVerdict,
    Verdict,
)
from al_furqan.engine.security.audit import AuditLogger
from al_furqan.engine.security.integrity import IntegrityVerifier
from al_furqan.engine.security.output_validator import OutputValidator
from al_furqan.engine.security.prompt_guard import PromptGuard
from al_furqan.engine.symbolic.verifier import VerificationResult

logger = logging.getLogger("al_furqan.orchestrator")


def generate_eval_id() -> str:
    """Generate a unique evaluation ID."""
    return f"eval_{uuid.uuid4().hex}"


@dataclass
class EvaluationResult:  # pylint: disable=too-many-instance-attributes
    """Complete evaluation result — what the Orchestrator returns."""

    # User-facing response
    response_text: str  # Natural language response for the user

    # Verdict data (for logs/dashboard)
    verdict: Verdict

    # Dual perspective (if embedded assumptions detected)
    dual_verdict: DualPerspectiveVerdict | None = None

    # KB sources used
    sources: list = field(default_factory=list)

    # Z3 verification
    z3_result: VerificationResult | None = None

    # Metadata
    evaluation_id: str = ""
    processing_time_ms: float = 0.0
    model_used: str = ""

    def to_log_dict(self) -> dict:
        """Full evaluation data for dashboard/logging."""
        result = {
            "evaluation_id": self.evaluation_id,
            "response_text": self.response_text,
            "verdict": self.verdict.to_dict()
            if hasattr(self.verdict, "to_dict")
            else str(self.verdict),  # pylint: disable=line-too-long
            "sources": self.sources,
            "processing_time_ms": self.processing_time_ms,
            "model_used": self.model_used,
        }
        if self.dual_verdict:
            result["dual_verdict"] = (
                self.dual_verdict.to_dict()
                if hasattr(self.dual_verdict, "to_dict")
                else str(self.dual_verdict)
            )
        if self.z3_result:
            result["z3_result"] = {
                "consistent": self.z3_result.consistent,
                "proof": self.z3_result.proof,
                "contradictions": self.z3_result.contradictions,
                "verification_time_ms": self.z3_result.verification_time_ms,
            }
        return result

    def to_user_response(self) -> str:
        """Just the user-facing response text."""
        return self.response_text


class Orchestrator:  # pylint: disable=too-many-instance-attributes
    """
    The ONLY component that knows about all layers.
    Connects Engine + KB + Graph + Z3 + Storage.
    """

    def __init__(  # pylint: disable=too-many-arguments, too-many-positional-arguments
        self,
        engine_pipeline,
        kb_retriever=None,
        graph_store=None,
        knowledge_linker=None,
        verdict_store=None,
        feedback_store=None,
        symbolic_verifier=None,
        llm_fn: Callable[[str], str] | None = None,
    ):
        self.engine = engine_pipeline
        self.kb = kb_retriever
        self.graph = graph_store
        self.linker = knowledge_linker
        self.store = verdict_store
        self.feedback = feedback_store
        self.verifier = symbolic_verifier
        self.llm_fn = llm_fn

        # Security components
        self.integrity_verifier = IntegrityVerifier()
        self.prompt_guard = PromptGuard()
        self.output_validator = OutputValidator()
        self.audit_logger = AuditLogger()

    async def evaluate(  # pylint: disable=too-many-locals
        self, question: str, use_kb: bool = False, use_z3: bool = True
    ) -> EvaluationResult:
        """
        Full evaluation pipeline:
        1. Detect intent (informational vs evaluative)
        2. Check for embedded assumptions → dual perspective
        3. Retrieve KB context (if use_kb)
        4. Expand via graph (if available)
        5. Run gate evaluation (chains + deterministic scoring)
        6. Z3 verification (if use_z3)
        7. Generate user-facing response via LLM
        8. Store verdict + log everything
        9. Return EvaluationResult
        """
        start = time.time()
        eval_id = generate_eval_id()

        # Security: Verify axiom integrity before every evaluation
        self.integrity_verifier.verify_or_die()

        # Security: Scan for prompt injection
        scan_result = self.prompt_guard.scan(question)
        injection_detected = not scan_result.is_safe
        if injection_detected:
            logger.warning(
                f"Prompt injection detected in {eval_id}:"
                f"patterns={scan_result.matched_patterns}"
            )
            # Use wrapped input to neutralize injection
            question = scan_result.sanitized_input

        # Step 3-4: KB retrieval + graph expansion
        context = ""
        sources = []
        if use_kb and self.kb:
            try:
                kb_result = self.kb.retrieve(question)
                context = (
                    kb_result.formatted_context
                    if hasattr(kb_result, "formatted_context")
                    else str(kb_result)
                )
                sources = kb_result.sources if hasattr(kb_result, "sources") else []
            except Exception as e:
                logger.warning(f"KB retrieval failed: {e}")

        # Step 5: Gate evaluation via the existing pipeline
        verdict = self.engine.evaluate(question, context=context)

        # Step 6: Z3 verification
        z3_result = None
        if use_z3 and self.verifier:
            try:
                verdict_data = {
                    "exists": True,
                    "has_purpose": True,
                }
                z3_result = self.verifier.verify_verdict(verdict_data)
            except Exception as e:
                logger.warning(f"Z3 verification failed: {e}")

        # Step 7: Generate user-facing response
        response_text = self._generate_response(question, verdict, sources, z3_result)

        # Security: Validate output
        validation = self.output_validator.validate_verdict(verdict)
        if not validation.valid:
            logger.warning(
                f"Output validation issues in {eval_id}: {validation.issues}"
            )

        # Step 8: Store
        if self.store:
            try:
                self.store.store(verdict)
            except Exception as e:
                logger.warning(f"Verdict storage failed: {e}")

        processing_time = (time.time() - start) * 1000

        # Security: Audit log
        try:
            hashes = self.integrity_verifier.get_hashes()
            gate_scores_data = (
                [
                    {"name": g.name, "score": g.score, "result": g.result.value}
                    for g in verdict.gate_scores
                ]
                if hasattr(verdict, "gate_scores")
                else []
            )

            self.audit_logger.log_evaluation(
                evaluation_id=eval_id,
                question_hash=hashlib.sha256(question.encode()).hexdigest(),
                axiom_hash=hashes["axiom_hash"],
                gate_hash=hashes["gate_hash"],
                gate_scores=gate_scores_data,
                z3_result=z3_result.consistent if z3_result else None,
                model_used=getattr(verdict, "model_name", "") or "",
                processing_time_ms=processing_time,
                prompt_injection_detected=injection_detected,
            )
        except Exception as e:
            logger.warning(f"Audit logging failed: {e}")

        return EvaluationResult(
            response_text=response_text,
            verdict=verdict,
            sources=sources,
            z3_result=z3_result,
            evaluation_id=eval_id,
            processing_time_ms=processing_time,
        )

    async def evaluate_grounded(self, question: str) -> EvaluationResult:
        """Always use KB — the target flow."""
        return await self.evaluate(question, use_kb=True, use_z3=True)

    def _generate_response(
        self, question: str, verdict: Verdict, sources: list, z3_result
    ) -> str:
        """
        Generate natural language response from verdict.
        This is where the LLM acts as TONGUE — it communicates
        the verdict in human-readable form.
        """
        if self.llm_fn:
            prompt = (
                f"Based on this evaluation, write a clear response to the user.\n\n"
                f"Question: {question}\n\n"
                f"""Verdict: {
                    verdict.final_judgment
                    if hasattr(verdict, "final_judgment")
                    else "N/A"
                }\n"""
                f"Score: {verdict.total_score}/100\n\n"
                f"Sources: {len(sources)} sources found\n\n"
                f"""Z3 Verification: {
                    "Consistent"
                    if z3_result and z3_result.consistent
                    else "Inconsistent"
                    if z3_result
                    else "N/A"
                }\n\n"""
                f"Write a natural, clear response.\n"
                f"""Respond with the scores structured at the top
                in a json format and the final response at the bottom.
                The response should be concise, factual, and avoid any technical jargon.\n\n"""
            )
            try:
                response = self.llm_fn(prompt)
                return response
            except Exception as e:
                logger.warning(f"LLM response generation failed: {e}")

        # Fallback: use verdict judgment directly
        if hasattr(verdict, "final_judgment") and verdict.final_judgment:
            return verdict.final_judgment
        return f"Evaluation complete. Score: {verdict.total_score}/100"
