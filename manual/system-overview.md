# System Overview

## What is omni?

omni is a Multi-Agent System (MAS) that orchestrates specialized AI agents to produce software. It enforces structure through a mandatory spec cascade, strict role boundaries, and an automated self-evolution loop that improves its own templates over time.

The system operates on two levels:

1. **Feature development** -- The orchestrator delegates work to subagents (spec writers, testers, workers) who follow a strict cascade from proposal through code.
2. **Self-evolution** -- An evaluation framework scores the system's output, and an evolution loop iteratively mutates and selects better templates.

## Core Concepts

### Orchestrator + Subagent Delegation

The orchestrator agent role is a pure delegator for project feature files -- it never reads or writes feature code, specs, or test files directly, delegating all such work to subagents. However, the orchestrator runtime modules (`loop.py`, `opsx.py`, `run_loop.py`) do perform direct I/O on manifest and state files (e.g., `eval-loop/manifest.json`) to manage evolution loop state.

The orchestrator agent:

- Communicates with the user
- Dispatches subagents with specific roles and injected context
- Coordinates across features and detects file-scope coupling

Each subagent is spawned with 0-state memory and receives only the documents specified in `context_map.json` for its role. See [Agent Roles](agent-roles.md) for the full list.

### Single Source of Truth (SSoT) Registry

All project context lives in the SSoT registry at `regs/omni-regs/ssot/`. This is split into:

- **Blueprint** (static) -- Architecture, design principles, engineering workflow, agent role definitions. Read-only during sprints.
- **Runtime** (dynamic) -- Active sprints, milestones, backlog, feature specs, implementation records. Updated by subagents during sprints.

See [SSoT Registries](registries.md) for details.

### Spec Cascade

Every feature must pass through a strict sequence before code is written:

```
proposal -> behavior_spec -> test_spec -> tests -> code
```

No step can be skipped. Tests are written before implementation code (TDD). See [Spec Cascade](spec-cascade.md) for the full workflow.

### Self-Evolution Loop

The system evaluates its own output against 48 yes/no questions across 8 categories. Templates are mutated, tested against a reference project, scored, and either promoted or rejected. The loop advances through three tiers of increasing difficulty (seed, tier-2, tier-3). See [Evolution Loop](evolution-loop.md) for the phase cycle.

## Project Definitions

- **Sprint**: One feature's complete lifecycle through the spec cascade (proposal through merge). This is NOT a time-boxed sprint.
- **Milestone**: A collection of completed sprints that achieve a larger goal.

## Key Files

| File | Purpose |
|---|---|
| `.harness.json` | Points to registry path (`regs/omni-regs/ssot`) and CLI path (`tpls/cli`) |
| `CLAUDE.md` | Top-level instructions injected into every agent session |
| `.agents` | Symlink to `regs/omni-regs/ssot/blueprint/orchestrate-members/` |
| `eval-loop/manifest.json` | Evolution loop state (phase, tier, candidates, scores) |

## How Everything Connects

```
User
  |
  v
Orchestrator (main agent, pure delegator)
  |
  +-- reads context_map.json to decide what docs each subagent needs
  |
  +-- dispatches subagents:
  |     Sonders (design) -> Negator (review)
  |     Behavior Spec Writer -> Test Spec Writer -> SDETs
  |     Team Lead -> Workers
  |     Regression Runner -> Auditor
  |
  +-- evolution loop (automated):
        prepare -> mutate -> execute -> verify -> decide
        |
        uses eval/ framework (criteria, scripts, gates)
        mutates tpls/ (templates)
        tracks state in eval-loop/manifest.json
```
