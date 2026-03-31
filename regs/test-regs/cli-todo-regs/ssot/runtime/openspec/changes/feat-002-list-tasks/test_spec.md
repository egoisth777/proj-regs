# Test Specification: List Tasks

> Produced by the Test Spec Writer from `behavior_spec.md`.
> Every behavior must have at least one corresponding test spec.
> Each test spec declares which SDET agent type is responsible.

## Tests

### Test 1: List all tasks returns everything (unit)

**Type:** Unit
**Covers behavior:** Behavior 1, 2 — List all tasks
**Setup:** Create a `TodoStore` with a pre-populated file containing 3 tasks.
**Steps:** Call `store.list_tasks()` and `store.list_tasks(status_filter="all")`.
**Assert:**
  - Both calls return a list of length 3.
  - All task dicts are present with correct fields.
**Teardown:** Remove temp directory.
**Assigned SDET:** sdet-unit

---

### Test 2: List empty store (unit)

**Type:** Unit
**Covers behavior:** Behavior 5 — Empty list output
**Setup:** Create a `TodoStore` with no pre-existing file.
**Steps:** Call `store.list_tasks()`.
**Assert:**
  - Returns an empty list.
**Teardown:** Remove temp directory.
**Assigned SDET:** sdet-unit

---

### Test 3: List pending tasks only (unit)

**Type:** Unit
**Covers behavior:** Behavior 3 — List pending tasks only
**Setup:** Pre-populate a file with 2 pending and 1 completed task.
**Steps:** Call `store.list_tasks(status_filter="pending")`.
**Assert:**
  - Returns 2 tasks.
  - All returned tasks have status "pending".
**Teardown:** Remove temp directory.
**Assigned SDET:** sdet-unit

---

### Test 4: List completed tasks only (unit)

**Type:** Unit
**Covers behavior:** Behavior 4 — List completed tasks only
**Setup:** Pre-populate a file with 1 pending and 1 completed task.
**Steps:** Call `store.list_tasks(status_filter="completed")`.
**Assert:**
  - Returns 1 task.
  - The returned task has status "completed".
**Teardown:** Remove temp directory.
**Assigned SDET:** sdet-unit

---

### Test 5: Invalid status filter raises (unit)

**Type:** Unit
**Covers behavior:** Behavior 9 — Invalid status filter
**Setup:** Instantiate `TodoStore`.
**Steps:** Call `store.list_tasks(status_filter="archived")`.
**Assert:**
  - Raises `ValueError` with message about invalid status filter.
**Teardown:** Remove temp directory.
**Assigned SDET:** sdet-unit

---

### Test 6: Insertion order preserved (unit)

**Type:** Unit
**Covers behavior:** Behavior 10 — Insertion order preserved
**Setup:** Pre-populate file with tasks in known order (ids 1, 2, 3).
**Steps:** Call `store.list_tasks()`.
**Assert:**
  - IDs appear in order [1, 2, 3].
**Teardown:** Remove temp directory.
**Assigned SDET:** sdet-unit

---

### Test 7: All required fields present (unit)

**Type:** Unit
**Covers behavior:** Behavior 11 — All required fields
**Setup:** Pre-populate file with tasks.
**Steps:** Call `store.list_tasks()`.
**Assert:**
  - Each returned dict has keys: id, title, priority, status, created_at.
**Teardown:** Remove temp directory.
**Assigned SDET:** sdet-unit

---

### Test 8: CLI list empty (integration)

**Type:** Integration
**Covers behavior:** Behavior 5 — Empty list output
**Setup:** Set `TODO_FILE` to a temp path (no file created).
**Steps:** Run `python -m src.cli list` as a subprocess.
**Assert:**
  - Exit code is 0.
  - stdout contains "No tasks found".
**Teardown:** Cleanup temp.
**Assigned SDET:** sdet-integration

---

### Test 9: CLI list all tasks (integration)

**Type:** Integration
**Covers behavior:** Behavior 1 — List all tasks
**Setup:** Add two tasks via CLI, set `TODO_FILE`.
**Steps:** Run `python -m src.cli list` as a subprocess.
**Assert:**
  - Exit code is 0.
  - stdout contains both task titles.
**Teardown:** Cleanup temp.
**Assigned SDET:** sdet-integration

---

### Test 10: CLI list pending filter (integration)

**Type:** Integration
**Covers behavior:** Behavior 3 — List pending tasks only
**Setup:** Add two tasks via CLI, complete one.
**Steps:** Run `python -m src.cli list --status pending`.
**Assert:**
  - Only the pending task title appears in stdout.
  - The completed task title does not appear.
**Teardown:** Cleanup temp.
**Assigned SDET:** sdet-integration

---

### Test 11: CLI list completed filter (integration)

**Type:** Integration
**Covers behavior:** Behavior 4 — List completed tasks only
**Setup:** Add two tasks, complete one.
**Steps:** Run `python -m src.cli list --status completed`.
**Assert:**
  - Only the completed task title appears in stdout.
**Teardown:** Cleanup temp.
**Assigned SDET:** sdet-integration

---

### Test 12: CLI list invalid status (integration)

**Type:** Integration
**Covers behavior:** Behavior 9 — Invalid status filter
**Setup:** Set `TODO_FILE`.
**Steps:** Run `python -m src.cli list --status archived`.
**Assert:**
  - Exit code is 2.
  - stderr contains "invalid choice".
**Teardown:** Cleanup temp.
**Assigned SDET:** sdet-integration

---

### Test 13: CLI list output format (integration)

**Type:** Integration
**Covers behavior:** Behavior 7, 8, 11 — Output format
**Setup:** Add a task via CLI.
**Steps:** Run `python -m src.cli list`.
**Assert:**
  - Output contains `[ ]` marker, task ID with period, title, and priority in parentheses.
**Teardown:** Cleanup temp.
**Assigned SDET:** sdet-integration
