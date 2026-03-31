# Proposal: Add Task

## Summary

The "Add Task" feature allows users to create new todo items via the command-line interface.
Each task is persisted to a local JSON file and assigned a unique auto-incrementing integer ID.
Users provide a required title and an optional priority level (low, medium, or high).
This is the foundational feature of the CLI todo application; without it no other features
(list, complete, delete) can operate. The feature establishes the data model, storage layer,
and the first CLI subcommand that all subsequent features will build upon.

## User Stories

- As a user, I want to add a task with just a title so I can quickly capture things I need to do.
- As a user, I want to optionally set a priority (low/medium/high) when adding a task so I can
  indicate how important it is.
- As a user, I want each task to receive a unique numeric ID so I can reference it later.
- As a user, I want to see a confirmation message after adding a task so I know it was saved.
- As a user, I want my tasks persisted to disk so they survive across CLI invocations.

## Requirements

- The CLI exposes an `add` subcommand: `cli-todo add "Buy groceries" --priority high`
- The `--priority` flag accepts exactly three values: `low`, `medium`, `high`.
- When `--priority` is omitted the default is `medium`.
- Each new task is stored as a JSON object with fields: `id`, `title`, `priority`, `status`, `created_at`.
- `id` is a positive integer, auto-incrementing from 1.
- `status` is always `"pending"` on creation.
- `created_at` is an ISO-8601 timestamp string.
- Tasks are appended to a JSON file (default `tasks.json` in the current directory).
- The storage file path can be overridden via the `TODO_FILE` environment variable.
- After successful creation the CLI prints: `Task <id> added: "<title>" [priority: <priority>]`
- If the title is empty or whitespace-only, the CLI prints an error and exits with code 1.
- If an invalid priority value is supplied, argparse rejects it before reaching application logic.

## Scope

### In Scope

- Task data model definition (dataclass / dict schema)
- TodoStore class with an `add_task` method
- JSON file read/write logic (create file if absent, load existing tasks)
- CLI `add` subcommand with argparse
- Confirmation output on success
- Input validation (empty title)
- Environment variable override for file path

### Out of Scope

- Listing tasks (feat-002)
- Completing tasks (feat-003)
- Deleting tasks (future feature)
- Any network or database storage
- GUI or TUI interface
- Task editing or updating fields other than status

## Dependencies

- Python 3.10+ standard library (json, argparse, datetime, os, dataclasses)
- No external packages required for this feature

## Acceptance Criteria

- Running `cli-todo add "Buy milk"` creates a task with id=1, title="Buy milk", priority="medium", status="pending".
- Running `cli-todo add "Urgent fix" --priority high` creates a task with priority="high".
- The JSON file is created automatically if it does not exist.
- Subsequent adds increment the ID correctly.
- An empty title produces an error message and exit code 1.
- The `TODO_FILE` environment variable is respected.
- All unit and integration tests for this feature pass.
