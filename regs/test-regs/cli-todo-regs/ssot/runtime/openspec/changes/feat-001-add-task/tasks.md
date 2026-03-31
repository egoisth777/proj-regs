# Tasks: feat-001-add-task

> Produced by the Team Lead from the locked OpenSpec.
> Each task declares its file scope for coupling detection.

## Task Checklist

### Task 1: Implement Task data model and TodoStore.add_task

#### File Scope
- `artifacts/src/__init__.py`
- `artifacts/src/todo.py`

**Assignee:** @Pool-E
**Worktree:** main
**Status:** complete

**Description:**
Create the Task dataclass with fields: id (int), title (str), priority (str),
status (str), created_at (str). Implement the TodoStore class with:
- `__init__(self, file_path)` — accepts storage file path, defaults via TODO_FILE env var or "tasks.json"
- `_load()` — reads JSON file, returns list of task dicts; returns [] if file missing
- `_save(tasks)` — writes list of task dicts to JSON with 2-space indent
- `add_task(title, priority="medium")` — validates title, creates new task with auto-incrementing ID, persists, returns task dict

---

### Task 2: Implement CLI add subcommand

#### File Scope
- `artifacts/src/cli.py`

**Assignee:** @Pool-E
**Worktree:** main
**Status:** complete

**Description:**
Create the CLI entry point using argparse with an `add` subcommand.
- Positional argument: `title` (str)
- Optional argument: `--priority` with choices=[low, medium, high], default=medium
- On success: print confirmation and exit 0
- On empty title: print error to stderr and exit 1

---

### Task 3: Write unit tests for TodoStore

#### File Scope
- `artifacts/tests/__init__.py`
- `artifacts/tests/conftest.py`
- `artifacts/tests/test_todo.py`

**Assignee:** @Pool-E
**Worktree:** main
**Status:** complete

**Description:**
Write pytest unit tests covering: add with default priority, add with explicit
priority, auto-incrementing IDs, ID gaps, empty title rejection, whitespace
title rejection, file auto-creation, persistence format.

---

### Task 4: Write CLI integration tests

#### File Scope
- `artifacts/tests/test_cli.py`

**Assignee:** @Pool-E
**Worktree:** main
**Status:** complete

**Description:**
Write pytest integration tests that invoke the CLI as a subprocess and verify
stdout, stderr, exit codes, and file contents for add operations.

---

### Task 5: Create pyproject.toml

#### File Scope
- `artifacts/pyproject.toml`

**Assignee:** @Pool-E
**Worktree:** main
**Status:** complete

**Description:**
Create project configuration with pytest settings, project metadata, and
any needed tool configuration.
