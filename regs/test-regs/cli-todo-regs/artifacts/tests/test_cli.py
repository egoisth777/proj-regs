"""CLI integration tests — covers add, list, and complete subcommands."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


ARTIFACTS_DIR = Path(__file__).resolve().parent.parent


def run_cli(*args: str, env_overrides: dict | None = None) -> subprocess.CompletedProcess:
    """Run the CLI as a subprocess and return the result."""
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-m", "src.cli", *args],
        capture_output=True,
        text=True,
        cwd=str(ARTIFACTS_DIR),
        env=env,
    )


# ============================================================
# feat-001: CLI Add Task
# ============================================================


class TestCLIAddDefaultPriority:
    """Test 10: CLI add with default priority."""

    def test_add_default_priority(self, tmp_path: Path) -> None:
        todo_file = tmp_path / "tasks.json"
        result = run_cli("add", "Buy groceries", env_overrides={"TODO_FILE": str(todo_file)})

        assert result.returncode == 0
        assert 'Task 1 added: "Buy groceries" [priority: medium]' in result.stdout

        data = json.loads(todo_file.read_text(encoding="utf-8"))
        assert len(data) == 1
        assert data[0]["title"] == "Buy groceries"
        assert data[0]["priority"] == "medium"


class TestCLIAddExplicitPriority:
    """Test 11: CLI add with explicit priority."""

    def test_add_high_priority(self, tmp_path: Path) -> None:
        todo_file = tmp_path / "tasks.json"
        result = run_cli(
            "add", "Urgent", "--priority", "high",
            env_overrides={"TODO_FILE": str(todo_file)},
        )

        assert result.returncode == 0
        assert 'Task 1 added: "Urgent" [priority: high]' in result.stdout


class TestCLIAddEmptyTitle:
    """Test 12: CLI add with empty title."""

    def test_add_empty_title(self, tmp_path: Path) -> None:
        todo_file = tmp_path / "tasks.json"
        result = run_cli("add", "", env_overrides={"TODO_FILE": str(todo_file)})

        assert result.returncode == 1
        assert "empty" in result.stderr.lower() or "Error" in result.stderr
        assert not todo_file.exists()


class TestCLIAddInvalidPriority:
    """Test 13: CLI add with invalid priority."""

    def test_add_invalid_priority(self, tmp_path: Path) -> None:
        todo_file = tmp_path / "tasks.json"
        result = run_cli(
            "add", "Task", "--priority", "urgent",
            env_overrides={"TODO_FILE": str(todo_file)},
        )

        assert result.returncode == 2
        assert "invalid choice" in result.stderr.lower()


class TestCLIAddEnvVarPath:
    """Test 14: Environment variable file path override."""

    def test_env_var_path(self, tmp_path: Path) -> None:
        custom_file = tmp_path / "custom.json"
        result = run_cli(
            "add", "Custom path task",
            env_overrides={"TODO_FILE": str(custom_file)},
        )

        assert result.returncode == 0
        assert custom_file.exists()

        data = json.loads(custom_file.read_text(encoding="utf-8"))
        assert data[0]["title"] == "Custom path task"


# ============================================================
# feat-002: CLI List Tasks
# ============================================================


class TestCLIListEmpty:
    """CLI list when no tasks exist."""

    def test_list_empty(self, tmp_path: Path) -> None:
        todo_file = tmp_path / "tasks.json"
        result = run_cli("list", env_overrides={"TODO_FILE": str(todo_file)})

        assert result.returncode == 0
        assert "No tasks found" in result.stdout


class TestCLIListAllTasks:
    """CLI list shows all tasks."""

    def test_list_all(self, tmp_path: Path) -> None:
        todo_file = tmp_path / "tasks.json"
        env = {"TODO_FILE": str(todo_file)}

        # Add two tasks
        run_cli("add", "Task one", env_overrides=env)
        run_cli("add", "Task two", "--priority", "high", env_overrides=env)

        result = run_cli("list", env_overrides=env)

        assert result.returncode == 0
        assert "Task one" in result.stdout
        assert "Task two" in result.stdout


class TestCLIListPendingFilter:
    """CLI list with --status pending filter."""

    def test_list_pending(self, tmp_path: Path) -> None:
        todo_file = tmp_path / "tasks.json"
        env = {"TODO_FILE": str(todo_file)}

        run_cli("add", "Pending task", env_overrides=env)
        run_cli("add", "To complete", env_overrides=env)
        run_cli("complete", "2", env_overrides=env)

        result = run_cli("list", "--status", "pending", env_overrides=env)

        assert result.returncode == 0
        assert "Pending task" in result.stdout
        assert "To complete" not in result.stdout


class TestCLIListCompletedFilter:
    """CLI list with --status completed filter."""

    def test_list_completed(self, tmp_path: Path) -> None:
        todo_file = tmp_path / "tasks.json"
        env = {"TODO_FILE": str(todo_file)}

        run_cli("add", "Pending task", env_overrides=env)
        run_cli("add", "Done task", env_overrides=env)
        run_cli("complete", "2", env_overrides=env)

        result = run_cli("list", "--status", "completed", env_overrides=env)

        assert result.returncode == 0
        assert "Done task" in result.stdout
        assert "Pending task" not in result.stdout


class TestCLIListInvalidStatus:
    """CLI list with invalid --status value."""

    def test_list_invalid_status(self, tmp_path: Path) -> None:
        todo_file = tmp_path / "tasks.json"
        result = run_cli(
            "list", "--status", "archived",
            env_overrides={"TODO_FILE": str(todo_file)},
        )

        assert result.returncode == 2
        assert "invalid choice" in result.stderr.lower()


class TestCLIListOutputFormat:
    """CLI list output format includes status marker and fields."""

    def test_output_format(self, tmp_path: Path) -> None:
        todo_file = tmp_path / "tasks.json"
        env = {"TODO_FILE": str(todo_file)}

        run_cli("add", "My task", "--priority", "high", env_overrides=env)
        result = run_cli("list", env_overrides=env)

        assert result.returncode == 0
        # Should contain checkbox marker, ID, title, priority
        assert "[ ]" in result.stdout
        assert "1." in result.stdout
        assert "My task" in result.stdout
        assert "high" in result.stdout


# ============================================================
# feat-003: CLI Complete Task
# ============================================================


class TestCLICompleteSuccess:
    """CLI complete marks a task as done."""

    def test_complete_task(self, tmp_path: Path) -> None:
        todo_file = tmp_path / "tasks.json"
        env = {"TODO_FILE": str(todo_file)}

        run_cli("add", "Finish report", env_overrides=env)
        result = run_cli("complete", "1", env_overrides=env)

        assert result.returncode == 0
        assert 'Task 1 completed: "Finish report"' in result.stdout

        data = json.loads(todo_file.read_text(encoding="utf-8"))
        assert data[0]["status"] == "completed"


class TestCLICompleteNotFound:
    """CLI complete with non-existent ID."""

    def test_complete_nonexistent(self, tmp_path: Path) -> None:
        todo_file = tmp_path / "tasks.json"
        env = {"TODO_FILE": str(todo_file)}

        run_cli("add", "Only task", env_overrides=env)
        result = run_cli("complete", "999", env_overrides=env)

        assert result.returncode == 1
        assert "not found" in result.stderr.lower()


class TestCLICompleteAlreadyCompleted:
    """CLI complete on an already-completed task."""

    def test_complete_already_done(self, tmp_path: Path) -> None:
        todo_file = tmp_path / "tasks.json"
        env = {"TODO_FILE": str(todo_file)}

        run_cli("add", "Task", env_overrides=env)
        run_cli("complete", "1", env_overrides=env)
        result = run_cli("complete", "1", env_overrides=env)

        assert result.returncode == 1
        assert "already completed" in result.stderr.lower()


class TestCLICompleteListVerification:
    """After completing, list --status completed shows the task."""

    def test_completed_shows_in_list(self, tmp_path: Path) -> None:
        todo_file = tmp_path / "tasks.json"
        env = {"TODO_FILE": str(todo_file)}

        run_cli("add", "Task A", env_overrides=env)
        run_cli("add", "Task B", env_overrides=env)
        run_cli("complete", "1", env_overrides=env)

        result = run_cli("list", "--status", "completed", env_overrides=env)
        assert "Task A" in result.stdout
        assert "Task B" not in result.stdout

        # Completed tasks should show [x] marker
        result_all = run_cli("list", env_overrides=env)
        assert "[x]" in result_all.stdout
