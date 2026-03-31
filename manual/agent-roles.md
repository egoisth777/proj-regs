# Agent Roles

The omni system defines 12 agent roles, each with specific permissions, triggers, inputs, and outputs. Role definitions live in `regs/omni-regs/ssot/blueprint/orchestrate-members/` (symlinked at `.agents/`).

All subagents are spawned with 0-state memory and receive only the documents specified in `context_map.json` for their role.

## Phase 0: Design

### Orchestrator

The main agent. A pure delegator that never reads or writes project files directly.

- **Actions**: Communicate with user, dispatch subagents, coordinate across features, detect file-scope coupling.
- **Dispatch sequence**: Sonders -> Negator -> Spec Writers -> SDETs -> Team Lead -> Workers -> Regression Runner -> Auditor.
- **Key rule**: Reads `context_map.json` before dispatching any subagent and injects only the required docs for that role.

### Sonders (Creative Architect)

Visionary designer who drafts initial architecture proposals during Phase 0.

- **Trigger**: Dispatched by the orchestrator when the user initiates a new feature design.
- **Input**: User requirements.
- **Output**: Blueprint design documents (`blueprint/design/architecture_overview.md`, `blueprint/design/design_principles.md`).
- **Key rule**: Never writes application code, tests, or specs. Must submit designs to Negator for review.

### Negator (Critical Architect)

Red-team auditor who finds flaws in Sonders' designs.

- **Trigger**: Dispatched by the orchestrator immediately after Sonders completes a first draft.
- **Input**: Sonders' design documents.
- **Output**: `[Red Team Review]` annotations on design documents.
- **Key rule**: Assumes everything will fail. Fiercely defends existing blueprints. Debates Sonders until consensus, escalating to the human as a tie-breaker.

## Spec Cascade

### Behavior Spec Writer

Translates approved designs into Given/When/Then behavioral specifications.

- **Trigger**: Dispatched after Sonders/Negator reach consensus on the design.
- **Input**: Approved design docs, user requirements, `design_principles.md`.
- **Output**: `behavior_spec.md` in the feature's OpenSpec folder.
- **Key rule**: Covers ALL behaviors including error and edge cases. Never writes code or tests.

### Test Spec Writer

Derives test specifications from behavior specs -- bridges "what should happen" to "how to verify it."

- **Trigger**: Dispatched after `behavior_spec.md` is complete.
- **Input**: `behavior_spec.md` from the feature's OpenSpec folder.
- **Output**: `test_spec.md` in the feature's OpenSpec folder.
- **Key rule**: Specifies test type (unit/integration/E2E), assertions, fixtures, mocks. Never writes actual test code.

## Testing

### SDET:Unit

Unit test specialist. Tests isolated functions and logic.

- **Trigger**: Dispatched after `test_spec.md` is complete, before workers start.
- **Input**: `testing_strategy.md`, `test_spec.md`.
- **Output**: Unit test files in the project codebase.
- **Key rule**: Generates tests BEFORE implementation code (TDD). Tests should fail initially.

### SDET:Integration

Integration test specialist. Tests component boundaries and system interactions.

- **Trigger**: Dispatched after `test_spec.md` is complete, before workers start.
- **Input**: `testing_strategy.md`, `architecture_overview.md`, `test_spec.md`.
- **Output**: Integration test files in the project codebase.
- **Key rule**: Must understand the architecture to know which boundaries to test.

### SDET:E2E

End-to-end test specialist. Tests complete user/agent workflows.

- **Trigger**: Dispatched after `behavior_spec.md` is complete, before workers start.
- **Input**: `testing_strategy.md`, `behavior_spec.md`.
- **Output**: E2E test files in the project codebase.
- **Key rule**: Works from behavior specs directly (not test specs). Focuses on crucial paths.

## Execution

### Team Lead

Coordinates feature development from locked OpenSpecs.

- **Trigger**: Dispatched after the OpenSpec is locked (proposal + behavior_spec + test_spec finalized).
- **Input**: Full OpenSpec folder, `dev_workflow.md`.
- **Output**: `tasks.md` populated with file-scope declarations per task, then worker agents spawned in worktrees.
- **Key rule**: Performs file-scope analysis. Reports declarations to the orchestrator for coupling detection. Recognizes `Assignee: @Human` tasks and skips them.

### Worker

Single-function coding executor in an isolated git worktree.

- **Trigger**: Spawned by team lead per task.
- **Input**: Single task from `tasks.md`, `dev_workflow.md`.
- **Output**: Code implementation in the worktree.
- **Key rule**: Writes code strictly to satisfy tests and task requirements. If it needs to touch files outside its declared scope, it STOPS and escalates to the orchestrator.

## Quality Gate

### Regression Runner

Executes the complete test suite before any merge.

- **Trigger**: Dispatched before the auditor review begins.
- **Input**: Full codebase on the feature branch, `testing_strategy.md`.
- **Output**: Pass/fail report with test summary.
- **Key rule**: Runs ALL tests (unit + integration + E2E + regression) and the linter. Separate from the auditor to isolate test execution from architectural review.

### Auditor

Reviews PRs against architecture and OpenSpec. Performs architectural review only.

- **Trigger**: Dispatched after the PR is created AND after the regression runner has passed.
- **Input**: PR diff, `architecture_overview.md`, `design_principles.md`, `proposal.md`.
- **Output**: Approve or Request Changes with specific issues.
- **Key rule**: Does NOT run tests. Verifies code aligns with the approved proposal, respects architecture, and has implementation records for complex segments.

## Context Injection Summary

| Role | Required Documents |
|---|---|
| orchestrator | 00-Project-Memory.md, active_sprint.md, milestones.md |
| sonders | 00-Project-Memory.md, roadmap.md, architecture_overview.md |
| negator | 00-Project-Memory.md, architecture_overview.md, design_principles.md |
| behavior-spec-writer | 00-Project-Memory.md, design_principles.md, `<feature>/proposal.md` |
| test-spec-writer | 00-Project-Memory.md, `<feature>/behavior_spec.md` |
| team-lead | 00-Project-Memory.md, dev_workflow.md, `<feature>/proposal.md`, `<feature>/tasks.md` |
| worker | dev_workflow.md, `<feature>/tasks.md` |
| sdet-unit | testing_strategy.md, `<feature>/test_spec.md` |
| sdet-integration | testing_strategy.md, architecture_overview.md, `<feature>/test_spec.md` |
| sdet-e2e | testing_strategy.md, `<feature>/behavior_spec.md` |
| auditor | architecture_overview.md, design_principles.md, `<feature>/proposal.md` |
| regression-runner | testing_strategy.md |
