"""
Axiom & Gate Selector — المودل يختار الـ Axioms والـ Gates المناسبة للسؤال.

Instead of static mapping (VERSE_LINK → [design, network_effect]),
the LLM reads the raw Axioms and Gates from the Engine and selects
which ones are relevant to the current question.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Callable


logger = logging.getLogger(__name__)


@dataclass
class AxiomGateSelection:
    """Result of LLM selecting axioms and gates for a question."""

    selected_axioms: list[dict] = field(default_factory=list)
    # Each: {"name": str, "description": str, "reason": str}
    selected_gates: list[dict] = field(default_factory=list)
    # Each: {"name": str, "description": str, "check": str, "reason": str}
    raw_response: str = ""


SELECTION_PROMPT = """أنت محلل منطقي. مهمتك تحديد أي مسلّمات (Axioms) وبوابات جودة (Gates) مناسبة لسؤال تفسيري معين.  # pylint: disable=line-too-long

## المسلّمات المتاحة (Axioms):
{axioms}

## بوابات الجودة المتاحة (Gates):
{gates}

## السؤال:
{question}

## المطلوب:
اختر المسلّمات والبوابات المناسبة لهذا السؤال. لكل اختيار، وضّح السبب بجملة واحدة.

أجب بـ JSON فقط:
{{
  "axioms": [
    {{"name": "اسم المسلّمة", "reason": "لماذا مناسبة لهذا السؤال"}}
  ],
  "gates": [
    {{"name": "اسم البوابة", "reason": "لماذا مناسبة لهذا السؤال"}}
  ]
}}
"""


# Parsed axioms and gates for reference
AVAILABLE_AXIOMS = [
    {
        "name": "Transcendence Necessity",
        "key": "transcendence",
        "description": (
            "If something exists it must have a purpose. "
            "Purpose cannot be explained logically without a Transcendent source. "
            "Design necessarily implies purpose."
        ),
    },
    {
        "name": "Final Court Necessity",
        "key": "final_court",
        "description": (
            "Objective moral obligations create real moral debts. "
            "Complete justice requires a final, non-contingent court. "
            "Real moral debts require just resolution."
        ),
    },
    {
        "name": "Design vs. Accident",
        "key": "design",
        "description": (
            "The world, humanity, and societal systems are designed with operational purposes. "
            "Complexity and functional order cannot arise purely by chance."
        ),
    },
    {
        "name": "The Network Effect",
        "key": "network_effect",
        "description": (
            "Every action produces compounded systemic consequences. "
            "Analyses must consider both local and global effects."
        ),
    },
]

AVAILABLE_GATES = [
    {
        "name": "Source-Integrity Gate",
        "key": "source_integrity",
        "description": (
            "Preserve raw truth. Require logical proof backed by evidence. "
            "FAIL: Any reduction or reinterpretation for human convenience. "
            "SURVIVE: Accept raw data as-is."
        ),
        "check": "هل استندت للنص القرآني والحديث الصحيح بدقة؟ لا تنسب للقرآن ما ليس فيه.",
    },
    {
        "name": "Structural-Consistency Gate",
        "key": "structural_consistency",
        "description": (
            "Can explain systemic stability and causality without luck or randomness. "
            "FAIL: Cannot provide logical evidence-based explanation. "
            "SURVIVE: Link events to a singular non-contingent source."
        ),
        "check": "هل الربط بين الآيات والأفكار متسق ومنطقي؟ لا تربط بدون دليل.",
    },
    {
        "name": "Mediation-Zeroing Gate",
        "key": "mediation_zeroing",
        "description": (
            "Human cognition is contingent and finite. "
            "FAIL: Relies on human preference as foundation. "
            "SURVIVE: Treat humans as observers of truth, not masters of it."
        ),
        "check": "هل تجنبت تقديم الرأي البشري على الوحي؟ الرأي ليس حجة بدون دليل شرعي.",
    },
    {
        "name": "Origin-Aware Gate",
        "key": "origin_aware",
        "description": (
            "Does the framework satisfy the Transcendence Necessity Proof? "
            "FAIL: Truth is treated as emergent or contingent. "
            "SURVIVE: Truth derived from a self-authenticating, revealed, transcendent source."
        ),
        "check": "هل المرجعية هي الوحي (قرآن + سنة)؟ لا تعتمد على فلسفة أو ثقافة كمصدر للحق.",
    },
]


def _build_axioms_text() -> str:
    """Format available axioms for the selection prompt."""
    lines = []
    for ax in AVAILABLE_AXIOMS:
        lines.append(f"### {ax['name']}")
        lines.append(ax["description"])
        lines.append("")
    return "\n".join(lines)


def _build_gates_text() -> str:
    """Format available gates for the selection prompt."""
    lines = []
    for g in AVAILABLE_GATES:
        lines.append(f"### {g['name']}")
        lines.append(g["description"])
        lines.append("")
    return "\n".join(lines)


def _parse_selection(response_text: str) -> AxiomGateSelection:  # pylint: disable=too-many-branches
    """Parse LLM response into AxiomGateSelection."""
    text = response_text.strip()

    # Extract JSON
    if "```" in text:
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if match:
            text = match.group(1).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                logger.warning("Could not parse axiom selection response")
                return _default_selection(response_text)
        else:
            return _default_selection(response_text)

    selection = AxiomGateSelection(raw_response=response_text)

    # Map selected axioms to full definitions
    for ax_sel in data.get("axioms", []):
        name = ax_sel.get("name", "")
        reason = ax_sel.get("reason", "")
        # Find matching axiom
        for ax in AVAILABLE_AXIOMS:
            if ax["name"].lower() in name.lower() or name.lower() in ax["name"].lower():
                selection.selected_axioms.append(
                    {
                        "name": ax["name"],
                        "key": ax["key"],
                        "description": ax["description"],
                        "reason": reason,
                    }
                )
                break

    # Map selected gates to full definitions
    for g_sel in data.get("gates", []):
        name = g_sel.get("name", "")
        reason = g_sel.get("reason", "")
        for g in AVAILABLE_GATES:
            if g["name"].lower() in name.lower() or name.lower() in g["name"].lower():
                selection.selected_gates.append(
                    {
                        "name": g["name"],
                        "key": g["key"],
                        "description": g["description"],
                        "check": g["check"],
                        "reason": reason,
                    }
                )
                break

    # Fallback: if nothing was selected, use defaults
    if not selection.selected_axioms:
        selection.selected_axioms = [
            {
                "name": ax["name"],
                "key": ax["key"],
                "description": ax["description"],
                "reason": "default",
            }  # pylint: disable=line-too-long
            for ax in AVAILABLE_AXIOMS[:2]
        ]
    if not selection.selected_gates:
        selection.selected_gates = [
            {
                "name": g["name"],
                "key": g["key"],
                "description": g["description"],
                "check": g["check"],
                "reason": "default",
            }  # pylint: disable=line-too-long
            for g in AVAILABLE_GATES[:2]
        ]

    return selection


def _default_selection(raw: str = "") -> AxiomGateSelection:
    """Return default selection (all axioms and gates) as fallback."""
    return AxiomGateSelection(
        selected_axioms=[
            {
                "name": ax["name"],
                "key": ax["key"],
                "description": ax["description"],
                "reason": "default fallback",
            }  # pylint: disable=line-too-long
            for ax in AVAILABLE_AXIOMS
        ],
        selected_gates=[
            {
                "name": g["name"],
                "key": g["key"],
                "description": g["description"],
                "check": g["check"],
                "reason": "default fallback",
            }  # pylint: disable=line-too-long
            for g in AVAILABLE_GATES
        ],
        raw_response=raw,
    )


def select_axioms_and_gates(question: str, llm_call: Callable) -> AxiomGateSelection:
    """
    Ask the LLM to select relevant axioms and gates for a question.

    Args:
        question: The user's question.
        llm_call: Function that calls the LLM.
                  Signature: llm_call(messages, tools=None) -> {"content": str, ...}

    Returns:
        AxiomGateSelection with the LLM's choices.
    """
    prompt = SELECTION_PROMPT.format(
        axioms=_build_axioms_text(),
        gates=_build_gates_text(),
        question=question,
    )

    response = llm_call(
        messages=[{"role": "user", "content": prompt}],
        tools=None,
    )

    content = response.get("content", "")
    return _parse_selection(content)
