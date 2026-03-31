# Proposal: List Tasks

## Summary

The "List Tasks" feature allows users to view their todo items from the command line.
Users can see all tasks at once or filter by status (pending or completed). Each task
is displayed with a visual status indicator, its numeric ID, title, and priority level.
This feature is essential for users to review what they need to do, check progress, and
decide which task to work on next. It reads from the same local JSON file used by the
add-task feature and produces formatted, human-readable output on stdout.

## User Stories

- As a user, I want to list all my tasks so I can see everything on my plate.
- As a user, I want to filter tasks by status so I can focus on what is pending or review
  what I have completed.
- As a user, I want to see a clear visual indicator of each task's status so I can quickly
  distinguish completed from pending items.
- As a user, I want to see the priority of each task in the listing so I can decide what
  to work on first.
- As a user, I want a helpful message when I have no tasks so I know the system is working
  even when the list is empty.

## Requirements

- The CLI exposes a `list` subcommand: `cli-todo list [--status all|pending|completed]`
- The `--status` flag accepts exactly three values: `all`, `pending`, `completed`.
- When `--status` is omitted the default is `all`.
- Each task is displayed on one line with the format:
  `[<marker>] <id>. <title> (priority: <priority>)`
  where `<marker>` is `x` for completed tasks and a space for pending tasks.
- If no tasks match the filter, the CLI prints `No tasks found.`
- The CLI exits with code 0 on success.
- If an invalid `--status` value is supplied, argparse rejects it and exits with code 2.
- Tasks are displayed in the order they appear in the JSON file (insertion order).
- The feature reads from the same storage file as add-task (respects `TODO_FILE` env var).

## Scope

### In Scope

- CLI `list` subcommand with argparse
- `--status` flag with choices: all, pending, completed
- Formatted output with status markers
- Empty list handling
- Reading from the JSON storage file
- Filtering logic in TodoStore

### Out of Scope

- Sorting by priority or date (future enhancement)
- Pagination for long lists
- Color/rich formatting
- Search/grep within task titles
- Exporting to other formats (CSV, etc.)

## Dependencies

- feat-001-add-task must be completed first (establishes data model and storage layer)
- TodoStore class with `_load()` method
- Python argparse (standard library)

## Acceptance Criteria

- Running `cli-todo list` with tasks present shows all tasks with proper formatting.
- Running `cli-todo list --status pending` shows only pending tasks.
- Running `cli-todo list --status completed` shows only completed tasks.
- Running `cli-todo list` with no tasks prints `No tasks found.`
- Running `cli-todo list --status invalid` produces an argparse error and exit code 2.
- Completed tasks show `[x]` marker; pending tasks show `[ ]` marker.
- Each line includes the task ID, title, and priority.
- All unit and integration tests for this feature pass.
