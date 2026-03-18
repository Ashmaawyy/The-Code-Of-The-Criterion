"""
Unit tests for human_review.py

Tests:
- Display functions (output verification via capsys)
- HumanReview class workflows with mocked input
- Review verdict flow (approve, correct, reject)
- Browse and search (smoke tests with mocked input)

Note: Interactive CLI functions are tested by mocking builtins.input.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure project root is on the path so bare module imports resolve
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reasoning_engine import Verdict, GateScore, GateResult, SystemType
from verdict_store import VerdictStore
from human_review import (
    display_verdict,
    display_stored_verdict,
    prompt_choice,
    prompt_text,
    prompt_int,
    prompt_list,
    HumanReview,
)


# ---------------------------------------------------------------------------
# Display Functions
# ---------------------------------------------------------------------------

class TestDisplayVerdict:
    def test_displays_question(self, sample_verdict, capsys):
        display_verdict(sample_verdict)
        output = capsys.readouterr().out
        assert "Is interest-based lending just?" in output

    def test_displays_system(self, sample_verdict, capsys):
        display_verdict(sample_verdict)
        output = capsys.readouterr().out
        assert "economic" in output

    def test_displays_gate_scores(self, sample_verdict, capsys):
        display_verdict(sample_verdict)
        output = capsys.readouterr().out
        assert "Source-Integrity" in output
        assert "85/100" in output
        assert "[+]" in output  # survive marker

    def test_displays_origin_gate(self, sample_verdict, capsys):
        display_verdict(sample_verdict)
        output = capsys.readouterr().out
        assert "Origin-Aware Gate: Survive" in output

    def test_displays_consequences(self, sample_verdict, capsys):
        display_verdict(sample_verdict)
        output = capsys.readouterr().out
        assert "Increased debt" in output
        assert "Wealth gap" in output

    def test_displays_judgment(self, sample_verdict, capsys):
        display_verdict(sample_verdict)
        output = capsys.readouterr().out
        assert "equitable exchange" in output

    def test_displays_fail_marker(self, capsys):
        v = Verdict(
            question="test",
            primary_system=SystemType.MIXED,
            friction_points=[],
            gate_scores=[
                GateScore("Test Gate", 30, GateResult.FAIL, "Failed."),
            ],
            origin_gate=GateResult.FAIL,
            consequences_short_term=[], consequences_long_term=[],
            revised_reasoning="", final_judgment="", total_score=0, passes=0,
        )
        display_verdict(v)
        output = capsys.readouterr().out
        assert "[X]" in output


class TestDisplayStoredVerdict:
    def test_displays_stored_dict(self, sample_verdict, capsys):
        data = sample_verdict.to_dict()
        data["id"] = "verdict_123"
        data["status"] = "approved"
        display_stored_verdict(data)
        output = capsys.readouterr().out
        assert "verdict_123" in output
        assert "approved" in output
        assert "interest-based lending" in output


# ---------------------------------------------------------------------------
# Input Helpers (with mocked input)
# ---------------------------------------------------------------------------

class TestPromptChoice:
    @patch("builtins.input", return_value="a")
    def test_valid_choice(self, mock_input):
        result = prompt_choice("Choose: ", ["a", "b", "c"])
        assert result == "a"

    @patch("builtins.input", side_effect=["x", "y", "b"])
    def test_retries_until_valid(self, mock_input):
        result = prompt_choice("Choose: ", ["a", "b"])
        assert result == "b"
        assert mock_input.call_count == 3

    @patch("builtins.input", return_value="A")
    def test_case_insensitive(self, mock_input):
        result = prompt_choice("Choose: ", ["a", "b"])
        assert result == "a"


class TestPromptText:
    @patch("builtins.input", return_value="hello world")
    def test_returns_text(self, mock_input):
        result = prompt_text("Enter: ")
        assert result == "hello world"

    @patch("builtins.input", side_effect=["", "", "finally"])
    def test_retries_on_empty(self, mock_input):
        result = prompt_text("Enter: ")
        assert result == "finally"

    @patch("builtins.input", return_value="")
    def test_allow_empty(self, mock_input):
        result = prompt_text("Enter: ", allow_empty=True)
        assert result == ""


class TestPromptInt:
    @patch("builtins.input", return_value="42")
    def test_returns_int(self, mock_input):
        result = prompt_int("Score: ", 0, 100)
        assert result == 42

    @patch("builtins.input", side_effect=["abc", "150", "50"])
    def test_retries_on_invalid(self, mock_input):
        result = prompt_int("Score: ", 0, 100)
        assert result == 50

    @patch("builtins.input", return_value="0")
    def test_boundary_min(self, mock_input):
        assert prompt_int("Score: ", 0, 100) == 0

    @patch("builtins.input", return_value="100")
    def test_boundary_max(self, mock_input):
        assert prompt_int("Score: ", 0, 100) == 100


class TestPromptList:
    @patch("builtins.input", side_effect=["item 1", "item 2", ""])
    def test_returns_list(self, mock_input):
        result = prompt_list("Enter items:")
        assert result == ["item 1", "item 2"]

    @patch("builtins.input", return_value="")
    def test_empty_list(self, mock_input):
        result = prompt_list("Enter items:")
        assert result == []


# ---------------------------------------------------------------------------
# HumanReview — Approve Flow
# ---------------------------------------------------------------------------

class TestHumanReviewApprove:
    @patch("builtins.input", return_value="a")
    def test_approve_stores_verdict(self, mock_input, tmp_store, sample_verdict):
        review = HumanReview(tmp_store)
        verdict_id = review.review_verdict(sample_verdict)
        assert verdict_id.startswith("verdict_")
        assert tmp_store.collection.count() == 1

    @patch("builtins.input", return_value="a")
    def test_approve_sets_status(self, mock_input, tmp_store, sample_verdict):
        review = HumanReview(tmp_store)
        verdict_id = review.review_verdict(sample_verdict)
        data = tmp_store.get_verdict_by_id(verdict_id)
        assert data["status"] == "approved"


# ---------------------------------------------------------------------------
# HumanReview — Reject Flow
# ---------------------------------------------------------------------------

class TestHumanReviewReject:
    @patch("builtins.input", side_effect=["r", "Reasoning is weak"])
    def test_reject_stores_with_reason(self, mock_input, tmp_store, sample_verdict):
        review = HumanReview(tmp_store)
        verdict_id = review.review_verdict(sample_verdict)
        data = tmp_store.get_verdict_by_id(verdict_id)
        assert data["status"] == "rejected"
        assert data["rejection_reason"] == "Reasoning is weak"
        assert tmp_store.collection.count() == 0


# ---------------------------------------------------------------------------
# HumanReview — Correct Flow
# ---------------------------------------------------------------------------

class TestHumanReviewCorrect:
    @patch("builtins.input", side_effect=[
        "c",       # choose correct
        "n",       # don't replace friction points
        "n",       # don't correct gate scores
        "n",       # don't correct origin gate
        "n",       # don't replace short-term consequences
        "n",       # don't replace long-term consequences
        "n",       # don't replace reasoning
        "n",       # don't replace judgment
        "y",       # correct score
        "95",      # new score
        "y",       # confirm correction
    ])
    def test_correct_with_score_change(self, mock_input, tmp_store, sample_verdict):
        review = HumanReview(tmp_store)
        verdict_id = review.review_verdict(sample_verdict)
        data = tmp_store.get_verdict_by_id(verdict_id)
        assert data["status"] == "corrected"
        assert data["total_score"] == 95

    @patch("builtins.input", side_effect=[
        "c",       # choose correct
        "n",       # don't replace friction points
        "n",       # don't correct gate scores
        "n",       # don't correct origin gate
        "n",       # don't replace short-term consequences
        "n",       # don't replace long-term consequences
        "n",       # don't replace reasoning
        "n",       # don't replace judgment
        "n",       # don't correct score
        "n",       # decline confirmation
        "a",       # then approve original
    ])
    def test_correct_then_decline_then_approve(self, mock_input, tmp_store, sample_verdict):
        review = HumanReview(tmp_store)
        verdict_id = review.review_verdict(sample_verdict)
        data = tmp_store.get_verdict_by_id(verdict_id)
        assert data["status"] == "approved"
