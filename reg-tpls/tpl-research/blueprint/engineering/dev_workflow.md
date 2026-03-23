# Development Workflow

This document dictates how features are built in this MAS (Multi-Agent System) project.

## 1. Feature Specification
- Everything begins with an OpenSpec in `openspec/changes/`.
- No code is written until the proposal and testing plan are finalized.

## 2. Branching & Parallelization (Deterministic `git-worktree`)
- Main branch (`main` or `master`) is protected.
- **git-worktree Isolation:** Every feature task MUST be developed in an isolated `git-worktree` parallel branch to prevent hallucination.
- **Command Injection Rules:** Agents must use the following rigid commands instead of navigating standard git branches:
  - **Create Worker Environment:** `git worktree add ../<branch-name> <branch-name>`
  - **Execute Task:** `cd ../<branch-name>`
  - **Cleanup (After PR):** `git worktree remove ../<branch-name> --force`

## 3. Hierarchical Execution (Agent Teams)
- **Executor Team Lead:** Reads the `proposal.md` and `tasks.md` from the OpenSpec, and delegates individual functions out to multiple Workers.
- **Worker:** A single-function coder executing strictly within the path created by `git worktree add`.
- **SDET:** Generates tests based on the `test-plan.md` *before* the Worker writes code.
- **Recorder:** Creates `IR-xxx` records for complex segments and updates `implementation/IR_INDEX.md`.

## 4. First-Class Human Citizenship (Override Protocol)
- In [`tracking/active_sprint.md`](../tracking/active_sprint.md), tasks can be labeled `Assignee: @Human`.
- The Executor Team Lead will see this and skip the task.
- The human writes the code and submits a Pull Request.
- The automated **Auditor Agent** will review the human's PR against the OpenSpec exactly as it would review an AI's PR.

## 5. Pull Requests & CI/CD
- All changes go through a PR.
- **Deterministic CI/CD Execution:** Before the Auditor agent reviews a PR, it MUST explicitly run the project's regression test suite and linter commands in the terminal.
  - *Example: `npm run lint && npm run test` or `pytest`*
  - The Auditor agent must read the terminal output to ensure 0 failures before proceeding to the architecture review.
- **Review & Merge (Phase 3):** The Auditor agent verifies alignment with the SSoT architecture and complexity tags.
- Merge via Squash to keep history clean.
