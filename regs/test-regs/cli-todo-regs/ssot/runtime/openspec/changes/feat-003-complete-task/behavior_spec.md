# Behavior Specification: Complete Task

> Produced by the Behavior Spec Writer from the approved proposal.
> Each behavior uses Given/When/Then format and must be observable and testable.

## Behaviors

### Behavior 1: Complete a pending task

**Given** the storage file contains a task with id=1, status="pending", title="Buy groceries"
**When** the user runs `cli-todo complete 1`
**Then** the task's status is changed to "completed" in the storage file. The CLI prints `Task 1 completed: "Buy groceries"` and exits with code 0.

---

### Behavior 2: Task not found

**Given** the storage file contains tasks with IDs 1, 2, and 3
**When** the user runs `cli-todo complete 999`
**Then** the CLI prints an error message to stderr indicating that task 999 was not found. The CLI exits with code 1. No tasks are modified.

---

### Behavior 3: Empty store — task not found

**Given** the storage file does not exist or contains no tasks
**When** the user runs `cli-todo complete 1`
**Then** the CLI prints an error message to stderr indicating that task 1 was not found. The CLI exits with code 1.

---

### Behavior 4: Already completed task

**Given** the storage file contains a task with id=1, status="completed"
**When** the user runs `cli-todo complete 1`
**Then** the CLI prints an error message to stderr indicating that task 1 is already completed. The CLI exits with code 1. The task's status remains "completed".

---

### Behavior 5: Other tasks unchanged

**Given** the storage file contains tasks with IDs 1, 2, and 3, all pending
**When** the user runs `cli-todo complete 2`
**Then** task 2's status changes to "completed". Tasks 1 and 3 remain with status "pending", and all their other fields are unchanged.

---

### Behavior 6: Persistence verification

**Given** the storage file contains a pending task with id=1
**When** the user runs `cli-todo complete 1`
**Then** the change is written to the JSON file immediately. A subsequent `cli-todo list --status completed` will show task 1.

---

### Behavior 7: CLI output format on success

**Given** a pending task with id=5, title="Deploy release"
**When** the user runs `cli-todo complete 5`
**Then** the CLI prints exactly: `Task 5 completed: "Deploy release"` to stdout.

---

### Behavior 8: ID argument is required

**Given** any state of the storage file
**When** the user runs `cli-todo complete` (without providing an ID)
**Then** argparse reports a missing required argument and exits with code 2.

---

### Behavior 9: Non-integer ID argument

**Given** any state of the storage file
**When** the user runs `cli-todo complete abc`
**Then** argparse reports an invalid argument type and exits with code 2.

---

### Behavior 10: Environment variable respected

**Given** `TODO_FILE` is set to a custom path containing tasks
**When** the user runs `cli-todo complete 1`
**Then** the task in the custom file is updated. The default `tasks.json` is not touched.

---

### Behavior 11: Completing after add — full lifecycle

**Given** the user has just added a task via `cli-todo add "Write report"`
**When** the user runs `cli-todo complete 1`
**Then** the task status changes from "pending" to "completed". A subsequent list shows the task with `[x]` marker.

---

### Behavior 12: Multiple completions

**Given** the storage file contains tasks 1, 2, 3, all pending
**When** the user completes task 1 and then task 3
**Then** tasks 1 and 3 have status "completed", task 2 remains "pending".
