# Behavior Specification: Add Task

> Produced by the Behavior Spec Writer from the approved proposal.
> Each behavior uses Given/When/Then format and must be observable and testable.

## Behaviors

### Behavior 1: Add a task with default priority

**Given** the todo storage file does not exist or is empty
**When** the user runs `cli-todo add "Buy groceries"`
**Then** a new task is created with id=1, title="Buy groceries", priority="medium", status="pending", and a valid ISO-8601 created_at timestamp. The storage file is created (or updated) with the task persisted. The CLI prints `Task 1 added: "Buy groceries" [priority: medium]` and exits with code 0.

---

### Behavior 2: Add a task with explicit priority

**Given** the todo storage file may or may not exist
**When** the user runs `cli-todo add "Fix critical bug" --priority high`
**Then** a new task is created with title="Fix critical bug" and priority="high". All other fields follow the same rules as Behavior 1. The CLI prints confirmation with the correct priority.

---

### Behavior 3: Auto-incrementing IDs

**Given** the storage file already contains tasks with IDs 1, 2, and 3
**When** the user runs `cli-todo add "New task"`
**Then** the new task receives id=4. The three existing tasks are unchanged. The storage file now contains four tasks.

---

### Behavior 4: Auto-incrementing IDs after gaps

**Given** the storage file contains tasks with IDs 1 and 3 (ID 2 was deleted)
**When** the user runs `cli-todo add "Another task"`
**Then** the new task receives id=4 (max existing ID + 1). The ID gap is not filled.

---

### Behavior 5: Empty title rejection

**Given** any state of the storage file
**When** the user runs `cli-todo add ""`
**Then** the CLI prints an error message indicating the title cannot be empty and exits with code 1. No task is written to the storage file.

---

### Behavior 6: Whitespace-only title rejection

**Given** any state of the storage file
**When** the user runs `cli-todo add "   "`
**Then** the CLI prints an error message indicating the title cannot be empty and exits with code 1. No task is written to the storage file.

---

### Behavior 7: Invalid priority rejection

**Given** any state of the storage file
**When** the user runs `cli-todo add "Task" --priority urgent`
**Then** argparse rejects the invalid choice and prints an error message listing the valid choices (low, medium, high). The CLI exits with code 2 (argparse default). No task is written.

---

### Behavior 8: Storage file created on first use

**Given** the configured storage file path does not exist and neither does its parent directory (when using a custom path)
**When** the user runs `cli-todo add "First task"`
**Then** the storage file is created (parent directories are created if needed via the environment variable path) and the task is persisted.

---

### Behavior 9: Environment variable overrides default file path

**Given** the environment variable `TODO_FILE` is set to `/tmp/my-tasks.json`
**When** the user runs `cli-todo add "Custom path task"`
**Then** the task is written to `/tmp/my-tasks.json` instead of the default `tasks.json` in the current directory.

---

### Behavior 10: Concurrent-safe file writes

**Given** the storage file exists with valid JSON content
**When** the user adds a task
**Then** the entire file is read, the new task is appended to the in-memory list, and the full list is written back atomically (or as close to atomic as practical). Existing tasks are never corrupted or lost.

---

### Behavior 11: Persistence format

**Given** a task has been added
**When** the storage file is inspected
**Then** it contains a JSON array of task objects. Each object has exactly these keys: `id` (int), `title` (str), `priority` (str), `status` (str), `created_at` (str, ISO-8601). The JSON is pretty-printed with 2-space indentation for human readability.

---

### Behavior 12: CLI output format

**Given** the user successfully adds a task
**When** the operation completes
**Then** the CLI writes exactly one line to stdout matching the pattern: `Task <id> added: "<title>" [priority: <priority>]` where `<id>` is the integer ID, `<title>` is the task title as provided, and `<priority>` is one of low/medium/high.
