"""Unit tests for TodoStore — covers feat-001-add-task, feat-002-list-tasks, feat-003-complete-task."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.todo import TodoStore


# ============================================================
# feat-001: Add Task
# ============================================================


class TestAddTaskDefaultPriority:
    """Test 1: Add task with default priority."""

    def test_add_task_returns_correct_fields(self, tmp_store: TodoStore) -> None:
        task = tmp_store.add_task(title="Buy groceries")

        assert task["id"] == 1
        assert task["title"] == "Buy groceries"
        assert task["priority"] == "medium"
        assert task["status"] == "pending"

    def test_add_task_created_at_is_recent(self, tmp_store: TodoStore) -> None:
        before = datetime.now(timezone.utc)
        task = tmp_store.add_task(title="Buy groceries")
        after = datetime.now(timezone.utc)

        created = datetime.fromisoformat(task["created_at"])
        assert before <= created <= after

    def test_add_task_persists_to_file(self, tmp_store: TodoStore) -> None:
        tmp_store.add_task(title="Buy groceries")

        assert tmp_store.file_path.exists()
        data = json.loads(tmp_store.file_path.read_text(encoding="utf-8"))
        assert len(data) == 1
        assert data[0]["title"] == "Buy groceries"


class TestAddTaskExplicitPriority:
    """Test 2 & 3: Add task with explicit priority."""

    def test_add_task_high_priority(self, tmp_store: TodoStore) -> None:
        task = tmp_store.add_task(title="Fix bug", priority="high")
        assert task["priority"] == "high"

    def test_add_task_low_priority(self, tmp_store: TodoStore) -> None:
        task = tmp_store.add_task(title="Someday task", priority="low")
        assert task["priority"] == "low"

    def test_add_task_medium_priority_explicit(self, tmp_store: TodoStore) -> None:
        task = tmp_store.add_task(title="Normal task", priority="medium")
        assert task["priority"] == "medium"


class TestAutoIncrementingIDs:
    """Test 4: Auto-incrementing IDs."""

    def test_sequential_ids(self, tmp_store: TodoStore) -> None:
        t1 = tmp_store.add_task(title="First")
        t2 = tmp_store.add_task(title="Second")
        t3 = tmp_store.add_task(title="Third")
        t4 = tmp_store.add_task(title="Fourth")

        assert t1["id"] == 1
        assert t2["id"] == 2
        assert t3["id"] == 3
        assert t4["id"] == 4

    def test_storage_contains_all_tasks(self, tmp_store: TodoStore) -> None:
        for i in range(4):
            tmp_store.add_task(title=f"Task {i+1}")

        data = json.loads(tmp_store.file_path.read_text(encoding="utf-8"))
        assert len(data) == 4


class TestIDIncrementingWithGaps:
    """Test 5: ID incrementing with gaps."""

    def test_new_id_is_max_plus_one(self, gapped_store: TodoStore) -> None:
        task = gapped_store.add_task(title="New task")
        assert task["id"] == 4  # max(1,3) + 1


class TestEmptyTitleRejection:
    """Test 6: Empty title rejection."""

    def test_empty_string_raises(self, tmp_store: TodoStore) -> None:
        with pytest.raises(ValueError, match="empty"):
            tmp_store.add_task(title="")

    def test_no_task_written_on_empty(self, tmp_store: TodoStore) -> None:
        with pytest.raises(ValueError):
            tmp_store.add_task(title="")
        assert not tmp_store.file_path.exists()


class TestWhitespaceTitleRejection:
    """Test 7: Whitespace-only title rejection."""

    def test_whitespace_raises(self, tmp_store: TodoStore) -> None:
        with pytest.raises(ValueError, match="empty"):
            tmp_store.add_task(title="   ")

    def test_no_task_written_on_whitespace(self, tmp_store: TodoStore) -> None:
        with pytest.raises(ValueError):
            tmp_store.add_task(title="   ")
        assert not tmp_store.file_path.exists()


class TestStorageFileAutoCreation:
    """Test 8: Storage file auto-creation."""

    def test_file_created_on_first_add(self, tmp_path: Path) -> None:
        file_path = tmp_path / "tasks.json"
        assert not file_path.exists()

        store = TodoStore(file_path=str(file_path))
        store.add_task(title="First task")

        assert file_path.exists()
        data = json.loads(file_path.read_text(encoding="utf-8"))
        assert len(data) == 1


class TestPersistenceFormat:
    """Test 9: Persistence format validation."""

    def test_json_format(self, tmp_store: TodoStore) -> None:
        tmp_store.add_task(title="Format test")
        content = tmp_store.file_path.read_text(encoding="utf-8")

        # Valid JSON
        data = json.loads(content)

        # Root is array of length 1
        assert isinstance(data, list)
        assert len(data) == 1

        # Task has required keys
        task = data[0]
        required_keys = {"id", "title", "priority", "status", "created_at"}
        assert set(task.keys()) == required_keys

        # JSON is indented (contains newlines)
        assert "\n" in content
        assert "  " in content


# ============================================================
# feat-002: List Tasks
# ============================================================


class TestListTasksAll:
    """List all tasks without filter."""

    def test_list_all_returns_everything(self, pre_populated_store: TodoStore) -> None:
        tasks = pre_populated_store.list_tasks()
        assert len(tasks) == 3

    def test_list_all_explicit(self, pre_populated_store: TodoStore) -> None:
        tasks = pre_populated_store.list_tasks(status_filter="all")
        assert len(tasks) == 3


class TestListTasksEmpty:
    """List tasks when store is empty."""

    def test_list_empty_store(self, tmp_store: TodoStore) -> None:
        tasks = tmp_store.list_tasks()
        assert tasks == []


class TestListTasksPendingFilter:
    """List tasks filtered by pending status."""

    def test_list_pending_only(self, tmp_path: Path) -> None:
        file_path = tmp_path / "tasks.json"
        tasks = [
            {"id": 1, "title": "Pending", "priority": "medium", "status": "pending", "created_at": "2026-01-01T00:00:00+00:00"},
            {"id": 2, "title": "Done", "priority": "medium", "status": "completed", "created_at": "2026-01-02T00:00:00+00:00"},
            {"id": 3, "title": "Also pending", "priority": "high", "status": "pending", "created_at": "2026-01-03T00:00:00+00:00"},
        ]
        file_path.write_text(json.dumps(tasks, indent=2) + "\n", encoding="utf-8")
        store = TodoStore(file_path=str(file_path))

        result = store.list_tasks(status_filter="pending")
        assert len(result) == 2
        assert all(t["status"] == "pending" for t in result)


class TestListTasksCompletedFilter:
    """List tasks filtered by completed status."""

    def test_list_completed_only(self, tmp_path: Path) -> None:
        file_path = tmp_path / "tasks.json"
        tasks = [
            {"id": 1, "title": "Pending", "priority": "medium", "status": "pending", "created_at": "2026-01-01T00:00:00+00:00"},
            {"id": 2, "title": "Done", "priority": "medium", "status": "completed", "created_at": "2026-01-02T00:00:00+00:00"},
        ]
        file_path.write_text(json.dumps(tasks, indent=2) + "\n", encoding="utf-8")
        store = TodoStore(file_path=str(file_path))

        result = store.list_tasks(status_filter="completed")
        assert len(result) == 1
        assert result[0]["title"] == "Done"


class TestListTasksInvalidFilter:
    """List tasks with invalid filter value."""

    def test_invalid_filter_raises(self, tmp_store: TodoStore) -> None:
        with pytest.raises(ValueError, match="Invalid status filter"):
            tmp_store.list_tasks(status_filter="archived")


class TestListTasksPreserveOrder:
    """List tasks preserves insertion order."""

    def test_order_preserved(self, pre_populated_store: TodoStore) -> None:
        tasks = pre_populated_store.list_tasks()
        ids = [t["id"] for t in tasks]
        assert ids == [1, 2, 3]


class TestListTasksShowsAllFields:
    """Each task in list contains all required fields."""

    def test_all_fields_present(self, pre_populated_store: TodoStore) -> None:
        tasks = pre_populated_store.list_tasks()
        required_keys = {"id", "title", "priority", "status", "created_at"}
        for task in tasks:
            assert set(task.keys()) == required_keys


# ============================================================
# feat-003: Complete Task
# ============================================================


class TestCompleteTaskSuccess:
    """Mark a pending task as completed."""

    def test_complete_task_changes_status(self, pre_populated_store: TodoStore) -> None:
        result = pre_populated_store.complete_task(task_id=1)
        assert result["status"] == "completed"
        assert result["id"] == 1

    def test_complete_task_persists(self, pre_populated_store: TodoStore) -> None:
        pre_populated_store.complete_task(task_id=2)
        tasks = pre_populated_store._load()
        task_2 = next(t for t in tasks if t["id"] == 2)
        assert task_2["status"] == "completed"


class TestCompleteTaskNotFound:
    """Attempt to complete a non-existent task."""

    def test_nonexistent_id_raises(self, pre_populated_store: TodoStore) -> None:
        with pytest.raises(ValueError, match="not found"):
            pre_populated_store.complete_task(task_id=999)

    def test_empty_store_raises(self, tmp_store: TodoStore) -> None:
        with pytest.raises(ValueError, match="not found"):
            tmp_store.complete_task(task_id=1)


class TestCompleteTaskAlreadyCompleted:
    """Attempt to complete a task that is already completed."""

    def test_already_completed_raises(self, tmp_path: Path) -> None:
        file_path = tmp_path / "tasks.json"
        tasks = [
            {"id": 1, "title": "Done task", "priority": "medium", "status": "completed", "created_at": "2026-01-01T00:00:00+00:00"},
        ]
        file_path.write_text(json.dumps(tasks, indent=2) + "\n", encoding="utf-8")
        store = TodoStore(file_path=str(file_path))

        with pytest.raises(ValueError, match="already completed"):
            store.complete_task(task_id=1)


class TestCompleteTaskOthersUnchanged:
    """Completing one task does not affect others."""

    def test_other_tasks_unchanged(self, pre_populated_store: TodoStore) -> None:
        pre_populated_store.complete_task(task_id=2)
        tasks = pre_populated_store._load()

        task_1 = next(t for t in tasks if t["id"] == 1)
        task_3 = next(t for t in tasks if t["id"] == 3)

        assert task_1["status"] == "pending"
        assert task_3["status"] == "pending"
