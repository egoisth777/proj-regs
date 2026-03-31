# Tasks: feat-002-list-tasks

> Produced by the Team Lead from the locked OpenSpec.
> Each task declares its file scope for coupling detection.

## Task Checklist

### Task 1: Implement TodoStore.list_tasks method

**File scope:**
- `artifacts/src/todo.py`

**Assignee:** @Pool-E
**Worktree:** main
**Status:** complete

**Description:**
Add the `list_tasks(status_filter="all")` method to the TodoStore class.
- Accepts a `status_filter` parameter with values: "all", "pending", "completed".
- Loads tasks from the JSON file.
- Returns all tasks if filter is "all", otherwise returns only tasks matching the status.
- Raises `ValueError` for invalid filter values.

---

### Task 2: Implement CLI list subcommand

**File scope:**
- `artifacts/src/cli.py`

**Assignee:** @Pool-E
**Worktree:** main
**Status:** complete

**Description:**
Add the `list` subcommand to the argparse parser.
- Optional `--status` argument with choices: all, pending, completed (default: all).
- Format output as `[<marker>] <id>. <title> (priority: <priority>)`.
- Print "No tasks found." when list is empty.
- Exit 0 on success.

---

### Task 3: Write unit tests for list_tasks

**File scope:**
- `artifacts/tests/test_todo.py`

**Assignee:** @Pool-E
**Worktree:** main
**Status:** complete

**Description:**
Write pytest unit tests covering: list all, list empty, list pending filter,
list completed filter, invalid filter, insertion order, all fields present.

---

### Task 4: Write CLI integration tests for list

**File scope:**
- `artifacts/tests/test_cli.py`

**Assignee:** @Pool-E
**Worktree:** main
**Status:** complete

**Description:**
Write pytest integration tests for the list subcommand covering: empty list,
all tasks, pending filter, completed filter, invalid status, output format.
