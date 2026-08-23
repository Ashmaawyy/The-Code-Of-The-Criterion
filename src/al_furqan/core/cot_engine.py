"""COT-Enabled Reasoning Engine for Al-Furqan."""

from collections.abc import Callable

from al_furqan.core.cot import COTMonitorResult
from al_furqan.core.cot_prompts import (
    build_cot_mirror_prompt,
    build_cot_monitor_prompt,
)
from al_furqan.core.reasoning_engine import ReasoningEngine, Verdict


class COTReasoningEngine(ReasoningEngine):
    """Extended reasoning engine with COT monitoring.

    Adds Chain of Thought step-level reasoning to the mirror phase
    and an independent COT monitor that audits reasoning integrity.

    The monitor can use a different (possibly cheaper) LLM to reduce costs
    while maintaining oversight quality.
    """

    def __init__(
        self,
        llm_call: Callable[[str], str],
        monitor_llm_call: Callable[[str], str] | None = None,
    ):  # pylint: disable=line-too-long
        super().__init__(llm_call)
        # The monitor can use a different (possibly cheaper) LLM
        self.monitor_llm_call = monitor_llm_call or llm_call

    def mirror_with_cot(self, question: str, scan_result: dict) -> dict:
        """Phase 2 with COT reasoning steps."""
        prompt = build_cot_mirror_prompt(question, scan_result)
        raw = self.llm_call(prompt)
        return self._parse_json(raw)

    def monitor_cot(self, question: str, mirror_result: dict) -> COTMonitorResult:
        """Run the COT monitor on mirror results.

        Uses the monitor LLM (which may differ from the main LLM)
        to independently audit the reasoning chain.
        """
        prompt = build_cot_monitor_prompt(question, mirror_result)
        raw = self.monitor_llm_call(prompt)
        result = self._parse_json(raw)
        return COTMonitorResult.from_dict(result)

    def evaluate_with_cot(
        self, question: str, context: str = ""
    ) -> tuple[Verdict, COTMonitorResult]:  # pylint: disable=line-too-long
        """Full evaluation with COT monitoring.

        Pipeline: Scan → Mirror(COT) → COT Monitor → Verdict → Self-Correction

        Returns:
            A tuple of (Verdict, COTMonitorResult).
        """
        # Phase 1: Scan (same as base)
        scan_result = self.scan(question, context)

        # Phase 2: Mirror with COT
        mirror_result = self.mirror_with_cot(question, scan_result)

        # Phase 2.5: COT Monitor
        cot_monitor = self.monitor_cot(question, mirror_result)

        # Phase 3: Verdict (same as base)
        verdict_result = self.verdict(question, scan_result, mirror_result)

        # Phase 4: Self-Correction
        passes = 0
        for i in range(1, self.MAX_CORRECTION_PASSES + 1):
            correction = self.self_correct(question, verdict_result, i)
            passes = i
            if correction.get("is_sound", False):
                break
            corrected = correction.get("corrected_verdict")
            if corrected:
                verdict_result = corrected

        verdict = self._build_verdict_object(
            question, scan_result, mirror_result, verdict_result, passes
        )

        return verdict, cot_monitor
