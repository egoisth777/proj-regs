---
description: OpenSpec Workflow Commands (/opsx)
---

This workflow defines the deterministic commands for executing features via the OpenSpec system.
Agents must follow these commands strictly when initiated by the user.

## `/opsx:propose <feature-name>` (Spec Cascade Phase)

1. **Initiate:** The Orchestrator dispatches a subagent to create a new directory `runtime/openspec/changes/<YYYY-MM-DD>-<feature-name>/` by copying from `runtime/openspec/template/`.
2. **Proposal:** The Orchestrator dispatches Sonders to write the design, then Negator to review. Once approved, the Orchestrator dispatches the Behavior Spec Writer to write `behavior_spec.md`.
3. **Test Spec:** The Orchestrator dispatches the Test Spec Writer to write `test_spec.md` from `behavior_spec.md`.
4. **Testing:** The Orchestrator dispatches SDET agents (unit, integration, E2E) to write tests in the codebase.
5. **Lock:** All spec cascade files are finalized. `status.md` is updated to `locked`. The OpenSpec is ready for execution.
6. **Index:** The Orchestrator dispatches a subagent to add the feature to `runtime/openspec/index.md`.

## `/opsx:apply` (Execution Phase)

1. The Orchestrator verifies it is in the context of a locked OpenSpec.
2. The Orchestrator dispatches the Team Lead, who reads the OpenSpec and writes `tasks.md` with file-scope declarations.
3. The Orchestrator checks file scopes against all other active features for coupling.
4. The Team Lead spawns Workers in parallel worktrees to implement code.
5. Workers implement code to pass SDET tests.
6. The Orchestrator dispatches the Regression Runner (full test suite).
7. The Orchestrator dispatches the Auditor (architectural review).
8. PR is created. `post-pr-wait` hook fires — polls remote CI + reviews.
9. All review issues resolved → merge.

## `/opsx:archive` (Wrap-up Phase)

1. The Orchestrator dispatches a subagent to move the completed OpenSpec directory to `runtime/openspec/archive/<YYYY>/<MM>-<feature-name>/`.
2. The subagent updates `runtime/openspec/index.md` (status → `archived`).
3. The subagent updates `runtime/milestones.md` (check off completed sprint).
4. The subagent updates `runtime/active_sprint.md` (remove the feature row).
5. Clean up worktrees and merged branches.
