# Proposal: Complete Task

## Summary

The "Complete Task" feature allows users to mark a pending todo item as completed by
specifying its numeric ID on the command line. This is the primary workflow for closing
out work items. When a task is completed, its status field changes from "pending" to
"completed" in the JSON storage file. The feature includes validation to ensure the
specified task exists and has not already been completed, providing clear error messages
in both failure cases. This completes the core task lifecycle: create (add) -> review
(list) -> finish (complete).

## User Stories

- As a user, I want to mark a task as completed by its ID so I can track my progress.
- As a user, I want a confirmation message after completing a task so I know the operation
  succeeded.
- As a user, I want an error if I try to complete a task that does not exist so I can
  correct my input.
- As a user, I want an error if I try to complete a task that is already done so I am
  aware it was previously finished.
- As a user, I want completing a task to leave all other tasks unchanged so my data
  remains consistent.

## Requirements

- The CLI exposes a `complete` subcommand: `cli-todo complete <id>`
- The `<id>` argument is a required positional integer.
- On success, the task's `status` field changes from `"pending"` to `"completed"`.
- On success, the CLI prints: `Task <id> completed: "<title>"`
- The CLI exits with code 0 on success.
- If no task with the given ID exists, the CLI prints an error to stderr and exits with code 1.
- If the task is already completed, the CLI prints an error to stderr and exits with code 1.
- All other tasks in the storage file remain unchanged.
- The change is persisted immediately to the JSON file.
- The feature respects the `TODO_FILE` environment variable for storage path.

## Scope

### In Scope

- CLI `complete` subcommand with argparse
- `TodoStore.complete_task(task_id)` method
- Status change from "pending" to "completed"
- Error handling: task not found, already completed
- Persistence of the updated task list
- Confirmation output

### Out of Scope

- Undoing a completion (reverting to pending)
- Completing multiple tasks at once
- Completing by title or pattern match
- Adding a `completed_at` timestamp (future enhancement)
- Deleting tasks

## Dependencies

- feat-001-add-task (establishes data model, storage layer, and TodoStore class)
- feat-002-list-tasks (users need to list tasks to find IDs before completing)
- Python argparse (standard library)

## Acceptance Criteria

- Running `cli-todo complete 1` on a pending task changes its status to "completed".
- The CLI prints `Task 1 completed: "<title>"` on success.
- Running `cli-todo complete 999` when no task 999 exists prints an error and exits 1.
- Running `cli-todo complete 1` when task 1 is already completed prints an error and exits 1.
- Other tasks in the file are not modified.
- The JSON file is updated immediately.
- All unit and integration tests for this feature pass.
