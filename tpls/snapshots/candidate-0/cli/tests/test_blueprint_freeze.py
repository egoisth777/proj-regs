"""Tests for blueprint_freeze hook."""

import json
from pathlib import Path
from unittest.mock import patch

from hooks.blueprint_freeze import is_sprint_active, check_blueprint_freeze


class TestIsSprintActive:
    def test_active_sprint_with_current_feature(self, tmp_path):
        sprint_file = tmp_path / "active_sprint.md"
        sprint_file.write_text("Current Feature: auth\nPhase: execution\n")
        assert is_sprint_active(sprint_file) is True

    def test_active_sprint_with_phase_only(self, tmp_path):
        sprint_file = tmp_path / "active_sprint.md"
        sprint_file.write_text("Phase: design\n")
        assert is_sprint_active(sprint_file) is True

    def test_no_active_sprint(self, tmp_path):
        sprint_file = tmp_path / "active_sprint.md"
        sprint_file.write_text("No active sprint.\n")
        assert is_sprint_active(sprint_file) is False

    def test_empty_file(self, tmp_path):
        sprint_file = tmp_path / "active_sprint.md"
        sprint_file.write_text("")
        assert is_sprint_active(sprint_file) is False

    def test_missing_file(self, tmp_path):
        sprint_file = tmp_path / "active_sprint.md"
        assert is_sprint_active(sprint_file) is False


class TestCheckBlueprintFreeze:
    def test_blocks_blueprint_write_during_sprint(self, tmp_path):
        sprint_file = tmp_path / "active_sprint.md"
        sprint_file.write_text("Current Feature: auth\nPhase: execution\n")
        result = check_blueprint_freeze("blueprint/design/arch.md", sprint_file)
        assert result["decision"] == "block"
        assert "reason" in result

    def test_allows_runtime_write_during_sprint(self, tmp_path):
        sprint_file = tmp_path / "active_sprint.md"
        sprint_file.write_text("Current Feature: auth\nPhase: execution\n")
        result = check_blueprint_freeze("runtime/openspec/changes/auth/status.md", sprint_file)
        assert result["decision"] == "allow"

    def test_allows_blueprint_write_when_no_sprint(self, tmp_path):
        sprint_file = tmp_path / "active_sprint.md"
        sprint_file.write_text("No active sprint.\n")
        result = check_blueprint_freeze("blueprint/design/arch.md", sprint_file)
        assert result["decision"] == "allow"

    def test_allows_non_blueprint_writes_always(self, tmp_path):
        sprint_file = tmp_path / "active_sprint.md"
        sprint_file.write_text("Current Feature: auth\nPhase: execution\n")
        result = check_blueprint_freeze("src/app.py", sprint_file)
        assert result["decision"] == "allow"

    def test_allows_blueprint_write_when_file_missing(self, tmp_path):
        sprint_file = tmp_path / "active_sprint.md"
        result = check_blueprint_freeze("blueprint/design/arch.md", sprint_file)
        assert result["decision"] == "allow"
