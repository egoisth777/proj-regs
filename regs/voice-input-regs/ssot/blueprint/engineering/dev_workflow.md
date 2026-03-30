# Development Workflow

This document dictates how features are built in the MAS Harness project.

## 1. Specification Cascade (Mandatory)

No code is written until the full spec cascade is complete:

1. **Proposal** (`proposal.md`) — what and why
2. **Behavior Spec** (`behavior_spec.md`) — Given/When/Then for all expected behaviors
3. **Test Spec** (`test_spec.md`) — testable assertions derived from behavior specs
4. **Tests** — SDET agents write all tests before Workers start (TDD)

The OpenSpec is locked after steps 1-3. Tests (step 4) go to the codebase, not the OpenSpec folder.

## 2. Branching & Worktree Isolation

- Main branch (`main`) is protected. Never push directly.
- Every feature task MUST be developed in an isolated `git worktree`.
- Commands:
  - **Create worker environment:** `git worktree add ../<branch-name> <branch-name>`
  - **Execute task:** `cd ../<branch-name>`
  - **Cleanup after merge:** `git worktree remove ../<branch-name> --force`

## 3. Parallel Feature Isolation

- Decoupled features run in parallel, each in its own worktree with its own OpenSpec folder.
- Coupled features (touching the same files) MUST run sequentially.
- **Coupling detection:**
  1. Team Lead performs file-scope analysis per task
  2. Orchestrator compares file scopes across all active features before approving parallel execution
  3. If a Worker discovers unexpected coupling mid-implementation, it STOPS and escalates to the Orchestrator

## 4. Hierarchical Execution (Agent Teams)

- **Orchestrator:** Pure delegator. Never reads/writes files. Only talks to user and dispatches subagents.
- **Team Lead:** Reads OpenSpec, breaks into tasks with file-scope declarations, delegates to Workers.
- **Worker:** Single-function coder executing in an isolated worktree. Sees only its task + blueprint.
- **SDET (Unit/Integration/E2E):** Writes tests before Workers start. Each SDET type has different inputs and scope.

## 5. First-Class Human Citizenship

- In `runtime/active_sprint.md`, tasks can be labeled `Assignee: @Human`.
- The Team Lead skips those tasks during automated execution.
- The human writes the code and submits a PR.
- The Auditor reviews the human's PR against the OpenSpec identically to an AI's PR.

## 6. Pull Requests & Quality Gate

Before any PR merges:
1. Regression Runner executes the full test suite (all tests, not just feature tests)
2. Linter must pass
3. Auditor performs architectural review against blueprint + OpenSpec
4. `post-pr-wait` hook polls remote GitHub PR for CI + review bot feedback
5. All review comments must be resolved

Parallel feature merges: first-merged wins. Subsequent features rebase onto updated main and re-run the full quality gate.

## 7. Conventional Commits

All commit messages follow Conventional Commits format:
```
<type>(<scope>): <description>
```
Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`
Never mention AI/assistant/generated in commit messages.
