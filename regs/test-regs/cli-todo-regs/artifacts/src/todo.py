"""Core logic for the CLI todo application.

Provides the Task data model and TodoStore class for managing todo items
persisted in a local JSON file.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class Task:
    """Represents a single todo item."""

    id: int
    title: str
    priority: str = "medium"
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TodoStore:
    """Manages todo tasks persisted in a JSON file.

    The storage file path is determined by:
    1. The explicit `file_path` argument if provided.
    2. The `TODO_FILE` environment variable if set.
    3. Defaults to `tasks.json` in the current working directory.
    """

    def __init__(self, file_path: Optional[str] = None) -> None:
        if file_path is not None:
            self.file_path = Path(file_path)
        else:
            env_path = os.environ.get("TODO_FILE")
            if env_path:
                self.file_path = Path(env_path)
            else:
                self.file_path = Path("tasks.json")

    def _load(self) -> list[dict]:
        """Load tasks from the JSON file.

        Returns an empty list if the file does not exist or is empty.
        """
        if not self.file_path.exists():
            return []
        content = self.file_path.read_text(encoding="utf-8").strip()
        if not content:
            return []
        return json.loads(content)

    def _save(self, tasks: list[dict]) -> None:
        """Write the full task list to the JSON file.

        Creates parent directories if they do not exist.
        Uses 2-space indentation for human readability.
        """
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.write_text(
            json.dumps(tasks, indent=2) + "\n",
            encoding="utf-8",
        )

    def add_task(self, title: str, priority: str = "medium") -> dict:
        """Add a new task.

        Args:
            title: The task title. Must not be empty or whitespace-only.
            priority: One of 'low', 'medium', 'high'. Defaults to 'medium'.

        Returns:
            A dict representation of the newly created task.

        Raises:
            ValueError: If the title is empty or whitespace-only.
            ValueError: If the priority is not one of the allowed values.
        """
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty.")

        allowed_priorities = ("low", "medium", "high")
        if priority not in allowed_priorities:
            raise ValueError(
                f"Invalid priority '{priority}'. Must be one of: {', '.join(allowed_priorities)}"
            )

        tasks = self._load()

        # Compute next ID: max existing ID + 1, or 1 if no tasks exist
        if tasks:
            next_id = max(t["id"] for t in tasks) + 1
        else:
            next_id = 1

        new_task = Task(id=next_id, title=title, priority=priority)
        task_dict = asdict(new_task)
        tasks.append(task_dict)
        self._save(tasks)

        return task_dict

    def list_tasks(self, status_filter: str = "all") -> list[dict]:
        """List tasks, optionally filtered by status.

        Args:
            status_filter: One of 'all', 'pending', 'completed'. Defaults to 'all'.

        Returns:
            A list of task dicts matching the filter.

        Raises:
            ValueError: If the status_filter is not valid.
        """
        allowed_filters = ("all", "pending", "completed")
        if status_filter not in allowed_filters:
            raise ValueError(
                f"Invalid status filter '{status_filter}'. Must be one of: {', '.join(allowed_filters)}"
            )

        tasks = self._load()

        if status_filter == "all":
            return tasks
        return [t for t in tasks if t["status"] == status_filter]

    def complete_task(self, task_id: int) -> dict:
        """Mark a task as completed by its ID.

        Args:
            task_id: The integer ID of the task to complete.

        Returns:
            A dict representation of the updated task.

        Raises:
            ValueError: If no task with the given ID exists.
            ValueError: If the task is already completed.
        """
        tasks = self._load()

        target = None
        for task in tasks:
            if task["id"] == task_id:
                target = task
                break

        if target is None:
            raise ValueError(f"Task with ID {task_id} not found.")

        if target["status"] == "completed":
            raise ValueError(f"Task {task_id} is already completed.")

        target["status"] = "completed"
        self._save(tasks)

        return target
