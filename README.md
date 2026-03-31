# omni

A Multi-Agent System (MAS) with self-evolution capability. omni orchestrates specialized AI agents through a structured spec-first workflow, enforcing quality via role boundaries, a spec cascade, and an automated evaluation loop that iteratively improves the system's own templates.

## Project Structure

```
omni/
├── eval/          # Evaluation framework (criteria, gates, scripts, tiers, pools) — FROZEN
├── eval-loop/     # Evolution loop engine (loop, dispatch, opsx CLI, manifest)
├── manual/        # Comprehensive system documentation (8 pages)
├── regs/          # Registries (omni-regs SSoT, test-regs)
├── tpls/          # Templates (snapshots, CLI tools, hooks)
├── docs/          # Historical planning docs and design specs
├── .harness.json  # Harness config (registry_path, cli_path)
├── .agents        # Symlink to agent role definitions
└── CLAUDE.md      # MAS agent instructions
```

## Documentation

The `manual/` directory contains the full system documentation. Start with the system overview for the big picture, then follow links to specific topics.

| Page | Description |
|------|-------------|
| [System Overview](manual/system-overview.md) | Architecture, delegation model, and core concepts |
| [SSoT Registries](manual/registries.md) | Single Source of Truth: blueprint vs runtime, context map, harness config |
| [Templates](manual/templates.md) | The `tpls/` subsystem: snapshots, CLI tools, hooks, snapshot management |
| [Evaluation Framework](manual/eval-framework.md) | Criteria, tier progression, check scripts, gates, FROZEN.lock integrity |
| [Evolution Loop](manual/evolution-loop.md) | The 5-phase cycle: prepare, mutate, execute, verify, decide |
| [Eval-Loop Guide](manual/eval-loop-guide.md) | Using `opsx.py` CLI commands and running the evolution loop |
| [Agent Roles](manual/agent-roles.md) | All 12 agent roles: orchestrator, team-lead, worker, spec writers, SDETs, and more |
| [Spec Cascade](manual/spec-cascade.md) | The mandatory workflow: proposal, behavior spec, test spec, tests, code |

## Quick Start

Bootstrap a new project with a single command:

```bash
python tpls/snapshots/candidate-0/cli/setup/bootstrap.py \
  --name my-project \
  --project ~/repos/my-project \
  --registry-dir ./regs
```

| Argument | Description |
|----------|-------------|
| `--name` | Registry name (used as the folder name, suffixed with `-regs`) |
| `--project` | Path to the target project repo (must be an existing git repository) |
| `--registry-dir` | Where to create the registry (default: `regs/` at the repo root) |

This creates a project registry under `regs/<name>-regs/` (with `ssot/` and `cli/` subdirectories), installs hooks into the target project, and wires up the harness config.

## Key Concepts

**Sprint** -- One feature's complete lifecycle through the spec cascade (proposal through merge). Not time-boxed.

**Milestone** -- A collection of completed sprints. Blueprint documents evolve between milestones, not within them.

**Blueprint vs Runtime** -- Blueprint is frozen during a sprint. Agents read it but cannot modify it. Runtime documents are the live working state.

**Branch convention** -- `feat/<feature>/<role>[-<instance>]`. Hooks read the branch name to determine role scope. Example: `feat/auth/worker-1`.

## Agent Roles

12 roles, each with a distinct purpose and file-scope boundary:

| Role | Responsibility |
|------|---------------|
| `orchestrator` | Pure delegator -- assigns work, never writes code |
| `sonders` | Creative architect -- explores solution space, challenges assumptions |
| `negator` | Red-team critic -- finds flaws before they become bugs |
| `behavior-spec-writer` | Writes Given/When/Then behavior specs |
| `test-spec-writer` | Writes test specs from behavior specs |
| `team-lead` | Coordinates implementation within a feature |
| `worker` | Writes implementation code |
| `sdet-unit` | Writes and runs unit tests |
| `sdet-integration` | Writes and runs integration tests |
| `sdet-e2e` | Writes and runs end-to-end tests |
| `auditor` | Reviews code and specs for compliance |
| `regression-runner` | Runs regression suites, reports results |

See [Agent Roles](manual/agent-roles.md) for full details on scope boundaries and behavioral contracts.

## Testing

```bash
# Evolution loop tests
python -m pytest eval-loop/tests/ -v

# Eval gate tests
python -m pytest eval/gates/tests/ -v

# CLI / harness tests (within the active snapshot)
python -m pytest tpls/snapshots/candidate-0/cli/tests/ -v
```
