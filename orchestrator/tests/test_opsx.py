"""Tests for opsx.py — CLI entry point for evolution loop operations."""

import json
import re
import pytest
from pathlib import Path

from opsx import (
    cmd_status,
    cmd_tier,
    cmd_new_feature,
    _next_feature_number,
)


class TestCmdStatus:
    def test_returns_manifest_summary(self, manifest_path):
        result = cmd_status(manifest_path)
        assert "candidate-0" in result
        assert "prepare" in result
        assert "seed" in result


class TestCmdTier:
    def test_returns_tier_info(self, manifest_path):
        result = cmd_tier(manifest_path)
        assert "seed" in result
        assert "consecutive" in result.lower()


class TestNextFeatureNumber:
    def test_empty_changes_returns_001(self, tmp_path):
        changes = tmp_path / "changes"
        changes.mkdir()
        assert _next_feature_number(changes) == 1

    def test_increments_from_existing(self, tmp_path):
        changes = tmp_path / "changes"
        changes.mkdir()
        (changes / "feat-001-add-task").mkdir()
        (changes / "feat-002-list-tasks").mkdir()
        assert _next_feature_number(changes) == 3

    def test_handles_gaps(self, tmp_path):
        changes = tmp_path / "changes"
        changes.mkdir()
        (changes / "feat-001-add-task").mkdir()
        (changes / "feat-005-delete").mkdir()
        assert _next_feature_number(changes) == 6


class TestCmdNewFeature:
    def test_creates_feature_folder(self, tmp_path):
        changes_dir = tmp_path / "changes"
        changes_dir.mkdir()
        template_dir = tmp_path / "template"
        template_dir.mkdir()
        (template_dir / "proposal.md").write_text("# Proposal\n")
        (template_dir / "behavior_spec.md").write_text("# Behavior Spec\n")
        (template_dir / "test_spec.md").write_text("# Test Spec\n")
        (template_dir / "tasks.md").write_text("# Tasks\n")
        (template_dir / "status.md").write_text("# Status\n")

        result = cmd_new_feature(
            "add-task",
            changes_dir=changes_dir,
            template_dir=template_dir,
        )

        feat_dir = changes_dir / "feat-001-add-task"
        assert feat_dir.exists()
        assert (feat_dir / "proposal.md").exists()
        assert (feat_dir / "behavior_spec.md").exists()
        assert (feat_dir / "test_spec.md").exists()
        assert (feat_dir / "tasks.md").exists()
        assert (feat_dir / "status.md").exists()
        assert "feat-001-add-task" in result

    def test_auto_increments(self, tmp_path):
        changes_dir = tmp_path / "changes"
        changes_dir.mkdir()
        (changes_dir / "feat-001-add-task").mkdir()
        template_dir = tmp_path / "template"
        template_dir.mkdir()
        (template_dir / "proposal.md").write_text("# Proposal\n")

        result = cmd_new_feature(
            "list-tasks",
            changes_dir=changes_dir,
            template_dir=template_dir,
        )
        assert "feat-002-list-tasks" in result
