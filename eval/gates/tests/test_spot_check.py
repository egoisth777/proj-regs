"""Tests for spot_check — random audit sampling of evidence reports."""

import pytest
from pathlib import Path

from spot_check import select_spot_checks, verify_file_evidence


class TestSelectSpotChecks:
    def test_selects_requested_sample_size(self):
        answers = [
            {"question": "p1.1", "answer": "yes", "evidence": [{"type": "file_timestamp", "path": "a.md"}]},
            {"question": "p1.3", "answer": "yes", "evidence": [{"type": "reasoning", "text": "x" * 30}]},
            {"question": "o1.1", "answer": "no", "evidence": [{"type": "command_output", "command": "echo hi"}]},
            {"question": "o1.2", "answer": "yes", "evidence": [{"type": "file_timestamp", "path": "b.md"}]},
            {"question": "p2.1", "answer": "yes", "evidence": [{"type": "reasoning", "text": "y" * 30}]},
        ]
        result = select_spot_checks(answers, sample_size=3)
        assert len(result) == 3
        assert all("question" in r for r in result)

    def test_returns_all_if_fewer_than_sample_size(self):
        answers = [
            {"question": "p1.1", "answer": "yes", "evidence": [{"type": "reasoning", "text": "x" * 30}]},
        ]
        result = select_spot_checks(answers, sample_size=3)
        assert len(result) == 1

    def test_prefers_judgment_evidence(self):
        """Reasoning-type evidence should be sampled more often (higher gaming risk)."""
        answers = [
            {"question": "p1.1", "answer": "yes", "evidence": [{"type": "reasoning", "text": "x" * 30}]},
            {"question": "o1.1", "answer": "yes", "evidence": [{"type": "command_output", "command": "echo"}]},
            {"question": "o1.2", "answer": "yes", "evidence": [{"type": "command_output", "command": "echo"}]},
            {"question": "p1.3", "answer": "yes", "evidence": [{"type": "reasoning", "text": "y" * 30}]},
            {"question": "o1.3", "answer": "yes", "evidence": [{"type": "command_output", "command": "echo"}]},
        ]
        # run multiple times and check reasoning questions appear more often
        reasoning_count = 0
        trials = 100
        for _ in range(trials):
            selected = select_spot_checks(answers, sample_size=2)
            for s in selected:
                if any(e.get("type") == "reasoning" for e in s["evidence"]):
                    reasoning_count += 1
        # reasoning should appear in > 50% of selections (2 of 5 are reasoning)
        assert reasoning_count > trials * 0.5

    def test_empty_answers_returns_empty(self):
        result = select_spot_checks([], sample_size=3)
        assert result == []


class TestVerifyFileEvidence:
    def test_existing_file_verifies(self, tmp_path):
        (tmp_path / "proposal.md").write_text("# proposal")
        result = verify_file_evidence(
            file_path="proposal.md",
            project_path=tmp_path,
        )
        assert result["verified"] is True
        assert result["discrepancy"] is None

    def test_missing_file_fails(self, tmp_path):
        result = verify_file_evidence(
            file_path="nonexistent.md",
            project_path=tmp_path,
        )
        assert result["verified"] is False
        assert "not found" in result["discrepancy"]
