# SSoT Registries

The Single Source of Truth (SSoT) registry is the central knowledge store for the omni system. Every agent's context comes from this registry -- agents do not browse the filesystem independently.

## Registry Location

The registry path is configured in `.harness.json` at the project root:

```json
{
  "registry_path": "regs/omni-regs/ssot",
  "cli_path": "tpls/cli",
  "version": "2.0.0"
}
```

Agents read `.harness.json` first to locate the SSoT, then consult the registry for all project context.

## Blueprint vs Runtime

The registry is divided into two sections with fundamentally different access patterns.

### Blueprint (Static)

Located under `regs/omni-regs/ssot/blueprint/`. These folders define HOW the system works and WHAT it is supposed to be. They are **read-only during sprints**.

| Path | Contents |
|---|---|
| `blueprint/design/architecture_overview.md` | System architecture |
| `blueprint/design/design_principles.md` | Design constraints and guidelines |
| `blueprint/design/api_mapping.md` | API and data contracts |
| `blueprint/engineering/dev_workflow.md` | Engineering workflow procedures |
| `blueprint/engineering/testing_strategy.md` | Testing approach and conventions |
| `blueprint/engineering/performance_goals.md` | Performance targets |
| `blueprint/orchestrate-members/` | Agent role definitions (12 roles) |
| `blueprint/hooks/` | Hook specifications |
| `blueprint/planning/roadmap.md` | Phase roadmap |

### Runtime (Dynamic)

Located under `regs/omni-regs/ssot/runtime/`. These folders track live execution, progress, and active context. Updated by dispatched subagents during sprints.

| Path | Contents |
|---|---|
| `runtime/active_sprint.md` | Current sprint state (orchestrator-only writes) |
| `runtime/milestones.md` | Milestone tracking |
| `runtime/backlog.md` | Backlog of upcoming work |
| `runtime/openspec/index.md` | Index of all features |
| `runtime/openspec/changes/` | Active feature specs (proposals, behavior specs, test specs) |
| `runtime/openspec/archive/` | Completed feature specs |
| `runtime/implementation/` | Implementation records |
| `runtime/resolved_bugs.md` | Log of resolved bugs |
| `runtime/research/` | Scratchpad for research notes |

## Implementation Record Index

`regs/omni-regs/ssot/IR_INDEX.md` lives at the SSoT root (not inside `runtime/implementation/`). It serves as the top-level index of all implementation records. Agents consult this file to locate implementation details for completed features.

## Context Map

`regs/omni-regs/ssot/context_map.json` defines which documents each agent role receives when spawned. The orchestrator reads this before dispatching any subagent and injects only the required docs for that role.

Example entries:

```json
{
  "orchestrator": {
    "required_docs": [
      "00-Project-Memory.md",
      "runtime/active_sprint.md",
      "runtime/milestones.md"
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
  }
}
```

The `<feature>` placeholder resolves to `runtime/openspec/changes/<YYYY-MM-DD-feature>/` at dispatch time. This means each subagent only sees documents relevant to its role and the specific feature it is working on.

## The `.agents` Symlink

The `.agents` symlink at the project root points to `regs/omni-regs/ssot/blueprint/orchestrate-members/`. This provides a convenient shortcut for agents to locate their role definitions without knowing the full registry path.

```
.agents -> regs/omni-regs/ssot/blueprint/orchestrate-members/
```

## Project Memory

`regs/omni-regs/ssot/00-Project-Memory.md` is the root document that describes the SSoT routing. It defines:

- The context protocol (how agents receive documents)
- The full SSoT directory structure (blueprint and runtime sections)
- Project-level definitions (sprint, milestone)

This document is included in the `required_docs` for most agent roles.
