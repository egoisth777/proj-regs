# Tasks: feat-003-complete-task

> Produced by the Team Lead from the locked OpenSpec.
> Each task declares its file scope for coupling detection.

## Task Checklist

### Task 1: Implement TodoStore.complete_task method

#### File Scope
- `artifacts/src/todo.py`

**Assignee:** @Pool-E
**Worktree:** main
**Status:** complete

**Description:**
Add the `complete_task(task_id)` method to the TodoStore class.
- Finds the task by integer ID in the loaded task list.
- Validates the task exists (raises ValueError if not found).
- Validates the task is not already completed (raises ValueError if so).
- Changes the task's status from "pending" to "completed".
- Persists the updated task list to the JSON file.
- Returns the updated task dict.

---

### Task 2: Implement CLI complete subcommand

#### File Scope
- `artifacts/src/cli.py`

**Assignee:** @Pool-E
**Worktree:** main
**Status:** complete

**Description:**
Add the `complete` subcommand to the argparse parser.
- Required positional argument: `id` (int).
- On success: print `Task <id> completed: "<title>"` and exit 0.
- On ValueError (not found or already completed): print error to stderr and exit 1.

---

### Task 3: Write unit tests for complete_task

#### File Scope
- `artifacts/tests/test_todo.py`

**Assignee:** @Pool-E
**Worktree:** main
**Status:** complete

**Description:**
Write pytest unit tests covering: successful completion, persistence,
task not found, empty store, already completed, other tasks unchanged.

---

### Task 4: Write CLI integration tests for complete

#### File Scope
- `artifacts/tests/test_cli.py`

**Assignee:** @Pool-E
**Worktree:** main
**Status:** complete

**Description:**
Write pytest integration tests for the complete subcommand covering:
success output, not found error, already completed error, list verification
after completion.
