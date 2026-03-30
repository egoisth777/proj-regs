"""Tests for loop.py — phase state machine + tier progression."""

import json
import pytest
from pathlib import Path

from loop import (
    get_current_phase,
    advance_phase,
    prepare_mutation,
    decide_outcome,
    check_tier_progression,
    VALID_TRANSITIONS,
)


class TestGetCurrentPhase:
    def test_returns_current_phase(self, manifest_path):
        assert get_current_phase(manifest_path) == "prepare"

    def test_raises_on_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            get_current_phase(tmp_path / "nonexistent.json")


class TestAdvancePhase:
    def test_prepare_to_mutate(self, manifest_path):
        new_phase = advance_phase(manifest_path, {"directive": "improve p1"})
        assert new_phase == "mutate"
        manifest = json.loads(manifest_path.read_text())
        assert manifest["phase"] == "mutate"

    def test_mutate_to_execute(self, manifest_path):
        advance_phase(manifest_path, {"directive": "test"})
        new_phase = advance_phase(manifest_path, {"candidate_id": "candidate-1"})
        assert new_phase == "execute"

    def test_full_cycle(self, manifest_path):
        """Walk through all 5 phases."""
        assert get_current_phase(manifest_path) == "prepare"
        advance_phase(manifest_path, {"directive": "improve p1"})
        assert get_current_phase(manifest_path) == "mutate"
        advance_phase(manifest_path, {"candidate_id": "candidate-1"})
        assert get_current_phase(manifest_path) == "execute"
        advance_phase(manifest_path, {"test_domain": "cli-todo"})
        assert get_current_phase(manifest_path) == "verify"
        advance_phase(manifest_path, {"evidence_path": "/tmp/evidence.yaml"})
        assert get_current_phase(manifest_path) == "decide"
        advance_phase(manifest_path, {"outcome": "promote"})
        assert get_current_phase(manifest_path) == "prepare"


class TestPrepareMutation:
    def test_identifies_weakest_category(self, manifest_path):
        m = json.loads(manifest_path.read_text())
        m["candidates"][0]["pass_rate"] = {
            "p1": "2/3", "p2": "3/3", "o1": "1/3", "o4": "3/3", "p4": "3/3",
        }
        manifest_path.write_text(json.dumps(m))

        result = prepare_mutation(manifest_path)
        assert result["target_category"] == "o1"
        assert "o1" in result["directive"].lower() or "correctness" in result["directive"].lower()

    def test_no_pass_rate_returns_general_directive(self, manifest_path):
        result = prepare_mutation(manifest_path)
        assert "directive" in result
        assert result["target_category"] is None

    def test_perfect_scores_returns_general(self, manifest_path):
        m = json.loads(manifest_path.read_text())
        m["candidates"][0]["pass_rate"] = {"p1": "3/3", "o1": "3/3"}
        manifest_path.write_text(json.dumps(m))
        result = prepare_mutation(manifest_path)
        assert "directive" in result


class TestDecideOutcome:
    def test_promote_when_improved(self, manifest_path):
        m = json.loads(manifest_path.read_text())
        m["candidates"][0]["pass_rate"] = {"overall": "4/9"}
        m["candidates"].append({
            "id": "candidate-1", "parent": "candidate-0",
            "status": "pending", "mutation": "test",
            "sha256": "abc", "pass_rate": {"overall": "6/9"},
            "created": "2026-03-30T00:00:00Z",
        })
        manifest_path.write_text(json.dumps(m))

        result = decide_outcome(manifest_path, "candidate-1")
        assert result == "promote"

    def test_reject_when_regressed(self, manifest_path):
        m = json.loads(manifest_path.read_text())
        m["candidates"][0]["pass_rate"] = {"overall": "6/9"}
        m["candidates"].append({
            "id": "candidate-1", "parent": "candidate-0",
            "status": "pending", "mutation": "test",
            "sha256": "abc", "pass_rate": {"overall": "4/9"},
            "created": "2026-03-30T00:00:00Z",
        })
        manifest_path.write_text(json.dumps(m))

        result = decide_outcome(manifest_path, "candidate-1")
        assert result == "reject"

    def test_tie_when_equal(self, manifest_path):
        m = json.loads(manifest_path.read_text())
        m["candidates"][0]["pass_rate"] = {"overall": "5/9"}
        m["candidates"].append({
            "id": "candidate-1", "parent": "candidate-0",
            "status": "pending", "mutation": "test",
            "sha256": "abc", "pass_rate": {"overall": "5/9"},
            "created": "2026-03-30T00:00:00Z",
        })
        manifest_path.write_text(json.dumps(m))

        result = decide_outcome(manifest_path, "candidate-1")
        assert result == "tie"


class TestCheckTierProgression:
    def test_no_progression_at_zero_passes(self, manifest_path, seed_tier_path):
        result = check_tier_progression(manifest_path, seed_tier_path)
        assert result["should_advance"] is False
        assert result["current_tier"] == "seed"

    def test_advances_after_three_consecutive(self, manifest_path, seed_tier_path):
        m = json.loads(manifest_path.read_text())
        m["consecutive_passes"] = 3
        m["candidates"][0]["pass_rate"] = {"overall": "9/9"}
        manifest_path.write_text(json.dumps(m))

        result = check_tier_progression(manifest_path, seed_tier_path)
        assert result["should_advance"] is True
        assert result["next_tier"] == "tier-2"

    def test_no_advance_if_not_perfect(self, manifest_path, seed_tier_path):
        m = json.loads(manifest_path.read_text())
        m["consecutive_passes"] = 3
        m["candidates"][0]["pass_rate"] = {"overall": "8/9"}
        manifest_path.write_text(json.dumps(m))

        result = check_tier_progression(manifest_path, seed_tier_path)
        assert result["should_advance"] is False
