"""
Unit tests for human_review.py

Tests:
- Display functions (output verification via capsys)
- HumanReview class workflows with mocked input
- Review verdict flow (approve, correct, reject)
- Browse and search (smoke tests with mocked input)

Note: Interactive CLI functions are tested by mocking builtins.input.
"""

import logging
from unittest.mock import patch

from al_furqan.core.reasoning_engine import GateResult, GateScore, SystemType, Verdict
from al_furqan.review.human_review import (
    HumanReview,
    display_stored_verdict,
    display_verdict,
    prompt_choice,
    prompt_int,
    prompt_list,
    prompt_text,
)

logger = logging.getLogger("test_human_review")


# ---------------------------------------------------------------------------
# Display Functions
# ---------------------------------------------------------------------------


class TestDisplayVerdict:
    """TestDisplayVerdict class."""

    def test_displays_question(self, sample_verdict, capsys):
        """Test displays_question."""
        logger.info("Testing display_verdict shows question text")
        display_verdict(sample_verdict)
        output = capsys.readouterr().out
        logger.debug("Output length: %d chars", len(output))
        assert "Is interest-based lending just?" in output
        logger.info("Question text found in display output")

    def test_displays_system(self, sample_verdict, capsys):
        """Test displays_system."""
        logger.info("Testing display_verdict shows primary system")
        display_verdict(sample_verdict)
        output = capsys.readouterr().out
        assert "economic" in output
        logger.info("Primary system 'economic' found in output")

    def test_displays_gate_scores(self, sample_verdict, capsys):
        """Test displays_gate_scores."""
        logger.info("Testing display_verdict shows gate scores with markers")
        display_verdict(sample_verdict)
        output = capsys.readouterr().out
        logger.debug("Checking for Source-Integrity, 85/100, and [+] marker")
        assert "Source-Integrity" in output
        assert "85/100" in output
        assert "[+]" in output  # survive marker
        logger.info("Gate scores displayed with correct names, values, and markers")

    def test_displays_origin_gate(self, sample_verdict, capsys):
        """Test displays_origin_gate."""
        logger.info("Testing display_verdict shows origin gate result")
        display_verdict(sample_verdict)
        output = capsys.readouterr().out
        assert "Origin-Aware Gate: Survive" in output
        logger.info("Origin gate 'Survive' displayed correctly")

    def test_displays_consequences(self, sample_verdict, capsys):
        """Test displays_consequences."""
        logger.info(
            "Testing display_verdict shows short-term and long-term consequences"
        )
        display_verdict(sample_verdict)
        output = capsys.readouterr().out
        assert "Increased debt" in output
        assert "Wealth gap" in output
        logger.info("Both short-term and long-term consequences displayed")

    def test_displays_judgment(self, sample_verdict, capsys):
        """Test displays_judgment."""
        logger.info("Testing display_verdict shows final judgment")
        display_verdict(sample_verdict)
        output = capsys.readouterr().out
        assert "equitable exchange" in output
        logger.info("Final judgment text found in output")

    def test_displays_fail_marker(self, capsys):
        """Test displays_fail_marker."""
        logger.info("Testing display_verdict shows [X] marker for FAIL gate")
        v = Verdict(
            question="test",
            primary_system=SystemType.MIXED,
            friction_points=[],
            gate_scores=[
                GateScore("Test Gate", 30, GateResult.FAIL, "Failed."),
            ],
            origin_gate=GateResult.FAIL,
            consequences_short_term=[],
            consequences_long_term=[],
            revised_reasoning="",
            final_judgment="",
            total_score=0,
            passes=0,
        )
        display_verdict(v)
        output = capsys.readouterr().out
        logger.debug("Output contains [X]: %s", "[X]" in output)
        assert "[X]" in output
        logger.info("FAIL marker [X] displayed correctly")


class TestDisplayStoredVerdict:  # pylint: disable=too-few-public-methods
    """TestDisplayStoredVerdict class."""

    def test_displays_stored_dict(self, sample_verdict, capsys):
        """Test displays_stored_dict."""
        logger.info("Testing display_stored_verdict shows ID, status, and question")
        data = sample_verdict.to_dict()
        data["id"] = "verdict_123"
        data["status"] = "approved"
        display_stored_verdict(data)
        output = capsys.readouterr().out
        logger.debug("Output length: %d chars", len(output))
        assert "verdict_123" in output
        assert "approved" in output
        assert "interest-based lending" in output
        logger.info("Stored verdict display includes ID, status, and question")


# ---------------------------------------------------------------------------
# Input Helpers (with mocked input)
# ---------------------------------------------------------------------------


class TestPromptChoice:
    """TestPromptChoice class."""

    @patch("builtins.input", return_value="a")
    def test_valid_choice(self, _mock_input):
        """Test valid_choice."""
        logger.info("Testing prompt_choice with valid input 'a'")
        result = prompt_choice("Choose: ", ["a", "b", "c"])
        logger.debug("Input='a', result='%s'", result)
        assert result == "a"
        logger.info("Valid choice returned correctly")

    @patch("builtins.input", side_effect=["x", "y", "b"])
    def test_retries_until_valid(self, mock_input):
        """Test retries_until_valid."""
        logger.info(
            "Testing prompt_choice retries on invalid inputs ('x', 'y') then accepts 'b'"
        )
        result = prompt_choice("Choose: ", ["a", "b"])
        logger.debug("Attempts: %d, final result='%s'", mock_input.call_count, result)
        assert result == "b"
        assert mock_input.call_count == 3
        logger.info(
            "Retried %d times before accepting valid input", mock_input.call_count
        )

    @patch("builtins.input", return_value="A")
    def test_case_insensitive(self, _mock_input):
        """Test case_insensitive."""
        logger.info(
            "Testing prompt_choice is case-insensitive (input='A', valid=['a','b'])"
        )
        result = prompt_choice("Choose: ", ["a", "b"])
        logger.debug("Input='A', result='%s'", result)
        assert result == "a"
        logger.info("Case-insensitive matching works correctly")


class TestPromptText:
    """TestPromptText class."""

    @patch("builtins.input", return_value="hello world")
    def test_returns_text(self, _mock_input):
        """Test returns_text."""
        logger.info("Testing prompt_text returns entered text")
        result = prompt_text("Enter: ")
        logger.debug("result='%s'", result)
        assert result == "hello world"
        logger.info("Text input returned correctly")

    @patch("builtins.input", side_effect=["", "", "finally"])
    def test_retries_on_empty(self, mock_input):
        """Test retries_on_empty."""
        logger.info("Testing prompt_text retries on empty input until non-empty")
        result = prompt_text("Enter: ")
        logger.debug("Attempts: %d, result='%s'", mock_input.call_count, result)
        assert result == "finally"
        logger.info(
            "Retried %d times before accepting non-empty input", mock_input.call_count
        )

    @patch("builtins.input", return_value="")
    def test_allow_empty(self, _mock_input):
        """Test allow_empty."""
        logger.info("Testing prompt_text with allow_empty=True")
        result = prompt_text("Enter: ", allow_empty=True)
        logger.debug("result='%s'", result)
        assert result == ""
        logger.info("Empty input accepted when allow_empty=True")


class TestPromptInt:
    """TestPromptInt class."""

    @patch("builtins.input", return_value="42")
    def test_returns_int(self, _mock_input):
        """Test returns_int."""
        logger.info("Testing prompt_int returns parsed integer")
        result = prompt_int("Score: ", 0, 100)
        logger.debug("Input='42', result=%d", result)
        assert result == 42
        logger.info("Integer input parsed correctly")

    @patch("builtins.input", side_effect=["abc", "150", "50"])
    def test_retries_on_invalid(self, mock_input):
        """Test retries_on_invalid."""
        logger.info(
            "Testing prompt_int retries on 'abc' (NaN) and '150' (out of range)"
        )
        result = prompt_int("Score: ", 0, 100)
        logger.debug("Attempts: %d, result=%d", mock_input.call_count, result)
        assert result == 50
        logger.info(
            "Retried %d times: rejected 'abc', '150', accepted '50'",
            mock_input.call_count,
        )

    @patch("builtins.input", return_value="0")
    def test_boundary_min(self, _mock_input):
        """Test boundary_min."""
        logger.info("Testing prompt_int at minimum boundary (0)")
        result = prompt_int("Score: ", 0, 100)
        logger.debug("result=%d", result)
        assert result == 0
        logger.info("Minimum boundary value accepted")

    @patch("builtins.input", return_value="100")
    def test_boundary_max(self, _mock_input):
        """Test boundary_max."""
        logger.info("Testing prompt_int at maximum boundary (100)")
        result = prompt_int("Score: ", 0, 100)
        logger.debug("result=%d", result)
        assert result == 100
        logger.info("Maximum boundary value accepted")


class TestPromptList:
    """TestPromptList class."""

    @patch("builtins.input", side_effect=["item 1", "item 2", ""])
    def test_returns_list(self, _mock_input):
        """Test returns_list."""
        logger.info("Testing prompt_list collects items until empty input")
        result = prompt_list("Enter items:")
        logger.debug("Collected %d items: %s", len(result), result)
        assert result == ["item 1", "item 2"]
        logger.info("Collected %d items correctly", len(result))

    @patch("builtins.input", return_value="")
    def test_empty_list(self, _mock_input):
        """Test empty_list."""
        logger.info("Testing prompt_list returns empty list on immediate empty input")
        result = prompt_list("Enter items:")
        logger.debug("Result: %s", result)
        assert not result
        logger.info("Empty list returned correctly")


# ---------------------------------------------------------------------------
# HumanReview — Approve Flow
# ---------------------------------------------------------------------------


class TestHumanReviewApprove:
    """TestHumanReviewApprove class."""

    @patch("builtins.input", return_value="a")
    def test_approve_stores_verdict(self, _mock_input, tmp_store, sample_verdict):
        """Test approve_stores_verdict."""
        logger.info("Testing approve flow — verdict should be stored and indexed")
        review = HumanReview(tmp_store)
        verdict_id = review.review_verdict(sample_verdict)
        logger.debug(
            "Verdict ID: %s, chroma count: %d", verdict_id, tmp_store.collection.count()
        )
        assert verdict_id.startswith("verdict_")
        assert tmp_store.collection.count() == 1
        logger.info(
            "Approved verdict stored with ID=%s, indexed in ChromaDB", verdict_id
        )

    @patch("builtins.input", return_value="a")
    def test_approve_sets_status(self, _mock_input, tmp_store, sample_verdict):
        """Test approve_sets_status."""
        logger.info("Testing approve flow sets status='approved' in stored data")
        review = HumanReview(tmp_store)
        verdict_id = review.review_verdict(sample_verdict)
        data = tmp_store.get_verdict_by_id(verdict_id)
        logger.debug("Stored status: %s", data["status"])
        assert data["status"] == "approved"
        logger.info("Stored verdict has status='approved'")


# ---------------------------------------------------------------------------
# HumanReview — Reject Flow
# ---------------------------------------------------------------------------


class TestHumanReviewReject:  # pylint: disable=too-few-public-methods
    """TestHumanReviewReject class."""

    @patch("builtins.input", side_effect=["r", "Reasoning is weak"])
    def test_reject_stores_with_reason(self, _mock_input, tmp_store, sample_verdict):
        """Test reject_stores_with_reason."""
        logger.info(
            "Testing reject flow — user rejects with reason 'Reasoning is weak'"
        )
        review = HumanReview(tmp_store)
        verdict_id = review.review_verdict(sample_verdict)
        data = tmp_store.get_verdict_by_id(verdict_id)
        logger.debug(
            "Status: %s, rejection_reason: '%s', chroma count: %d",
            data["status"],
            data["rejection_reason"],
            tmp_store.collection.count(),
        )
        assert data["status"] == "rejected"
        assert data["rejection_reason"] == "Reasoning is weak"
        assert tmp_store.collection.count() == 0
        logger.info("Rejected verdict stored with reason, not indexed in ChromaDB")


# ---------------------------------------------------------------------------
# HumanReview — Correct Flow
# ---------------------------------------------------------------------------


class TestHumanReviewCorrect:
    """TestHumanReviewCorrect class."""

    @patch(
        "builtins.input",
        side_effect=[
            "c",  # choose correct
            "n",  # don't replace friction points
            "n",  # don't correct gate scores
            "n",  # don't correct origin gate
            "n",  # don't replace short-term consequences
            "n",  # don't replace long-term consequences
            "n",  # don't replace reasoning
            "n",  # don't replace judgment
            "y",  # correct score
            "95",  # new score
            "y",  # confirm correction
        ],
    )
    def test_correct_with_score_change(self, mock_input, tmp_store, sample_verdict):
        """Test correct_with_score_change."""
        logger.info("Testing correct flow — changing score from 85 to 95")
        review = HumanReview(tmp_store)
        verdict_id = review.review_verdict(sample_verdict)
        data = tmp_store.get_verdict_by_id(verdict_id)
        logger.debug(
            "Status: %s, total_score: %d, input call count: %d",
            data["status"],
            data["total_score"],
            mock_input.call_count,
        )
        assert data["status"] == "corrected"
        assert data["total_score"] == 95
        logger.info(
            "Correction flow: score changed 85→95, status='corrected', %d inputs consumed",
            mock_input.call_count,
        )

    @patch(
        "builtins.input",
        side_effect=[
            "c",  # choose correct
            "n",  # don't replace friction points
            "n",  # don't correct gate scores
            "n",  # don't correct origin gate
            "n",  # don't replace short-term consequences
            "n",  # don't replace long-term consequences
            "n",  # don't replace reasoning
            "n",  # don't replace judgment
            "n",  # don't correct score
            "n",  # decline confirmation
            "a",  # then approve original
        ],
    )
    def test_correct_then_decline_then_approve(
        self, mock_input, tmp_store, sample_verdict
    ):
        """Test correct_then_decline_then_approve."""
        logger.info(
            "Testing correct flow — decline correction then fall back to approve"
        )
        review = HumanReview(tmp_store)
        verdict_id = review.review_verdict(sample_verdict)
        data = tmp_store.get_verdict_by_id(verdict_id)
        logger.debug(
            "Final status: %s, input call count: %d",
            data["status"],
            mock_input.call_count,
        )  # pylint: disable=line-too-long
        assert data["status"] == "approved"
        logger.info(
            "Correction declined → approved, %d inputs consumed", mock_input.call_count
        )
