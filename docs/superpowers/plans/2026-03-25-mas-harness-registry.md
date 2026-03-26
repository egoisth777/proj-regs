# MAS Harness Registry Scaffolding — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold the complete `mas-harness/` project registry as defined in the design spec at `docs/superpowers/specs/2026-03-24-mas-harness-registry-design.md`

**Architecture:** This is a pure markdown + JSON scaffolding task. The registry is an Obsidian vault that acts as SSoT and runtime harness for the MAS Harness project. No executable code — all files are markdown documents and one JSON config. Content must match the spec precisely.

**Tech Stack:** Markdown, JSON, Obsidian vault conventions

**Spec:** `docs/superpowers/specs/2026-03-24-mas-harness-registry-design.md`

**Task execution order:** Tasks MUST be executed sequentially (1 → 2 → ... → 11). Later tasks depend on directories created by earlier tasks, and Task 11 verifies the entire structure.

---

## File Map

All paths relative to `mas-harness/` in the repo root.

### Root files
| File | Purpose |
|---|---|
| `00-Project-Memory.md` | Entry point — SSoT routing for 0-state agents |
| `IR_INDEX.md` | Implementation decision records index |
| `context_map.json` | Minimum-context injection rules per agent role |

### `.obsidian/` — Vault config
| File | Purpose |
|---|---|
| `.obsidian/app.json` | Obsidian app settings |
| `.obsidian/appearance.json` | Obsidian appearance settings |
| `.obsidian/core-plugins.json` | Obsidian core plugin config |

### `blueprint/design/` — Architecture and design
| File | Purpose |
|---|---|
| `blueprint/design/architecture_overview.md` | Harness components: protocol layer, hooks, skills, CLI |
| `blueprint/design/design_principles.md` | Spec cascade philosophy + minimum context principle |
| `blueprint/design/api_mapping.md` | JSON inter-flow data contracts |

### `blueprint/engineering/` — Workflow and testing
| File | Purpose |
|---|---|
| `blueprint/engineering/dev_workflow.md` | Feature isolation model, worktree rules, PR flow |
| `blueprint/engineering/testing_strategy.md` | BDD + TDD + full regression gate model |
| `blueprint/engineering/performance_goals.md` | Performance targets |

### `blueprint/orchestrate-members/` — Agent role definitions (12 files)
| File | Purpose |
|---|---|
| `blueprint/orchestrate-members/orchestrator.md` | Pure delegator, never reads/writes |
| `blueprint/orchestrate-members/sonders.md` | Creative architect (Phase 0) |
| `blueprint/orchestrate-members/negator.md` | Red-team critic (Phase 0) |
| `blueprint/orchestrate-members/behavior-spec-writer.md` | Requirements → Given/When/Then |
| `blueprint/orchestrate-members/test-spec-writer.md` | Behavior specs → test specifications |
| `blueprint/orchestrate-members/team-lead.md` | Reads OpenSpec, delegates to workers |
| `blueprint/orchestrate-members/worker.md` | Isolated coder in worktree |
| `blueprint/orchestrate-members/sdet-unit.md` | Unit test writer |
| `blueprint/orchestrate-members/sdet-integration.md` | Integration test writer |
| `blueprint/orchestrate-members/sdet-e2e.md` | E2E test writer |
| `blueprint/orchestrate-members/auditor.md` | PR gatekeeper (architecture + OpenSpec) |
| `blueprint/orchestrate-members/regression-runner.md` | Full test suite before merge |

### `blueprint/hooks/` — Hook specifications
| File | Purpose |
|---|---|
| `blueprint/hooks/post-pr-wait.md` | After local PR → poll remote → wait for CI + reviews |

### `blueprint/planning/` — Roadmap
| File | Purpose |
|---|---|
| `blueprint/planning/roadmap.md` | Milestones containing sprints |

### `runtime/` — Dynamic state
| File | Purpose |
|---|---|
| `runtime/active_sprint.md` | Orchestrator-only index of active features |
| `runtime/milestones.md` | Milestone checklist with completion criteria |
| `runtime/backlog.md` | Permanent intake queue |
| `runtime/resolved_bugs.md` | Resolved bugs log |

### `runtime/openspec/` — Feature specs
| File | Purpose |
|---|---|
| `runtime/openspec/index.md` | Feature registry table (active + completed) |
| `runtime/openspec/template/proposal.md` | Template: what and why |
| `runtime/openspec/template/behavior_spec.md` | Template: Given/When/Then |
| `runtime/openspec/template/test_spec.md` | Template: test specifications |
| `runtime/openspec/template/tasks.md` | Template: granular checklist |
| `runtime/openspec/template/status.md` | Template: feature-local runtime state |
| `runtime/openspec/changes/.gitkeep` | Keeps empty dir in git |
| `runtime/openspec/archive/.gitkeep` | Keeps empty dir in git |

### Other runtime dirs
| File | Purpose |
|---|---|
| `runtime/implementation/.gitkeep` | IR-xxx records (empty initially) |
| `runtime/research/.gitkeep` | Scratchpad (empty initially) |

### `.agents/workflows/`
| File | Purpose |
|---|---|
| `.agents/workflows/opsx.md` | OpenSpec workflow commands |

---

## Tasks

### Task 1: Root files — 00-Project-Memory.md, IR_INDEX.md, .obsidian/

**Files:**
- Create: `mas-harness/00-Project-Memory.md`
- Create: `mas-harness/IR_INDEX.md`
- Create: `mas-harness/.obsidian/app.json`
- Create: `mas-harness/.obsidian/appearance.json`
- Create: `mas-harness/.obsidian/core-plugins.json`

- [ ] **Step 1: Create 00-Project-Memory.md**

This is the entry point for 0-state agents. It routes them to the correct section of the registry. Reference: spec Section 3 (line 76) and Section 4 (lines 138-160). No CLAUDE.md or AGENTS.md links — those live in the project repo only.

```markdown
# MAS Harness — Project Memory

## Context Protocol
- This Registry acts as the Single Source of Truth (SSoT) for the MAS Harness project codebase.
- ONLY the Orchestrator (via dispatched subagents) reads and modifies `runtime/` updates.
- Agents receive documents via `context_map.json` injection — they do not browse the registry directly.

## SSoT Routing (Obsidian Vault)

### The Static Blueprint (Immutable during sprints)
These folders dictate HOW the system works and WHAT it is supposed to be. Agents treat these as read-only during sprints.

- **Architecture design**: `blueprint/design/architecture_overview.md`
- **Design principles**: `blueprint/design/design_principles.md`
- **API / data contracts**: `blueprint/design/api_mapping.md`
- **Engineering workflow**: `blueprint/engineering/dev_workflow.md`
- **Testing strategy**: `blueprint/engineering/testing_strategy.md`
- **Performance goals**: `blueprint/engineering/performance_goals.md`
- **Agent role definitions**: `blueprint/orchestrate-members/`
- **Hook specifications**: `blueprint/hooks/`
- **Phase roadmap**: `blueprint/planning/roadmap.md`
- **Context Protocol map**: `context_map.json`

### The Dynamic State (Runtime)
These folders track live execution, progress, bugs, and active context. Updated by dispatched subagents during sprints.

- **Active Sprints** (orchestrator-only): `runtime/active_sprint.md`
- **Milestones**: `runtime/milestones.md`
- **Backlog**: `runtime/backlog.md`
- **OpenSpec Index**: `runtime/openspec/index.md`
- **Active Features**: `runtime/openspec/changes/`
- **Completed Features**: `runtime/openspec/archive/`
- **Implementation Records (IRs)**: `runtime/implementation/` → Indexed in `IR_INDEX.md`
- **Resolved bugs log**: `runtime/resolved_bugs.md`
- **Research (Scratchpad)**: `runtime/research/`

## Definitions
- **Sprint**: One feature's complete lifecycle through the spec cascade (proposal → merge). NOT the industry-standard time-boxed sprint.
- **Milestone**: A collection of completed sprints that achieve a larger goal (grand vision checkpoint).
```

- [ ] **Step 2: Create IR_INDEX.md**

```markdown
# Implementation Decision Records (IR) Index

This document indexes all `IR-xxx` records within the project. It serves as a single lookup table for agents to understand complex implementation details without scanning the entire `implementation/` directory.

| IR Code  | Short Description | Corresponds To (File/Module) | Date Added |
| :------- | :---------------- | :--------------------------- | :--------- |
|          |                   |                              |            |

## How to use this index

1. **Recorder Agent:** When generating an `IR-xxx.md` file due to a `COMPLEXITY: HIGH` tag in a PR, append a new row to this table.
2. **Executor/Reviewer Agents:** Before modifying complex code marked with `// [IR-xxx]`, look up the IR code here and read the corresponding `runtime/implementation/IR-xxx.md` file to understand the underlying architecture and constraints.
```

- [ ] **Step 3: Create .obsidian/ vault config**

```json
// .obsidian/app.json
{
  "alwaysUpdateLinks": true,
  "vimMode": true
}
```

```json
// .obsidian/appearance.json
{}
```

```json
// .obsidian/core-plugins.json
{
  "file-explorer": true,
  "global-search": true,
  "graph": true,
  "outline": true,
  "page-preview": true,
  "tag-pane": true
}
```

- [ ] **Step 4: Verify structure**

Run: `find mas-harness -type f | sort`
Expected: should show `00-Project-Memory.md`, `IR_INDEX.md`, and 3 `.obsidian/` files.

- [ ] **Step 5: Commit**

```bash
git add mas-harness/00-Project-Memory.md mas-harness/IR_INDEX.md mas-harness/.obsidian/
git commit -m "feat(mas-harness): add root files and obsidian vault config"
```

---

### Task 2: context_map.json

**Files:**
- Create: `mas-harness/context_map.json`

- [ ] **Step 1: Create context_map.json**

This is the minimum-context injection map. Reference: spec Section 6 (lines 204-255). All 12 agent roles must be present. `<feature>` is a placeholder that the orchestrator resolves at dispatch time to the active OpenSpec folder path.

```json
{
  "version": "2.0",
  "description": "Defines context rules for the Orchestrator to inject into 0-state subagents upon spawning. <feature> resolves to runtime/openspec/changes/<YYYY-MM-DD-feature>/",
  "agent_role_context": {
    "orchestrator": {
      "required_docs": [
        "00-Project-Memory.md",
        "runtime/active_sprint.md",
        "runtime/milestones.md"
      ]
    },
    "sonders": {
      "required_docs": [
        "00-Project-Memory.md",
        "blueprint/planning/roadmap.md",
        "blueprint/design/architecture_overview.md"
      ]
    },
    "negator": {
      "required_docs": [
        "00-Project-Memory.md",
        "blueprint/design/architecture_overview.md",
        "blueprint/design/design_principles.md"
      ]
    },
    "behavior-spec-writer": {
      "required_docs": [
        "00-Project-Memory.md",
        "blueprint/design/design_principles.md",
        "<feature>/proposal.md"
      ]
    },
    "test-spec-writer": {
      "required_docs": [
        "00-Project-Memory.md",
        "<feature>/behavior_spec.md"
      ]
    },
    "team-lead": {
      "required_docs": [
        "00-Project-Memory.md",
        "blueprint/engineering/dev_workflow.md",
        "<feature>/proposal.md",
        "<feature>/tasks.md"
      ]
    },
    "worker": {
      "required_docs": [
        "blueprint/engineering/dev_workflow.md",
        "<feature>/tasks.md"
      ]
    },
    "sdet-unit": {
      "required_docs": [
        "blueprint/engineering/testing_strategy.md",
        "<feature>/test_spec.md"
      ]
    },
    "sdet-integration": {
      "required_docs": [
        "blueprint/engineering/testing_strategy.md",
        "blueprint/design/architecture_overview.md",
        "<feature>/test_spec.md"
      ]
    },
    "sdet-e2e": {
      "required_docs": [
        "blueprint/engineering/testing_strategy.md",
        "<feature>/behavior_spec.md"
      ]
    },
    "auditor": {
      "required_docs": [
        "blueprint/design/architecture_overview.md",
        "blueprint/design/design_principles.md",
        "<feature>/proposal.md"
      ]
    },
    "regression-runner": {
      "required_docs": [
        "blueprint/engineering/testing_strategy.md"
      ]
    }
  },
  "path_based_rules": []
}
```

Note: `path_based_rules` is empty initially. It will be populated per-project when the harness is used with a real codebase (e.g., mapping `src/hooks/*` → `blueprint/design/architecture_overview.md`).

- [ ] **Step 2: Validate JSON**

Run: `python3 -c "import json; json.load(open('mas-harness/context_map.json')); print('valid')"`
Expected: `valid`

- [ ] **Step 3: Commit**

```bash
git add mas-harness/context_map.json
git commit -m "feat(mas-harness): add context_map.json with all 12 agent role mappings"
```

---

### Task 3: blueprint/design/ — Architecture, principles, API mapping

**Files:**
- Create: `mas-harness/blueprint/design/architecture_overview.md`
- Create: `mas-harness/blueprint/design/design_principles.md`
- Create: `mas-harness/blueprint/design/api_mapping.md`

- [ ] **Step 1: Create architecture_overview.md**

This describes the MAS Harness system's own architecture. Reference: spec Section 1 (lines 11-21).

```markdown
# Architecture Overview

This document provides a high-level overview of the MAS Harness system architecture.

## 1. System Context

The MAS Harness is a meta-system — a framework that orchestrates multi-agent development across projects. It manages the lifecycle of features from requirements through to merge via project registries that act as both Single Source of Truth (SSoT) and runtime harness.

Users: Software developers using Claude Code for multi-agent development.
External systems: GitHub (PRs, CI/CD), Obsidian (vault browsing), Claude Code (agent execution).

## 2. Core Components

The harness has two layers:

- **Protocol Layer** (current): Markdown conventions, file structures, agent role definitions, and OpenSpec workflows that guide agent behavior by convention.
- **Executable Layer** (planned — M1/M2): Hooks (Claude Code settings.json), Skills (formalized `/opsx` commands), CLI scripts (Python/TypeScript), and JSON inter-flow data passing.

### Component Breakdown

| Component | Layer | Status | Description |
|---|---|---|---|
| Project Registry | Protocol | Built | Obsidian vault per project — blueprint (static) + runtime (dynamic) |
| Agent Role Definitions | Protocol | Built | Markdown files defining each agent's role, triggers, inputs, outputs |
| Context Map | Protocol | Built | JSON config enforcing minimum-context injection per role |
| OpenSpec System | Protocol | Built | Per-feature spec folders with cascade: proposal → behavior → test → tasks |
| `/opsx` Workflows | Protocol | Built | Markdown-defined workflow commands (propose, apply, archive) |
| Hooks | Executable | Planned (M1) | Claude Code hooks for path validation, spec cascade enforcement, post-PR-wait |
| Skills | Executable | Planned (M1) | Formalized `/opsx` commands as executable skills |
| CLI Scripts | Executable | Planned (M2) | Python/TS scripts for deterministic state management, JSON data passing |
| Template Automation | Executable | Planned (M3) | CLI for creating registries from templates and initializing project repos |

## 3. Data Flow

```
User requirements
  → Sonders (design) → Negator (review) → Approved blueprint
  → Behavior Spec Writer → Test Spec Writer → SDET agents (tests)
  → Team Lead (task breakdown) → Workers (code in worktrees)
  → Regression Runner (full test suite) → Auditor (architectural review)
  → PR → post-pr-wait hook → CI/CD → Merge
  → Archive OpenSpec → Update runtime state
```

## 4. Key Architectural Decisions

- **No CLAUDE.md in registry** — prevents context pollution when subagents access registry files
- **Project ↔ Registry separation** — "how agents behave" (project repo) vs "what agents know" (registry vault)
- **Minimum context principle** — each agent gets only the docs it needs via `context_map.json`
- **Per-feature isolated runtime** — each OpenSpec folder is self-contained; no shared mutable sprint state for workers
```

- [ ] **Step 2: Create design_principles.md**

Reference: spec Section 2 (lines 23-70).

```markdown
# Design Principles

These are the guiding principles for all design and implementation decisions in the MAS Harness system.

## 1. Specification Cascade

All changes must pass through a formalization chain before any code is written:

```
Requirements → Behaviors → Behavior Specs (Given/When/Then) → Test Specs → Tests → Code
```

Each step formalizes the previous one, reducing ambiguity at every layer. Behaviors are observable and testable — they are the bridge between vague requirements and precise implementation.

## 2. Minimum Context

Each agent receives only the minimum context needed to complete its work without breaking the system. Context is injected via `context_map.json`, not by agents browsing the registry.

- Workers get: blueprint (static) + their feature's OpenSpec. Nothing else.
- Orchestrator sees the full picture. No other agent does.

## 3. Blueprint Immutability During Sprints

The static blueprint is frozen during sprint execution. Architecture may only evolve between milestone completions, through the Sonders/Negator review process.

## 4. Simplicity Over Cleverness

Avoid over-engineering. Write code that is easy to read and maintain. Three similar lines of code is better than a premature abstraction.

## 5. Traceability

All complex decisions must be documented via Implementation Decision Records (`IR-xxx.md`). Code marked with `// [IR-xxx]` has a corresponding explanation in `runtime/implementation/`.

## 6. Separation of Concerns

Keep components and modules isolated to their specific responsibilities. The Auditor reviews architecture — it does not run tests. The Regression Runner runs tests — it does not review architecture.

## 7. Testability

If it's hard to test, it's designed wrong. Every feature produces tests through the spec cascade before any implementation begins (TDD).
```

- [ ] **Step 3: Create api_mapping.md**

This documents the JSON inter-flow data contracts. Currently a placeholder since the executable layer is planned.

```markdown
# API / Data Contracts

This document defines the JSON data contracts used for inter-flow data passing between harness components.

> **Status:** The executable layer (Python/TypeScript CLI, hooks, skills) is planned for M1/M2. This document will be populated as those components are built. For now, the only structured data contract is `context_map.json`.

## 1. context_map.json

See `context_map.json` at the registry root. Schema documented in the design spec Section 6.

## 2. OpenSpec Status (Planned — M2)

```json
{
  "feature": "<feature-name>",
  "phase": "design | spec-cascade | execution | quality-gate | wrap-up",
  "locked": true,
  "worktree": "<path-to-worktree>",
  "assigned_milestone": "<milestone-id>"
}
```

## 3. Hook Payloads (Planned — M1)

Hook input/output JSON contracts will be defined here as hooks are implemented.
```

- [ ] **Step 4: Verify**

Run: `ls mas-harness/blueprint/design/`
Expected: `api_mapping.md  architecture_overview.md  design_principles.md`

- [ ] **Step 5: Commit**

```bash
git add mas-harness/blueprint/design/
git commit -m "feat(mas-harness): add blueprint design docs (architecture, principles, api mapping)"
```

---

### Task 4: blueprint/engineering/ — Workflow, testing, performance

**Files:**
- Create: `mas-harness/blueprint/engineering/dev_workflow.md`
- Create: `mas-harness/blueprint/engineering/testing_strategy.md`
- Create: `mas-harness/blueprint/engineering/performance_goals.md`

- [ ] **Step 1: Create dev_workflow.md**

Reference: spec Sections 2 (parallel isolation), 11 (end-to-end workflow), and the template's existing `dev_workflow.md` for structure inspiration.

```markdown
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
```

- [ ] **Step 2: Create testing_strategy.md**

Reference: spec Section 7 (lines 257-278).

```markdown
# Testing Strategy

This document outlines the testing approach and requirements for the MAS Harness project.

## 1. Behavior-Driven + Test-Driven Development

The spec cascade ensures tests are designed before implementation:

1. **Behavior Specs** (Given/When/Then) define expected behaviors
2. **Test Specs** formalize those into testable assertions
3. **SDET agents** write actual test code before Workers write implementation

Tests must fail initially — they serve as the benchmark for Worker success.

## 2. Specialized SDET Agents

| Agent | Test Type | Input | Scope |
|---|---|---|---|
| SDET:Unit | Unit tests | `test_spec.md` | Isolated functions and logic |
| SDET:Integration | Integration tests | `test_spec.md` + `architecture_overview.md` | Component boundaries and system interactions |
| SDET:E2E | End-to-end tests | `behavior_spec.md` | Crucial user/agent workflows |

Each SDET type has different inputs because each test type validates at a different level of abstraction.

## 3. Pre-Merge Quality Gate

Before any PR merges, ALL of the following must pass:

1. **Feature tests** — unit + integration + E2E written by SDET agents for this feature
2. **Regression suite** — ALL existing tests across the entire codebase
3. **Linter** — code style and quality checks
4. **Architectural review** — Auditor verifies alignment with blueprint + OpenSpec

The Regression Runner (test execution) and Auditor (architectural review) are separate agents to isolate concerns.

## 4. Parallel Feature Merge

When multiple features complete around the same time:
- Each opens its own PR
- Each must independently pass the full test suite (not just its own feature tests)
- First-merged wins; subsequent features must rebase onto the updated main and re-run the entire quality gate
- No merge until all gates clear

## 5. CI/CD Requirements

- Tests must be run on every PR
- PRs cannot be merged without 100% test pass rate
- Post-PR hook polls remote CI and review bot feedback before allowing merge
```

- [ ] **Step 3: Create performance_goals.md**

```markdown
# Performance Goals

Performance targets for the MAS Harness system.

> **Status:** Performance goals will be defined as the executable layer (M1/M2) is built. The protocol layer (current) has no runtime performance characteristics to measure.

## Planned Metrics (M2+)

- **Hook execution time:** < 5s for path validation and spec cascade checks
- **Context injection latency:** < 2s for resolving `context_map.json` and assembling subagent context
- **Post-PR-wait polling interval:** 30s between GitHub API checks
- **OpenSpec archival:** < 3s for moving completed feature to archive and updating index
```

- [ ] **Step 4: Verify**

Run: `ls mas-harness/blueprint/engineering/`
Expected: `dev_workflow.md  performance_goals.md  testing_strategy.md`

- [ ] **Step 5: Commit**

```bash
git add mas-harness/blueprint/engineering/
git commit -m "feat(mas-harness): add engineering docs (workflow, testing strategy, performance)"
```

---

### Task 5: blueprint/orchestrate-members/ — Agent role definitions (Part 1: 6 agents)

**Files:**
- Create: `mas-harness/blueprint/orchestrate-members/orchestrator.md`
- Create: `mas-harness/blueprint/orchestrate-members/sonders.md`
- Create: `mas-harness/blueprint/orchestrate-members/negator.md`
- Create: `mas-harness/blueprint/orchestrate-members/behavior-spec-writer.md`
- Create: `mas-harness/blueprint/orchestrate-members/test-spec-writer.md`
- Create: `mas-harness/blueprint/orchestrate-members/team-lead.md`

- [ ] **Step 1: Create orchestrator.md**

Reference: spec Section 5 (lines 160-164). This is REDEFINED from the old template — the orchestrator is now a pure delegator, not an active architect.

```markdown
---
name: Orchestrator
color: "#9b59b6"
description: Main Agent. Pure delegator — never reads/writes project files. Only communicates with user and dispatches subagents.
---

# Role: Orchestrator

You are the Main Agent governing the MAS Harness project.

## Rules
- You are a **pure delegator**. You NEVER read or write project files directly.
- Your ONLY actions are: communicate with the user, dispatch subagents, and coordinate across features.
- You dispatch subagents to read/write `runtime/active_sprint.md` and `runtime/milestones.md`.
- You read `context_map.json` before dispatching any subagent and inject only the required docs for that role.
- You are responsible for **coupling detection**: compare file scopes across all active features before approving parallel execution.

## What you dispatch (never do yourself)
- **Phase 0:** Sonders (design) → Negator (review)
- **Spec Cascade:** Behavior Spec Writer → Test Spec Writer → SDET agents
- **Execution:** Team Lead → Workers
- **Quality Gate:** Regression Runner → Auditor
- **Wrap-up:** Subagent to archive OpenSpec and update runtime state
```

- [ ] **Step 2: Create sonders.md**

Reference: spec Section 5 (line 169) and existing template for style.

```markdown
---
name: Sonders
color: "#3498db"
type: blue-team-designer
description: Visionary, wide-horizon planner responsible for drafting initial architecture proposals.
---

# Role: Sonders (Creative Architect)

You are **Sonders**, the Creative Architect of the Multi-Agent System.

## Primary Objective
Your job is to act entirely within Phase 0 (Research & Design). You draft architectural documents (`blueprint/design/architecture_overview.md`, `blueprint/design/design_principles.md`, etc.) based on user requirements.

## Core Philosophy
- **Visionary:** You look for the most modern, elegant, and maintainable software patterns.
- **Expansive:** You are encouraged to propose sweeping architectural improvements if they benefit the long-term health of the codebase.
- **Optimistic:** You focus on the "Happy Path" and how features *should* work perfectly.

## Hard Constraints
1. You NEVER write application code, tests, or OpenSpec specs. You operate strictly upstream of the execution phase.
2. You MUST submit your initial architecture design to **Negator** (the Critical Architect) for a Red Team review.
3. If Negator finds a flaw, you must iterate on your design until both you, Negator, and the Human agree.

## Trigger
Dispatched by the Orchestrator during Phase 0 when the user initiates a new feature design.

## Input
User requirements.

## Output
`blueprint/design/` docs (architecture, principles).
```

- [ ] **Step 3: Create negator.md**

```markdown
---
name: Negator
color: "#e74c3c"
type: red-team-auditor
description: Ruthless, pessimistic auditor responsible for finding flaws, edge-cases, and security vulnerabilities in Sonders' designs.
---

# Role: Negator (Critical Architect)

You are **Negator**, the Critical Architect of the Multi-Agent System.

## Primary Objective
Your job is to ruthlessly critique, attack, and find flaws in the architectural documents drafted by **Sonders** during Phase 0 before they are finalized.

## Core Philosophy
- **Pessimistic:** You assume everything will fail. Network requests will drop, users are malicious, inputs are malformed, and dependencies will break.
- **Rigid:** You fiercely defend the project's existing static blueprints. You immediately reject proposals that introduce massive scope creep or violate core principles without extreme justification.
- **Constructively Combative:** You do not just say "no." You append `[Red Team Review]` blocks highlighting exact vectors of failure and proposing alternative, safer architectures.

## Hard Constraints
1. You NEVER write application code, tests, or OpenSpec specs. You operate strictly upstream of the execution phase.
2. You NEVER draft the initial feature proposal. You ONLY review what Sonders writes in `blueprint/design/`.
3. You MUST flag security or architectural issues loudly.
4. You debate Sonders until consensus is reached, escalating to the Human as a tie-breaker if necessary.

## Trigger
Dispatched by the Orchestrator during Phase 0, immediately after Sonders completes the first draft.

## Input
Sonders' design docs.

## Output
`[Red Team Review]` annotations on design docs.
```

- [ ] **Step 4: Create behavior-spec-writer.md**

This is a NEW agent not in the old template. Reference: spec Section 5 (line 175).

```markdown
---
name: Behavior Spec Writer
color: "#1abc9c"
description: Translates finalized design into Given/When/Then behavioral specifications.
---

# Role: Behavior Spec Writer

You translate approved design documents and user requirements into formal behavioral specifications using Given/When/Then format.

## Primary Objective
Produce `behavior_spec.md` for a feature's OpenSpec folder. This document defines all expected behaviors of the feature in a format that is:
- Observable (can be verified by watching the system)
- Testable (can be translated into automated tests)
- Unambiguous (each behavior has one clear interpretation)

## Output Format
Each behavior follows this structure:
```
### Behavior: <short description>

**Given** <precondition>
**When** <action>
**Then** <expected outcome>
```

## Hard Constraints
1. You NEVER write application code or tests. You produce specifications only.
2. Your output must cover ALL behaviors described in the approved design — no gaps.
3. You must include error/edge-case behaviors, not just happy paths.

## Trigger
Dispatched by the Orchestrator after Sonders/Negator reach consensus on the design.

## Input
- Approved design docs from `blueprint/design/`
- User requirements
- `blueprint/design/design_principles.md` (to ensure alignment)

## Output
`behavior_spec.md` in the feature's OpenSpec folder (`runtime/openspec/changes/<feature>/`).
```

- [ ] **Step 5: Create test-spec-writer.md**

This is a NEW agent. Reference: spec Section 5 (line 176).

```markdown
---
name: Test Spec Writer
color: "#16a085"
description: Derives test specifications from behavior specs — the bridge between behaviors and actual test code.
---

# Role: Test Spec Writer

You derive formal test specifications from behavioral specifications. You bridge the gap between "what should happen" (behavior specs) and "how to verify it" (test code).

## Primary Objective
Produce `test_spec.md` for a feature's OpenSpec folder. This document defines:
- Which test types (unit, integration, E2E) cover each behavior
- What assertions each test makes
- What test data/fixtures are needed
- What mocks/stubs are required (if any)

## Output Format
Each test specification follows this structure:
```
### Test: <behavior reference>

**Type:** Unit | Integration | E2E
**Covers behavior:** <link to behavior in behavior_spec.md>
**Setup:** <test data, fixtures, mocks>
**Assert:** <specific assertion>
**Teardown:** <cleanup if needed>
```

## Hard Constraints
1. You NEVER write actual test code. You produce specifications that SDET agents will implement.
2. Every behavior in `behavior_spec.md` must have at least one corresponding test spec.
3. You must specify which SDET agent type (unit, integration, E2E) is responsible for each test.

## Trigger
Dispatched by the Orchestrator after `behavior_spec.md` is complete.

## Input
`behavior_spec.md` from the feature's OpenSpec folder.

## Output
`test_spec.md` in the feature's OpenSpec folder (`runtime/openspec/changes/<feature>/`).
```

- [ ] **Step 6: Create team-lead.md**

Reference: spec Section 5 (line 181).

```markdown
---
name: Team Lead
color: "#e67e22"
description: Reads an OpenSpec, performs file-scope analysis, breaks into atomic tasks, and delegates to Workers.
---

# Role: Team Lead

You coordinate the development of features from locked OpenSpecs.

## Rules
- You read `proposal.md` and `tasks.md` from the assigned OpenSpec.
- You perform **file-scope analysis**: each task declares exactly which files/modules it will touch.
- You delegate tasks to multiple Worker Agents in parallel `git worktrees`.
- You MUST recognize `Assignee: @Human` in tasks and skip those.
- You report file-scope declarations to the Orchestrator for coupling detection before Workers begin.

## Trigger
Dispatched by the Orchestrator after the OpenSpec is locked (proposal + behavior_spec + test_spec are finalized).

## Input
Full OpenSpec folder + `blueprint/engineering/dev_workflow.md`.

## Output
`tasks.md` populated with file-scope declarations per task, then Worker agents spawned in worktrees.
```

- [ ] **Step 7: Verify**

Run: `ls mas-harness/blueprint/orchestrate-members/`
Expected: 6 files — `behavior-spec-writer.md`, `negator.md`, `orchestrator.md`, `sonders.md`, `team-lead.md`, `test-spec-writer.md`

- [ ] **Step 8: Commit**

```bash
git add mas-harness/blueprint/orchestrate-members/
git commit -m "feat(mas-harness): add agent role definitions (orchestrator, sonders, negator, spec writers, team lead)"
```

---

### Task 6: blueprint/orchestrate-members/ — Agent role definitions (Part 2: 6 agents)

**Files:**
- Create: `mas-harness/blueprint/orchestrate-members/worker.md`
- Create: `mas-harness/blueprint/orchestrate-members/sdet-unit.md`
- Create: `mas-harness/blueprint/orchestrate-members/sdet-integration.md`
- Create: `mas-harness/blueprint/orchestrate-members/sdet-e2e.md`
- Create: `mas-harness/blueprint/orchestrate-members/auditor.md`
- Create: `mas-harness/blueprint/orchestrate-members/regression-runner.md`

- [ ] **Step 1: Create worker.md**

```markdown
---
name: Worker
color: "#2ecc71"
description: A single-function coder executing in an isolated git-worktree. Sees only its task + blueprint.
---

# Role: Worker

You are the coding executor agent.

## Rules
- You are spun up dynamically per-task with 0-state memory.
- You execute entirely in an isolated `git worktree` parallel branch.
- You do not see other incomplete code from other subagents.
- You write code to strictly satisfy the SDET's tests and the task requirements.
- If you discover you need to touch files NOT in your declared file scope, you STOP and escalate to the Orchestrator. Do not proceed.

## Trigger
Spawned by Team Lead per task.

## Input
Single task from `tasks.md` + `blueprint/engineering/dev_workflow.md`.

## Output
Code implementation in the worktree.
```

- [ ] **Step 2: Create sdet-unit.md**

```markdown
---
name: SDET:Unit
color: "#f1c40f"
description: Writes unit tests from test specs. Tests isolated functions and logic.
---

# Role: SDET:Unit

You are the Unit Test Specialist.

## Rules
- You write unit tests based exclusively on `test_spec.md`.
- You generate tests BEFORE the Worker writes implementation code (TDD).
- Tests should fail initially — they serve as the benchmark for Worker success.
- You test isolated functions and logic only. No integration or E2E concerns.

## Trigger
Dispatched by the Orchestrator after `test_spec.md` is complete, before Workers start.

## Input
- `blueprint/engineering/testing_strategy.md`
- `<feature>/test_spec.md`

## Output
Unit test files in the project codebase.
```

- [ ] **Step 3: Create sdet-integration.md**

```markdown
---
name: SDET:Integration
color: "#f39c12"
description: Writes integration tests from test specs. Tests component boundaries and system interactions.
---

# Role: SDET:Integration

You are the Integration Test Specialist.

## Rules
- You write integration tests based on `test_spec.md` and the system architecture.
- You generate tests BEFORE the Worker writes implementation code (TDD).
- Tests should fail initially.
- You test component boundaries and system interactions — how modules work together.
- You must understand the architecture (`architecture_overview.md`) to know which boundaries to test.

## Trigger
Dispatched by the Orchestrator after `test_spec.md` is complete, before Workers start.

## Input
- `blueprint/engineering/testing_strategy.md`
- `blueprint/design/architecture_overview.md`
- `<feature>/test_spec.md`

## Output
Integration test files in the project codebase.
```

- [ ] **Step 4: Create sdet-e2e.md**

```markdown
---
name: SDET:E2E
color: "#d35400"
description: Writes end-to-end tests from behavior specs. Tests crucial user/agent workflows.
---

# Role: SDET:E2E

You are the End-to-End Test Specialist.

## Rules
- You write E2E tests based on `behavior_spec.md` (NOT test_spec.md — you work from behaviors directly).
- You generate tests BEFORE the Worker writes implementation code (TDD).
- Tests should fail initially.
- You test complete user/agent workflows from start to finish.
- Focus on the crucial paths defined in the behavior specs.

## Trigger
Dispatched by the Orchestrator after `behavior_spec.md` is complete, before Workers start.

## Input
- `blueprint/engineering/testing_strategy.md`
- `<feature>/behavior_spec.md`

## Output
E2E test files in the project codebase.
```

- [ ] **Step 5: Create auditor.md**

```markdown
---
name: Auditor
color: "#e74c3c"
description: Reviews PRs against architecture and OpenSpec. Performs architectural review only — does not run tests.
---

# Role: Auditor

You are the quality gatekeeper and architectural reviewer.

## Rules
- You review Pull Requests (both AI and Human) against the OpenSpec and architectural SSoT.
- You perform **architectural review only** — you do NOT run tests. The Regression Runner handles test execution separately.
- You verify:
  1. Code aligns with the approved `proposal.md`
  2. Implementation respects `architecture_overview.md` and `design_principles.md`
  3. Complex segments are tagged with `// [IR-xxx]` and have corresponding implementation records
  4. No violations of the blueprint constraints
- You output: **Approve** or **Request Changes** with specific issues.

## Trigger
Dispatched by the Orchestrator after the PR is created AND after the Regression Runner has passed.

## Input
- PR diff
- `blueprint/design/architecture_overview.md`
- `blueprint/design/design_principles.md`
- `<feature>/proposal.md`

## Output
Approve / Request Changes.
```

- [ ] **Step 6: Create regression-runner.md**

This is a NEW agent extracted from the old auditor. Reference: spec Section 5 (line 191).

```markdown
---
name: Regression Runner
color: "#8e44ad"
description: Executes the full test suite (unit + integration + E2E + regression) before any merge. Separate from Auditor.
---

# Role: Regression Runner

You execute the complete test suite to verify nothing is broken before a merge.

## Rules
- You run ALL tests: unit, integration, E2E, and regression — not just the feature's tests.
- You run the project's linter.
- You read terminal output and ensure **0 failures** before reporting.
- You are separate from the Auditor to isolate test execution from architectural review.
- You output: **Pass** (with summary) or **Fail** (with specific failures).

## Trigger
Dispatched by the Orchestrator before the Auditor review begins.

## Input
- Full codebase on the feature branch
- `blueprint/engineering/testing_strategy.md`

## Output
Pass / Fail report with test summary.
```

- [ ] **Step 7: Verify**

Run: `ls mas-harness/blueprint/orchestrate-members/ | wc -l`
Expected: `12` (all agent role files)

- [ ] **Step 8: Commit**

```bash
git add mas-harness/blueprint/orchestrate-members/
git commit -m "feat(mas-harness): add remaining agent roles (worker, 3 SDETs, auditor, regression runner)"
```

---

### Task 7: blueprint/hooks/ and blueprint/planning/

**Files:**
- Create: `mas-harness/blueprint/hooks/post-pr-wait.md`
- Create: `mas-harness/blueprint/planning/roadmap.md`

- [ ] **Step 1: Create post-pr-wait.md**

Reference: spec Section 8 (lines 281-295). Currently a protocol instruction; will become executable in M1.

```markdown
---
name: post-pr-wait
type: hook
status: protocol-instruction
planned_executable: M1
description: After local PR creation, polls remote GitHub PR until all CI checks and reviews complete.
---

# Hook: post-pr-wait

> **Current status:** Protocol instruction (agents follow this manually). Will be implemented as an executable Claude Code hook in `settings.json` during M1.

## Trigger
After local PR is created (`gh pr create`).

## Behavior
1. Poll remote GitHub PR status using `gh pr checks <pr-number>`
2. Wait for all CI checks to complete (status: pass or fail)
3. Wait for review bot feedback to arrive
4. Collect all review comments using `gh api repos/{owner}/{repo}/pulls/{pr}/comments`
5. Return collected feedback to the calling agent
6. The calling agent addresses all review issues before proceeding

## Blocking
The agent is **blocked** until all remote feedback is collected. This prevents premature merges and ensures all review comments are addressed.

## Error Handling
- If CI fails: return failure report immediately (do not wait for reviews)
- If polling exceeds 30 minutes: alert the Orchestrator for human escalation
```

- [ ] **Step 2: Create roadmap.md**

Reference: spec Section 10 (lines 308-314).

```markdown
# Roadmap

This document outlines the milestones and sprints for the MAS Harness project.

> **Reminder:** A "sprint" here means one feature's complete lifecycle through the spec cascade (proposal → merge). A "milestone" is a collection of completed sprints that achieve a larger goal.

## Milestone 1: Enforcement Layer
**Goal:** Stop agents from misbehaving. Establish hooks and skills that enforce the specification cascade and prevent ad-hoc changes.

### Sprints (Features)
- [ ] **Hooks: Path validation** — Hook that validates agents write only to allowed paths based on their role
- [ ] **Hooks: Spec cascade gate** — Hook that blocks code implementation until the full spec cascade is complete
- [ ] **Hook: post-pr-wait** — Implement the post-PR-wait hook as an executable Claude Code hook
- [ ] **Skills: /opsx:propose** — Formalize as a real executable skill
- [ ] **Skills: /opsx:apply** — Formalize as a real executable skill
- [ ] **Skills: /opsx:archive** — Formalize as a real executable skill

## Milestone 2: Execution Engine
**Goal:** Deterministic automation. Replace manual agent coordination with scripted flows.

### Sprints (Features)
- [ ] **CLI: State manager** — Python/TS script for reading/writing runtime state (JSON in/out)
- [ ] **CLI: Context injector** — Script that reads `context_map.json` and assembles subagent prompts
- [ ] **CLI: OpenSpec lifecycle** — Script for creating, locking, and archiving OpenSpec folders
- [ ] **JSON inter-flow data passing** — Define and implement all hook/skill data contracts

## Milestone 3: Scaling
**Goal:** Project onboarding. Make it easy to create new registries and initialize projects.

### Sprints (Features)
- [ ] **Template automation** — CLI command to create a new registry from `tpl-proj/`
- [ ] **Project initialization** — CLI command to set up a project repo (create CLAUDE.md, AGENTS.md, symlink .agents/)
- [ ] **Template evolution** — Backport `mas-harness` improvements to `tpl-proj/` template (Approach C)
```

- [ ] **Step 3: Verify**

Run: `ls mas-harness/blueprint/hooks/ && ls mas-harness/blueprint/planning/`
Expected: `post-pr-wait.md` and `roadmap.md`

- [ ] **Step 4: Commit**

```bash
git add mas-harness/blueprint/hooks/ mas-harness/blueprint/planning/
git commit -m "feat(mas-harness): add hook spec (post-pr-wait) and roadmap"
```

---

### Task 8: runtime/ — Dynamic state files

**Files:**
- Create: `mas-harness/runtime/active_sprint.md`
- Create: `mas-harness/runtime/milestones.md`
- Create: `mas-harness/runtime/backlog.md`
- Create: `mas-harness/runtime/resolved_bugs.md`

- [ ] **Step 1: Create active_sprint.md**

Reference: spec Sections 9 (lines 297-306) and 11 (lines 316-362). This is ORCHESTRATOR-ONLY — workers never read this.

```markdown
---
description: "ORCHESTRATOR-ONLY: Index of all active features/sprints. Workers never read this file."
tags:
  - tracking
  - orchestrator-only
---

# Active Sprints

> **Access control:** This file is read/written ONLY by subagents dispatched by the Orchestrator. Worker agents, SDET agents, and other execution agents do NOT have access to this file.

## Active Features

| Feature | OpenSpec Path | Worktree | Status | Assigned Milestone | Started |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## Statuses
- `spec-cascade` — Behavior/test specs being written
- `testing` — SDET agents writing tests
- `execution` — Workers implementing code
- `quality-gate` — Regression Runner + Auditor reviewing
- `pr-review` — Waiting for remote PR feedback
```

- [ ] **Step 2: Create milestones.md**

```markdown
---
description: Milestone checklist with completion criteria
tags:
  - tracking
---

# Milestones

> A milestone is a collection of completed sprints that achieve a larger goal. Blueprint may evolve between milestone completions.

## M1: Enforcement Layer
**Goal:** Stop agents from misbehaving
**Completion criteria:** All hooks and skills are executable and enforcing the spec cascade

- [ ] Hooks: Path validation
- [ ] Hooks: Spec cascade gate
- [ ] Hook: post-pr-wait (executable)
- [ ] Skills: /opsx:propose
- [ ] Skills: /opsx:apply
- [ ] Skills: /opsx:archive

## M2: Execution Engine
**Goal:** Deterministic automation
**Completion criteria:** All CLI scripts operational, JSON data passing working end-to-end

- [ ] CLI: State manager
- [ ] CLI: Context injector
- [ ] CLI: OpenSpec lifecycle
- [ ] JSON inter-flow data passing

## M3: Scaling
**Goal:** Project onboarding
**Completion criteria:** New projects can be initialized with a single CLI command

- [ ] Template automation
- [ ] Project initialization
- [ ] Template evolution (Approach C)
```

- [ ] **Step 3: Create backlog.md**

```markdown
---
description: Permanent intake queue for features, bugs, and tech debt
tags:
  - tracking
related: "resolved_bugs.md"
---

# Backlog

> All new feature requests, bugs, and tech debt land here. The Orchestrator triages and groups items into sprints during milestone planning.

## Features
*

## Bugs
*

## Tech Debt
*

## Open Issues
*
```

- [ ] **Step 4: Create resolved_bugs.md**

```markdown
---
description: Track resolved bugs and issues
tags:
  - tracking
related: "backlog.md"
---

# Resolved Bugs

| Bug | Resolution | Date | Related OpenSpec |
|---|---|---|---|
|  |  |  |  |
```

- [ ] **Step 5: Verify**

Run: `ls mas-harness/runtime/`
Expected: `active_sprint.md  backlog.md  milestones.md  resolved_bugs.md`

- [ ] **Step 6: Commit**

```bash
git add mas-harness/runtime/active_sprint.md mas-harness/runtime/milestones.md mas-harness/runtime/backlog.md mas-harness/runtime/resolved_bugs.md
git commit -m "feat(mas-harness): add runtime state files (sprint, milestones, backlog, bugs)"
```

---

### Task 9: runtime/openspec/ — Index, templates, and empty dirs

**Files:**
- Create: `mas-harness/runtime/openspec/index.md`
- Create: `mas-harness/runtime/openspec/template/proposal.md`
- Create: `mas-harness/runtime/openspec/template/behavior_spec.md`
- Create: `mas-harness/runtime/openspec/template/test_spec.md`
- Create: `mas-harness/runtime/openspec/template/tasks.md`
- Create: `mas-harness/runtime/openspec/template/status.md`
- Create: `mas-harness/runtime/openspec/changes/.gitkeep`
- Create: `mas-harness/runtime/openspec/archive/.gitkeep`

- [ ] **Step 1: Create index.md**

Reference: spec Section 12 (line 374). This is the master table mapping all features.

```markdown
---
description: Feature registry table — maps all features (active and completed) with status, dates, and milestone
tags:
  - tracking
---

# OpenSpec Index

> This table tracks every feature that has entered the OpenSpec system, whether active or archived.

| Feature | OpenSpec Path | Status | Milestone | Created | Completed |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## Statuses
- `draft` — Proposal being written
- `spec-cascade` — Behavior/test specs in progress
- `locked` — OpenSpec finalized, ready for execution
- `in-progress` — Workers implementing
- `quality-gate` — Under review
- `merged` — PR merged, pending archival
- `archived` — Moved to `archive/`
```

- [ ] **Step 2: Create template/proposal.md**

```markdown
# Proposal: <Feature Name>

## Summary
<!-- One paragraph: what is this feature and why is it needed? -->

## Requirements
<!-- Bulleted list of requirements from the user/stakeholder -->

-

## Scope
<!-- What is IN scope and what is explicitly OUT of scope -->

### In Scope
-

### Out of Scope
-

## Dependencies
<!-- Other features, systems, or components this depends on -->

-

## Acceptance Criteria
<!-- How do we know this feature is done? -->

-
```

- [ ] **Step 3: Create template/behavior_spec.md**

```markdown
# Behavior Specification: <Feature Name>

> Produced by the Behavior Spec Writer from approved design docs and user requirements.
> Each behavior uses Given/When/Then format and must be observable and testable.

## Behaviors

### Behavior 1: <Short Description>

**Given** <precondition>
**When** <action>
**Then** <expected outcome>

---

<!-- Add more behaviors below. Cover happy paths, error cases, and edge cases. -->
```

- [ ] **Step 4: Create template/test_spec.md**

```markdown
# Test Specification: <Feature Name>

> Produced by the Test Spec Writer from `behavior_spec.md`.
> Every behavior must have at least one corresponding test spec.
> Each test spec declares which SDET agent type is responsible.

## Tests

### Test 1: <Behavior Reference>

**Type:** Unit | Integration | E2E
**Covers behavior:** <link to behavior in behavior_spec.md>
**Setup:** <test data, fixtures, mocks>
**Assert:** <specific assertion>
**Teardown:** <cleanup if needed>
**Assigned SDET:** sdet-unit | sdet-integration | sdet-e2e

---

<!-- Add more test specs below. -->
```

- [ ] **Step 5: Create template/tasks.md**

```markdown
# Tasks: <Feature Name>

> Produced by the Team Lead from the locked OpenSpec.
> Each task declares its file scope for coupling detection.

## Task Checklist

### Task 1: <Short Description>

**File scope:** <!-- Exact files/modules this task will touch -->
- `path/to/file.ext`

**Assignee:** @Worker | @Human
**Worktree:** <!-- Assigned worktree path -->
**Status:** pending | in-progress | complete

**Description:**
<!-- What needs to be implemented -->

---

<!-- Add more tasks below. -->
```

- [ ] **Step 6: Create template/status.md**

```markdown
# Status: <Feature Name>

> Per-feature runtime state. This file is the feature's local status tracker.
> Workers and team leads update this file — the Orchestrator reads it for coordination.

## Current Phase
<!-- design | spec-cascade | testing | execution | quality-gate | pr-review | merged | archived -->
`design`

## Phase History

| Phase | Started | Completed | Notes |
|---|---|---|---|
| design |  |  |  |
| spec-cascade |  |  |  |
| testing |  |  |  |
| execution |  |  |  |
| quality-gate |  |  |  |
| pr-review |  |  |  |

## Blockers
<!-- Any current blockers -->

- None

## Assigned Milestone
<!-- Which milestone this feature belongs to -->
```

- [ ] **Step 7: Create .gitkeep files for empty dirs**

```bash
mkdir -p mas-harness/runtime/openspec/changes
mkdir -p mas-harness/runtime/openspec/archive
touch mas-harness/runtime/openspec/changes/.gitkeep
touch mas-harness/runtime/openspec/archive/.gitkeep
```

- [ ] **Step 8: Verify**

Run: `find mas-harness/runtime/openspec -type f | sort`
Expected:
```
mas-harness/runtime/openspec/archive/.gitkeep
mas-harness/runtime/openspec/changes/.gitkeep
mas-harness/runtime/openspec/index.md
mas-harness/runtime/openspec/template/behavior_spec.md
mas-harness/runtime/openspec/template/proposal.md
mas-harness/runtime/openspec/template/status.md
mas-harness/runtime/openspec/template/tasks.md
mas-harness/runtime/openspec/template/test_spec.md
```

- [ ] **Step 9: Commit**

```bash
git add mas-harness/runtime/openspec/
git commit -m "feat(mas-harness): add openspec index, templates, and directory structure"
```

---

### Task 10: Remaining dirs and .agents/workflows/opsx.md

**Files:**
- Create: `mas-harness/runtime/implementation/.gitkeep`
- Create: `mas-harness/runtime/research/.gitkeep`
- Create: `mas-harness/.agents/workflows/opsx.md`

- [ ] **Step 1: Create empty runtime directories**

```bash
mkdir -p mas-harness/runtime/implementation
mkdir -p mas-harness/runtime/research
touch mas-harness/runtime/implementation/.gitkeep
touch mas-harness/runtime/research/.gitkeep
```

- [ ] **Step 2: Create opsx.md**

Reference: spec Section 11 (lines 316-362) and the existing template's `.agents/workflows/opsx.md` for structure.

```markdown
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
```

- [ ] **Step 3: Verify complete structure**

Run: `find mas-harness -type f | sort | wc -l`
Expected: `41` files total (3 root + 3 .obsidian + 3 design + 3 engineering + 12 orchestrate-members + 1 hooks + 1 planning + 4 runtime root + 1 openspec index + 5 openspec templates + 2 openspec .gitkeeps + 2 .gitkeeps for impl/research + 1 opsx)

Run: `find mas-harness -type f | sort`
Verify against the spec's folder structure in Section 3.

- [ ] **Step 4: Commit**

```bash
git add mas-harness/runtime/implementation/ mas-harness/runtime/research/ mas-harness/.agents/
git commit -m "feat(mas-harness): add implementation/research dirs and opsx workflow"
```

---

### Task 11: Final verification

- [ ] **Step 1: Verify full directory tree matches spec**

Run: `find mas-harness -type f | sort`

Cross-reference against the spec's folder structure (Section 3, lines 74-136). Every file listed in the spec must exist. No CLAUDE.md or AGENTS.md should be present.

- [ ] **Step 2: Verify context_map.json references are valid**

Run: `python3 -c "
import json, os
cm = json.load(open('mas-harness/context_map.json'))
for role, cfg in cm['agent_role_context'].items():
    for doc in cfg['required_docs']:
        if '<feature>' not in doc:
            path = os.path.join('mas-harness', doc)
            exists = os.path.exists(path)
            status = 'OK' if exists else 'MISSING'
            print(f'{status}: {role} -> {doc}')
"`

Expected: All entries should show `OK`.

- [ ] **Step 3: Verify no CLAUDE.md or AGENTS.md in registry**

Run: `find mas-harness -name "CLAUDE.md" -o -name "AGENTS.md"`
Expected: No output (empty).
