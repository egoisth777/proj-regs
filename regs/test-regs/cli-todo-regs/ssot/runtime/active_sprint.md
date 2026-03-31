---
description: "ORCHESTRATOR-ONLY: Index of all active features/sprints. Workers never read this file."
tags:
  - tracking
  - orchestrator-only
---

# Active Sprints

> **Access control:** This file is read/written ONLY by subagents dispatched by the Orchestrator. Worker agents, SDET agents, and other execution agents do NOT have access to this file.

## Active Features

| Feature | OpenSpec Path | Status | Started |
|---|---|---|---|
| add-task | runtime/openspec/changes/feat-001-add-task | execution | 2026-03-30 |
| list-tasks | runtime/openspec/changes/feat-002-list-tasks | execution | 2026-03-30 |
| complete-task | runtime/openspec/changes/feat-003-complete-task | execution | 2026-03-30 |

## Current Feature: feat-003-complete-task
## Phase: execution

## Statuses
- `spec-cascade` — Behavior/test specs being written
- `testing` — SDET agents writing tests
- `execution` — Workers implementing code
- `quality-gate` — Regression Runner + Auditor reviewing
- `pr-review` — Waiting for remote PR feedback
