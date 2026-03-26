# MAS Harness

A multi-agent development harness that orchestrates AI coding agents via project registries, enforcement hooks, and a strict spec-first workflow.

## What is this?

MAS Harness is a meta-framework for multi-agent software development. It uses:

- **Project registries** (Obsidian vaults as Single Source of Truth) to track specs, plans, and agent state
- **Enforcement hooks** (pre-tool-use / post-tool-use) that block agents from writing code before specs are complete, and from touching files outside their role's scope
- **The OpenSpec workflow** — a spec cascade that forces requirements → behaviors → specs → tests → code ordering
- **12 agent role definitions** with distinct responsibilities and scope boundaries

## Quick Start

### Onboard a new project

```bash
# One command to bootstrap
python harness-cli/setup/bootstrap.py \
  --name my-project \
  --project ~/repos/my-project

# Then start Claude Code in the project
cd ~/repos/my-project && claude
```

This creates a project registry (copied from `mas-harness/`), installs hooks into the target project, and wires up the context injector.

## Architecture

```
proj-regs/
├── mas-harness/          # Template registry (Obsidian vault)
│   ├── blueprint/        # Static — frozen during sprints
│   └── runtime/          # Dynamic — updated during agent work
├── harness-cli/          # Executable layer
│   ├── hooks/            # Enforcement hooks
│   ├── context/          # Context injection
│   └── setup/            # Bootstrap + init tooling
├── mas-harness-regs/     # Registry for this project's own development
├── reg-tpls/             # Legacy templates (superseded by mas-harness/)
└── docs/                 # Specs and plans
```

### `mas-harness/`

The template Obsidian vault. Contains:

- `blueprint/` — Static documents (architecture, role definitions, conventions). Frozen during a sprint; evolves only between milestones.
- `runtime/` — Dynamic documents (active sprint state, agent assignments, feature tracking).
- 12 agent role definitions with scope rules and behavioral contracts.

New projects get a copy of this vault as their registry.

### `harness-cli/`

The executable layer. All tooling lives here.

| Path | Purpose |
|------|---------|
| `hooks/path_validator.py` | Blocks writes outside a role's allowed file scope |
| `hooks/spec_cascade_gate.py` | Blocks code from being written before specs are complete |
| `hooks/post_pr_wait.ts` | Polls GitHub PR for CI status and required reviews |
| `context/inject.py` | Assembles minimum-context prompts per role |
| `setup/bootstrap.py` | One-command project onboarding |
| `setup/init_project.py` | Project initialization (used by bootstrap) |

## How it Works

### The Spec Cascade

Every feature must travel through this chain before a line of implementation code is written:

```
Requirements
    → Behaviors
    → Behavior Specs (Given / When / Then)
    → Test Specs
    → Tests
    → Code
```

`spec_cascade_gate.py` enforces this order. If the current stage is incomplete, the hook blocks the next stage from starting. Agents cannot skip ahead.

### Hook enforcement

`path_validator.py` reads the active role from the branch name (`feat/<feature>/<role>[-<instance>]`) and rejects any write to a path outside that role's declared scope. This prevents roles from accidentally (or deliberately) modifying files they do not own.

### Context injection

`inject.py` reads the registry and assembles a minimal, role-scoped prompt for a subagent. Only the documents relevant to that role and the current feature are included — avoiding context bloat across large registries.

## Agent Roles

12 roles, each with a distinct purpose and file-scope boundary:

| Role | Responsibility |
|------|---------------|
| `orchestrator` | Pure delegator — assigns work, never writes code |
| `sonders` | Creative architect — explores solution space, challenges assumptions |
| `negator` | Red-team critic — finds flaws before they become bugs |
| `behavior-spec-writer` | Writes Given/When/Then behavior specs |
| `test-spec-writer` | Writes test specs from behavior specs |
| `team-lead` | Coordinates implementation within a feature |
| `worker` | Writes implementation code |
| `sdet-unit` | Writes and runs unit tests |
| `sdet-integration` | Writes and runs integration tests |
| `sdet-e2e` | Writes and runs end-to-end tests |
| `auditor` | Reviews code and specs for compliance |
| `regression-runner` | Runs regression suites, reports results |

## Key Concepts

**Sprint** — One feature's complete lifecycle (requirements through deployed code). Not time-boxed.

**Milestone** — A collection of sprints. Blueprint documents evolve between milestones, not within them.

**Blueprint vs. Runtime** — Blueprint is frozen during a sprint. Agents read it but cannot modify it. Runtime documents are the live working state.

**No CLAUDE.md in registries** — Registries do not contain `CLAUDE.md` or `AGENTS.md`. This prevents the registry content from being auto-loaded as agent instructions, which would pollute the context of every agent that opens the project.

**Branch convention** — `feat/<feature>/<role>[-<instance>]`. The hook reads this to determine scope. Example: `feat/auth/worker-1`.

## CLI Reference

### `bootstrap.py`

Creates a registry and initializes a project in one step.

```
python harness-cli/setup/bootstrap.py \
  --name <name> \
  --project <path> \
  [--registry-dir <path>]
```

| Argument | Description |
|----------|-------------|
| `--name` | Registry name (used as the vault directory name) |
| `--project` | Absolute path to the target project |
| `--registry-dir` | Where to create the registry (default: current dir) |

### `init_project.py`

Initializes an existing project against an existing registry.

```
python harness-cli/setup/init_project.py \
  --project <path> \
  --registry <path>
```

### `inject.py`

Assembles a role-scoped context prompt for a subagent.

```
python harness-cli/context/inject.py \
  --role <role> \
  [--feature <feature>] \
  [--project <path>] \
  [--format json|text]
```

## Testing

```bash
cd harness-cli

# Python tests (128 tests)
python -m pytest -v

# TypeScript tests (8 tests)
npx vitest run
```

## Specs and Plans

Located in `docs/superpowers/specs/` and `docs/superpowers/plans/`.
