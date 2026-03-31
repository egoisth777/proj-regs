"""Shared fixtures for cli-todo tests."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from src.todo import TodoStore


@pytest.fixture
def tmp_store(tmp_path: Path) -> TodoStore:
    """Provide a TodoStore backed by a temporary file."""
    file_path = tmp_path / "tasks.json"
    return TodoStore(file_path=str(file_path))


@pytest.fixture
def tmp_todo_file(tmp_path: Path):
    """Provide a temporary file path for CLI integration tests.

    Sets the TODO_FILE environment variable and restores it after the test.
    """
    file_path = tmp_path / "tasks.json"
    old_env = os.environ.get("TODO_FILE")
    os.environ["TODO_FILE"] = str(file_path)
    yield file_path
    if old_env is None:
        os.environ.pop("TODO_FILE", None)
    else:
        os.environ["TODO_FILE"] = old_env


@pytest.fixture
def pre_populated_store(tmp_path: Path) -> TodoStore:
    """Provide a TodoStore with three pre-existing tasks."""
    file_path = tmp_path / "tasks.json"
    tasks = [
        {
            "id": 1,
            "title": "Task one",
            "priority": "medium",
            "status": "pending",
            "created_at": "2026-01-01T00:00:00+00:00",
        },
        {
            "id": 2,
            "title": "Task two",
            "priority": "high",
            "status": "pending",
            "created_at": "2026-01-02T00:00:00+00:00",
        },
        {
            "id": 3,
            "title": "Task three",
            "priority": "low",
            "status": "pending",
            "created_at": "2026-01-03T00:00:00+00:00",
        },
    ]
    file_path.write_text(json.dumps(tasks, indent=2) + "\n", encoding="utf-8")
    return TodoStore(file_path=str(file_path))


@pytest.fixture
def gapped_store(tmp_path: Path) -> TodoStore:
    """Provide a TodoStore with a gap in IDs (1 and 3, missing 2)."""
    file_path = tmp_path / "tasks.json"
    tasks = [
        {
            "id": 1,
            "title": "First",
            "priority": "medium",
            "status": "pending",
            "created_at": "2026-01-01T00:00:00+00:00",
        },
        {
            "id": 3,
            "title": "Third",
            "priority": "medium",
            "status": "pending",
            "created_at": "2026-01-03T00:00:00+00:00",
        },
    ]
    file_path.write_text(json.dumps(tasks, indent=2) + "\n", encoding="utf-8")
    return TodoStore(file_path=str(file_path))
