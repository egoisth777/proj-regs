# Behavior Specification: List Tasks

> Produced by the Behavior Spec Writer from the approved proposal.
> Each behavior uses Given/When/Then format and must be observable and testable.

## Behaviors

### Behavior 1: List all tasks (default)

**Given** the storage file contains three tasks (two pending, one completed)
**When** the user runs `cli-todo list`
**Then** all three tasks are printed to stdout, each on its own line. Pending tasks show `[ ]` and completed tasks show `[x]`. The CLI exits with code 0.

---

### Behavior 2: List all tasks with explicit flag

**Given** the storage file contains tasks
**When** the user runs `cli-todo list --status all`
**Then** the output is identical to running `cli-todo list` without the flag. All tasks are shown.

---

### Behavior 3: List pending tasks only

**Given** the storage file contains a mix of pending and completed tasks
**When** the user runs `cli-todo list --status pending`
**Then** only tasks with status "pending" are shown. Completed tasks are excluded. Each line shows the `[ ]` marker.

---

### Behavior 4: List completed tasks only

**Given** the storage file contains a mix of pending and completed tasks
**When** the user runs `cli-todo list --status completed`
**Then** only tasks with status "completed" are shown. Pending tasks are excluded. Each line shows the `[x]` marker.

---

### Behavior 5: Empty list output

**Given** the storage file does not exist or contains no tasks
**When** the user runs `cli-todo list`
**Then** the CLI prints `No tasks found.` to stdout and exits with code 0.

---

### Behavior 6: Empty filtered list

**Given** the storage file contains only pending tasks (no completed tasks)
**When** the user runs `cli-todo list --status completed`
**Then** the CLI prints `No tasks found.` to stdout and exits with code 0.

---

### Behavior 7: Output format per line

**Given** a task with id=3, title="Buy milk", priority="high", status="pending"
**When** it appears in a list output
**Then** the line reads: `[ ] 3. Buy milk (priority: high)`

---

### Behavior 8: Output format for completed task

**Given** a task with id=1, title="File taxes", priority="medium", status="completed"
**When** it appears in a list output
**Then** the line reads: `[x] 1. File taxes (priority: medium)`

---

### Behavior 9: Invalid status filter

**Given** any state of the storage file
**When** the user runs `cli-todo list --status archived`
**Then** argparse rejects the invalid choice, prints an error to stderr listing valid choices, and exits with code 2.

---

### Behavior 10: Insertion order preserved

**Given** tasks were added in order: id=1 "Alpha", id=2 "Beta", id=3 "Gamma"
**When** the user runs `cli-todo list`
**Then** the tasks are displayed in insertion order: Alpha first, Beta second, Gamma third.

---

### Behavior 11: All required fields in each line

**Given** tasks exist in the storage file
**When** the user runs `cli-todo list`
**Then** each output line includes: a status marker (`[ ]` or `[x]`), the numeric task ID followed by a period, the task title, and the priority in parentheses.

---

### Behavior 12: Environment variable respected

**Given** `TODO_FILE` is set to a custom path containing tasks
**When** the user runs `cli-todo list`
**Then** the tasks from the custom file are listed, not from the default `tasks.json`.
