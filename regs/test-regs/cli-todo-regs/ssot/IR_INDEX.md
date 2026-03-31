# Implementation Decision Records (IR) Index

This document indexes all `IR-xxx` records within the project. It serves as a single lookup table for agents to understand complex implementation details without scanning the entire `implementation/` directory.

| IR Code  | Short Description | Corresponds To (File/Module) | Date Added |
| :------- | :---------------- | :--------------------------- | :--------- |
| IR-001   | feat-001-add-task: Task model and add functionality | `artifacts/src/todo.py`, `artifacts/src/cli.py` | 2026-03-30 |
| IR-002   | feat-002-list-tasks: List and filter tasks | `artifacts/src/todo.py`, `artifacts/src/cli.py` | 2026-03-30 |
| IR-003   | feat-003-complete-task: Mark tasks as completed | `artifacts/src/todo.py`, `artifacts/src/cli.py` | 2026-03-30 |

## How to use this index

1. **Recorder Agent:** When generating an `IR-xxx.md` file due to a `COMPLEXITY: HIGH` tag in a PR, append a new row to this table.
2. **Executor/Reviewer Agents:** Before modifying complex code marked with `// [IR-xxx]`, look up the IR code here and read the corresponding `runtime/implementation/IR-xxx.md` file to understand the underlying architecture and constraints.
