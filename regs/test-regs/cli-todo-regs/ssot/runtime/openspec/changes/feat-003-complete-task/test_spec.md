# Test Specification: Complete Task

> Produced by the Test Spec Writer from `behavior_spec.md`.
> Every behavior must have at least one corresponding test spec.
> Each test spec declares which SDET agent type is responsible.

## Tests

### Test 1: Complete a pending task changes status (unit)

**Type:** Unit
**Covers behavior:** Behavior 1 — Complete a pending task
**Setup:** Create a `TodoStore` with pre-populated tasks (3 pending tasks).
**Steps:** Call `store.complete_task(task_id=1)`.
**Assert:**
  - Returned dict has `status` = "completed" and `id` = 1.
**Teardown:** Remove temp directory.
**Assigned SDET:** sdet-unit

---

### Test 2: Completed task persists to file (unit)

**Type:** Unit
**Covers behavior:** Behavior 1, 6 — Persistence verification
**Setup:** Create a `TodoStore` with pre-populated tasks.
**Steps:** Call `store.complete_task(task_id=2)`, then reload and inspect.
**Assert:**
  - Task 2 in the reloaded data has status "completed".
**Teardown:** Remove temp directory.
**Assigned SDET:** sdet-unit

---

### Test 3: Task not found raises ValueError (unit)

**Type:** Unit
**Covers behavior:** Behavior 2 — Task not found
**Setup:** Create a `TodoStore` with pre-populated tasks (IDs 1-3).
**Steps:** Call `store.complete_task(task_id=999)`.
**Assert:**
  - Raises `ValueError` with "not found" in the message.
**Teardown:** Remove temp directory.
**Assigned SDET:** sdet-unit

---

### Test 4: Empty store raises ValueError (unit)

**Type:** Unit
**Covers behavior:** Behavior 3 — Empty store
**Setup:** Create a `TodoStore` with no file.
**Steps:** Call `store.complete_task(task_id=1)`.
**Assert:**
  - Raises `ValueError` with "not found" in the message.
**Teardown:** Remove temp directory.
**Assigned SDET:** sdet-unit

---

### Test 5: Already completed task raises ValueError (unit)

**Type:** Unit
**Covers behavior:** Behavior 4 — Already completed task
**Setup:** Pre-populate file with a task that has status "completed".
**Steps:** Call `store.complete_task(task_id=1)`.
**Assert:**
  - Raises `ValueError` with "already completed" in the message.
**Teardown:** Remove temp directory.
**Assigned SDET:** sdet-unit

---

### Test 6: Other tasks unchanged after completion (unit)

**Type:** Unit
**Covers behavior:** Behavior 5 — Other tasks unchanged
**Setup:** Create a `TodoStore` with 3 pending tasks.
**Steps:** Call `store.complete_task(task_id=2)`, reload all tasks.
**Assert:**
  - Task 1 status is still "pending".
  - Task 3 status is still "pending".
  - Task 2 status is "completed".
**Teardown:** Remove temp directory.
**Assigned SDET:** sdet-unit

---

### Test 7: CLI complete success (integration)

**Type:** Integration
**Covers behavior:** Behavior 1, 7 — CLI output format
**Setup:** Add a task via CLI, set `TODO_FILE`.
**Steps:** Run `python -m src.cli complete 1` as a subprocess.
**Assert:**
  - Exit code is 0.
  - stdout contains `Task 1 completed: "Finish report"` (or the task title used).
  - JSON file shows task 1 with status "completed".
**Teardown:** Cleanup temp.
**Assigned SDET:** sdet-integration

---

### Test 8: CLI complete not found (integration)

**Type:** Integration
**Covers behavior:** Behavior 2 — Task not found
**Setup:** Add a task via CLI, set `TODO_FILE`.
**Steps:** Run `python -m src.cli complete 999` as a subprocess.
**Assert:**
  - Exit code is 1.
  - stderr contains "not found".
**Teardown:** Cleanup temp.
**Assigned SDET:** sdet-integration

---

### Test 9: CLI complete already completed (integration)

**Type:** Integration
**Covers behavior:** Behavior 4 — Already completed task
**Setup:** Add a task, complete it once via CLI.
**Steps:** Run `python -m src.cli complete 1` again.
**Assert:**
  - Exit code is 1.
  - stderr contains "already completed".
**Teardown:** Cleanup temp.
**Assigned SDET:** sdet-integration

---

### Test 10: CLI complete then list shows completed (integration)

**Type:** Integration
**Covers behavior:** Behavior 6, 11 — Full lifecycle
**Setup:** Add two tasks, complete one.
**Steps:** Run `python -m src.cli list --status completed`.
**Assert:**
  - The completed task appears in the output.
  - The pending task does not appear.
  - Completed task line has `[x]` marker.
**Teardown:** Cleanup temp.
**Assigned SDET:** sdet-integration

---

### Test 11: CLI complete list shows checkbox (integration)

**Type:** Integration
**Covers behavior:** Behavior 11 — Full lifecycle with list display
**Setup:** Add two tasks, complete task 1.
**Steps:** Run `python -m src.cli list` to show all tasks.
**Assert:**
  - Task 1 appears with `[x]` marker.
  - Task 2 appears with `[ ]` marker.
**Teardown:** Cleanup temp.
**Assigned SDET:** sdet-integration
