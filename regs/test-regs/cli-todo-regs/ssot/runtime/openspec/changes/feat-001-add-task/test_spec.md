# Test Specification: Add Task

> Produced by the Test Spec Writer from `behavior_spec.md`.
> Every behavior must have at least one corresponding test spec.
> Each test spec declares which SDET agent type is responsible.

## Tests

### Test 1: Add task with default priority (unit)

**Type:** Unit
**Covers behavior:** Behavior 1 — Add a task with default priority
**Setup:** Create a temporary directory. Instantiate `TodoStore` pointing at a non-existent file in that directory.
**Steps:** Call `store.add_task(title="Buy groceries")`.
**Assert:**
  - Returned task has id=1, title="Buy groceries", priority="medium", status="pending".
  - `created_at` is a valid ISO-8601 string within the last 5 seconds.
  - The storage file now exists and contains exactly one task.
**Teardown:** Remove temporary directory.
**Assigned SDET:** sdet-unit

---

### Test 2: Add task with explicit priority (unit)

**Type:** Unit
**Covers behavior:** Behavior 2 — Add a task with explicit priority
**Setup:** Instantiate `TodoStore` with a temp file.
**Steps:** Call `store.add_task(title="Fix bug", priority="high")`.
**Assert:**
  - Returned task has priority="high".
  - All other fields are correctly populated.
**Teardown:** Remove temp directory.
**Assigned SDET:** sdet-unit

---

### Test 3: Add task with low priority (unit)

**Type:** Unit
**Covers behavior:** Behavior 2 — Add a task with explicit priority
**Setup:** Instantiate `TodoStore` with a temp file.
**Steps:** Call `store.add_task(title="Someday task", priority="low")`.
**Assert:**
  - Returned task has priority="low".
**Teardown:** Remove temp directory.
**Assigned SDET:** sdet-unit

---

### Test 4: Auto-incrementing IDs (unit)

**Type:** Unit
**Covers behavior:** Behavior 3 — Auto-incrementing IDs
**Setup:** Instantiate `TodoStore`. Add three tasks sequentially.
**Steps:** Add a fourth task.
**Assert:**
  - First task has id=1, second id=2, third id=3, fourth id=4.
  - Storage file contains exactly four tasks.
**Teardown:** Remove temp directory.
**Assigned SDET:** sdet-unit

---

### Test 5: ID incrementing with gaps (unit)

**Type:** Unit
**Covers behavior:** Behavior 4 — Auto-incrementing IDs after gaps
**Setup:** Pre-populate storage file with tasks having IDs [1, 3] (simulating a deletion gap).
**Steps:** Call `store.add_task(title="New")`.
**Assert:**
  - New task has id=4 (max existing + 1).
**Teardown:** Remove temp directory.
**Assigned SDET:** sdet-unit

---

### Test 6: Empty title rejection (unit)

**Type:** Unit
**Covers behavior:** Behavior 5 — Empty title rejection
**Setup:** Instantiate `TodoStore`.
**Steps:** Call `store.add_task(title="")`.
**Assert:**
  - A `ValueError` is raised with a message about empty title.
  - No task is written to storage.
**Teardown:** Remove temp directory.
**Assigned SDET:** sdet-unit

---

### Test 7: Whitespace-only title rejection (unit)

**Type:** Unit
**Covers behavior:** Behavior 6 — Whitespace-only title rejection
**Setup:** Instantiate `TodoStore`.
**Steps:** Call `store.add_task(title="   ")`.
**Assert:**
  - A `ValueError` is raised.
  - No task is written to storage.
**Teardown:** Remove temp directory.
**Assigned SDET:** sdet-unit

---

### Test 8: Storage file auto-creation (unit)

**Type:** Unit
**Covers behavior:** Behavior 8 — Storage file created on first use
**Setup:** Create a temp directory. Do NOT create the storage file.
**Steps:** Instantiate `TodoStore` pointing to `<tmpdir>/tasks.json`. Add a task.
**Assert:**
  - `<tmpdir>/tasks.json` now exists.
  - It contains valid JSON with one task.
**Teardown:** Remove temp directory.
**Assigned SDET:** sdet-unit

---

### Test 9: Persistence format validation (unit)

**Type:** Unit
**Covers behavior:** Behavior 11 — Persistence format
**Setup:** Instantiate `TodoStore`. Add one task.
**Steps:** Read the raw storage file content.
**Assert:**
  - Content is valid JSON.
  - Root element is an array of length 1.
  - The task object has keys: id, title, priority, status, created_at.
  - JSON is indented (contains newlines and spaces).
**Teardown:** Remove temp directory.
**Assigned SDET:** sdet-unit

---

### Test 10: CLI add with default priority (integration)

**Type:** Integration
**Covers behavior:** Behavior 1, Behavior 12 — CLI output format
**Setup:** Set `TODO_FILE` env var to a temp file path.
**Steps:** Run `python -m src.cli add "Buy groceries"` as a subprocess.
**Assert:**
  - Exit code is 0.
  - stdout contains `Task 1 added: "Buy groceries" [priority: medium]`.
  - The temp file contains one task with correct fields.
**Teardown:** Remove temp file.
**Assigned SDET:** sdet-integration

---

### Test 11: CLI add with explicit priority (integration)

**Type:** Integration
**Covers behavior:** Behavior 2, Behavior 12 — CLI output format
**Setup:** Set `TODO_FILE` env var to a temp file path.
**Steps:** Run `python -m src.cli add "Urgent" --priority high` as a subprocess.
**Assert:**
  - Exit code is 0.
  - stdout contains `Task 1 added: "Urgent" [priority: high]`.
**Teardown:** Remove temp file.
**Assigned SDET:** sdet-integration

---

### Test 12: CLI add with empty title (integration)

**Type:** Integration
**Covers behavior:** Behavior 5 — Empty title rejection
**Setup:** Set `TODO_FILE` env var to a temp file path.
**Steps:** Run `python -m src.cli add ""` as a subprocess.
**Assert:**
  - Exit code is 1.
  - stderr contains an error message about empty title.
  - Temp file does not exist (no task written).
**Teardown:** Cleanup if needed.
**Assigned SDET:** sdet-integration

---

### Test 13: CLI add with invalid priority (integration)

**Type:** Integration
**Covers behavior:** Behavior 7 — Invalid priority rejection
**Setup:** Set `TODO_FILE` env var to a temp file path.
**Steps:** Run `python -m src.cli add "Task" --priority urgent` as a subprocess.
**Assert:**
  - Exit code is 2.
  - stderr mentions invalid choice.
**Teardown:** Cleanup if needed.
**Assigned SDET:** sdet-integration

---

### Test 14: Environment variable file path override (integration)

**Type:** Integration
**Covers behavior:** Behavior 9 — Environment variable overrides default file path
**Setup:** Create a temp directory. Set `TODO_FILE` to `<tmpdir>/custom.json`.
**Steps:** Run `python -m src.cli add "Custom path"` as a subprocess.
**Assert:**
  - `<tmpdir>/custom.json` exists and contains the task.
  - Default `tasks.json` in CWD does NOT exist.
**Teardown:** Remove temp directory.
**Assigned SDET:** sdet-integration
