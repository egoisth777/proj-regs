import json
from pathlib import Path, PurePath
from unittest.mock import patch

from hooks.path_validator import validate_path, get_allowed_paths, parse_worker_file_scope


class TestParseWorkerFileScope:
    def test_parses_task_1_scope(self):
        tasks_md = """# Tasks: Auth\n\n## Task Checklist\n\n### Task 1: Add auth handler\n\n**File scope:**\n- `src/auth/handler.py`\n- `src/auth/utils.py`\n\n**Assignee:** @Worker\n\n### Task 2: Add auth tests\n\n**File scope:**\n- `tests/test_auth.py`\n\n**Assignee:** @Worker\n"""
        result = parse_worker_file_scope(tasks_md, worker_instance=1)
        assert result == ["src/auth/handler.py", "src/auth/utils.py"]

    def test_parses_task_2_scope(self):
        tasks_md = "### Task 1: First\n**File scope:**\n- `src/a.py`\n\n### Task 2: Second\n**File scope:**\n- `src/b.py`\n- `src/c.py`\n"
        result = parse_worker_file_scope(tasks_md, worker_instance=2)
        assert result == ["src/b.py", "src/c.py"]

    def test_returns_empty_for_out_of_range(self):
        tasks_md = "### Task 1: Only one\n**File scope:**\n- `src/a.py`\n"
        result = parse_worker_file_scope(tasks_md, worker_instance=5)
        assert result == []

    def test_returns_empty_for_empty_input(self):
        result = parse_worker_file_scope("", worker_instance=1)
        assert result == []


class TestGetAllowedPaths:
    def test_orchestrator_blocked(self):
        paths, _ = get_allowed_paths("orchestrator", feature=None, registry_path=None)
        assert paths == []

    def test_auditor_blocked(self):
        paths, _ = get_allowed_paths("auditor", feature=None, registry_path=None)
        assert paths == []

    def test_regression_runner_blocked(self):
        paths, _ = get_allowed_paths("regression-runner", feature=None, registry_path=None)
        assert paths == []

    def test_sonders_returns_absolute_registry_paths(self):
        paths, is_abs = get_allowed_paths("sonders", feature=None, registry_path="/reg")
        assert is_abs is True
        assert any("blueprint/design" in p for p in paths)

    def test_sdet_unit_returns_relative_project_paths(self):
        paths, is_abs = get_allowed_paths("sdet-unit", feature=None, registry_path=None)
        assert is_abs is False
        assert "tests/**/*" in paths
        assert "test/**/*" in paths

    def test_behavior_spec_writer_scoped(self, tmp_path):
        registry = tmp_path / "reg"
        changes = registry / "runtime" / "openspec" / "changes" / "2026-03-25-auth"
        changes.mkdir(parents=True)
        paths, is_abs = get_allowed_paths("behavior-spec-writer", feature="auth", registry_path=str(registry))
        assert is_abs is True
        assert any("behavior_spec.md" in p for p in paths)


class TestValidatePath:
    def test_worker_allowed_in_scope(self, tmp_path):
        registry = tmp_path / "registry"
        changes = registry / "runtime" / "openspec" / "changes" / "2026-03-25-auth"
        changes.mkdir(parents=True)
        (changes / "tasks.md").write_text("### Task 1: Handler\n**File scope:**\n- `src/handler.py`\n")
        result = validate_path(
            role="worker", feature="auth", file_path="src/handler.py",
            registry_path=str(registry), worker_instance=1, project_root=str(tmp_path / "project")
        )
        assert result["decision"] == "allow"

    def test_worker_blocked_outside_scope(self, tmp_path):
        registry = tmp_path / "registry"
        changes = registry / "runtime" / "openspec" / "changes" / "2026-03-25-auth"
        changes.mkdir(parents=True)
        (changes / "tasks.md").write_text("### Task 1: Handler\n**File scope:**\n- `src/handler.py`\n")
        result = validate_path(
            role="worker", feature="auth", file_path="src/other.py",
            registry_path=str(registry), worker_instance=1, project_root=str(tmp_path / "project")
        )
        assert result["decision"] == "block"

    def test_worker_1_blocked_from_task_2(self, tmp_path):
        registry = tmp_path / "registry"
        changes = registry / "runtime" / "openspec" / "changes" / "2026-03-25-auth"
        changes.mkdir(parents=True)
        (changes / "tasks.md").write_text("### Task 1: A\n**File scope:**\n- `src/a.py`\n\n### Task 2: B\n**File scope:**\n- `src/b.py`\n")
        result = validate_path(
            role="worker", feature="auth", file_path="src/b.py",
            registry_path=str(registry), worker_instance=1, project_root=str(tmp_path / "project")
        )
        assert result["decision"] == "block"

    def test_worker_blocked_no_tasks(self):
        result = validate_path(
            role="worker", feature="auth", file_path="src/foo.py",
            registry_path="/nonexistent", worker_instance=1, project_root="/project"
        )
        assert result["decision"] == "block"

    def test_orchestrator_always_blocked(self):
        result = validate_path(
            role="orchestrator", feature=None, file_path="anything.py",
            registry_path=None, worker_instance=None, project_root="/project"
        )
        assert result["decision"] == "block"

    def test_sonders_allowed_blueprint_design(self, tmp_path):
        registry = tmp_path / "reg"
        (registry / "blueprint" / "design").mkdir(parents=True)
        result = validate_path(
            role="sonders", feature=None, file_path="blueprint/design/arch.md",
            registry_path=str(registry), worker_instance=None, project_root="/project",
            file_path_abs=str(registry / "blueprint" / "design" / "arch.md"),
        )
        assert result["decision"] == "allow"

    def test_sonders_blocked_src(self, tmp_path):
        registry = tmp_path / "reg"
        registry.mkdir()
        result = validate_path(
            role="sonders", feature=None, file_path="src/app.py",
            registry_path=str(registry), worker_instance=None, project_root="/project",
            file_path_abs="/project/src/app.py",
        )
        assert result["decision"] == "block"

    def test_sdet_allowed_tests(self):
        result = validate_path(
            role="sdet-unit", feature=None, file_path="tests/test_auth.py",
            registry_path=None, worker_instance=None, project_root="/project"
        )
        assert result["decision"] == "allow"

    def test_sdet_allowed_nested_tests(self):
        result = validate_path(
            role="sdet-unit", feature=None, file_path="tests/unit/deep/test_auth.py",
            registry_path=None, worker_instance=None, project_root="/project"
        )
        assert result["decision"] == "allow"

    def test_sdet_blocked_src(self):
        result = validate_path(
            role="sdet-unit", feature=None, file_path="src/auth.py",
            registry_path=None, worker_instance=None, project_root="/project"
        )
        assert result["decision"] == "block"

    def test_degraded_mode_no_config(self):
        result = validate_path(
            role=None, feature=None, file_path="anything.py",
            registry_path=None, worker_instance=None, project_root=None
        )
        assert result["decision"] == "allow"
