---
description: OpenSpec Workflow Commands (/opsx)
---

This workflow defines the deterministic CLI commands for executing features via the OpenSpec system.
Agents must follow these commands strictly when initiated by the user.

## `/opsx:propose <feature-name>` (The Spec/Planning Phase)
9: 1. **Initiate:** The Execution Architect creates a new directory `runtime/openspec/changes/<YYYY-MM-DD>-<feature-name>/` from `runtime/openspec/template/`.
10: 2. **Translate:** The Execution Architect reads the finalized `blueprint/design/design.md` written by Sonders during Phase 0 and translates it into granular `proposal.md`, `specs/requirements.md`, and `tasks.md` documents.
11: 3. **Audit:** The Execution Architect spawns the Auditor Subagent. The Auditor verifies that the newly written OpenSpec files perfectly match Sonders' `blueprint/design/design.md`.
12: 4. **Lock:** The Execution Architect fixes any discrepancies reported by the Auditor. The OpenSpec is now locked and ready for implementation.

## `/opsx:apply` (The Execution Phase)
15: 1. The Execution Architect (Main Thread) verifies it is in the context of an approved OpenSpec (e.g., `runtime/openspec/changes/current-feature/`).
16: 2. The Execution Architect sequentially parses the checklist in `tasks.md`.
3. For each task, the Execution Architect spawns 0-State Worker Subagents to implement the code.
4. Workers follow `design.md` and `specs/requirements.md`, writing code until tests pass (0 failures).
5. The Execution Architect checks off tasks in `tasks.md` as Subagents complete them.
6. The Execution Architect outputs a success message indicating all tasks are complete.

## `/opsx:archive`
23: 1. The Agent moves the active OpenSpec directory to `runtime/archive/<YYYY>/<MM>-<feature-name>/`.
24: 2. The Agent updates `runtime/tracking/active_sprint.md` and `runtime/tracking/milestones.md` to reflect the completed work.
25: 3. The Agent outputs a success message indicating the archive is complete.
