# MAS Harness Registry Design Spec

**Date:** 2026-03-24
**Status:** Approved
**Subject:** Project registry structure for the MAS Harness system

> **Note:** This spec describes the **evolved** `mas-harness/` registry (Approach B). It intentionally diverges from the existing `tpl-proj/` template — the template is the "before" state, this spec is the "after." The template will not be updated until the model is proven (a future Approach C effort).

---

## 1. Overview

The MAS Harness is a meta-system — a framework that orchestrates multi-agent development across projects. It has two layers:

- **Protocol layer**: Markdown conventions, file structures, and agent role definitions that guide agent behavior
- **Executable layer** (planned): Hooks, skills, CLI scripts (Python/TypeScript), and JSON inter-flow data passing

The harness manages projects through **project registries** — Obsidian vaults that act as both the Single Source of Truth (SSoT) and the runtime harness for each project. The registry serves two roles:

1. **Persistent brain** — survives session death so 0-state agents can resume exactly where things were left off
2. **Process gatekeeper** — prevents ad-hoc changes by enforcing the specification cascade

## 2. Core Philosophy

### Specification Cascade

All changes must pass through a formalization chain before any code is written:

```
Requirements → Behaviors → Behavior Specs (Given/When/Then) → Test Specs → Tests → Code
```

Each step formalizes the previous one, reducing ambiguity at every layer. Humans (and agents) are bad at abstract requirements, but behaviors are observable and testable.

### Two-Part System

**Part 1 — Spec cascade (per-feature):** The chain above. Every feature and bug fix, no matter how small, goes through this process.

**Part 2 — Grand framework (per-project):** The static architectural scaffold that constrains how development happens:
- Tech specification
- Code linter (quality and style)
- Roadmap (milestones = grand vision, sprints = per-feature lifecycle)
- OpenSpec system (each feature gets its own spec folder)

The grand framework is frozen during sprints. It may only evolve between milestone completions.

### Minimum Context Principle

Each agent team receives only the minimum context needed to complete its work without breaking the system:
- **Workers** get: blueprint (static) + their feature's OpenSpec folder. Nothing else.
- **Orchestrator** sees the full picture: `active_sprint.md`, `milestones.md`, all active features.
- `context_map.json` enforces which docs each role receives.

### Parallel Feature Isolation

- Decoupled features run in parallel, each in its own worktree with its own OpenSpec folder
- Coupled features must run sequentially — never in parallel
- If a worker discovers mid-implementation that it needs to touch files owned by another active feature, it stops and escalates to the orchestrator

**Coupling detection:** The Team Lead performs upfront file-scope analysis when breaking an OpenSpec into tasks. Each task declares which files/modules it will touch. The Orchestrator compares file scopes across all active features before approving parallel execution. If scopes overlap, the features are sequenced. If unexpected coupling is discovered mid-implementation (a worker needs a file not in its declared scope), the worker stops and escalates to the Orchestrator.

### Cyclical Lifecycle

There is no "project complete" state. The system cycles:

```
Milestones complete → Triage backlog → Define new milestones → New sprints → Execute → Repeat
```

Between milestone completions, the blueprint is allowed to evolve (through Sonders/Negator review). During sprints, it is frozen.

## 3. Registry Folder Structure

```
mas-harness/
├── 00-Project-Memory.md              # Entry point — SSoT routing
├── (NO CLAUDE.md or AGENTS.md here)   # These live in the project repo only
├── IR_INDEX.md                       # Implementation decision records index
├── context_map.json                  # Minimum-context injection per agent role
├── .obsidian/                        # Vault config
│
├── blueprint/                        # STATIC — frozen during sprints
│   ├── design/
│   │   ├── architecture_overview.md  # Harness components: protocol, hooks, skills, CLI
│   │   ├── design_principles.md      # Spec cascade + minimum context principle
│   │   └── api_mapping.md            # JSON inter-flow data contracts
│   ├── engineering/
│   │   ├── dev_workflow.md           # Feature isolation, worktree rules, PR flow
│   │   ├── testing_strategy.md       # BDD + TDD + full regression gate
│   │   └── performance_goals.md
│   ├── orchestrate-members/          # → project repo symlinks .agents/ here
│   │   ├── orchestrator.md           # Pure delegator, never reads/writes
│   │   ├── sonders.md               # Creative architect (Phase 0)
│   │   ├── negator.md               # Red-team critic (Phase 0)
│   │   ├── behavior-spec-writer.md  # Requirements → Given/When/Then
│   │   ├── test-spec-writer.md      # Behavior specs → test specifications
│   │   ├── team-lead.md             # Reads OpenSpec, delegates to workers
│   │   ├── worker.md                # Isolated coder in worktree
│   │   ├── sdet-unit.md             # Unit test writer
│   │   ├── sdet-integration.md      # Integration test writer
│   │   ├── sdet-e2e.md              # E2E test writer
│   │   ├── auditor.md               # PR gatekeeper (architecture + OpenSpec)
│   │   └── regression-runner.md     # Full test suite before merge
│   ├── hooks/
│   │   └── post-pr-wait.md          # After local PR → poll remote → wait CI + reviews
│   └── planning/
│       └── roadmap.md               # Milestones (grand vision) containing sprints
│
├── runtime/                          # DYNAMIC — read/write during execution
│   ├── active_sprint.md             # ORCHESTRATOR-ONLY — index of active features
│   ├── milestones.md                # Milestone checklist with completion criteria
│   ├── backlog.md                   # Permanent intake (features, bugs, tech debt)
│   ├── resolved_bugs.md
│   ├── openspec/
│   │   ├── index.md                 # Feature registry table (all: active + completed)
│   │   ├── template/               # Blank OpenSpec for new features
│   │   │   ├── proposal.md         # Supersedes old template's proposal.md (unchanged)
│   │   │   ├── behavior_spec.md    # NEW — replaces no equivalent in old template
│   │   │   ├── test_spec.md        # Supersedes old template's test-plan.md
│   │   │   ├── tasks.md            # Supersedes old template's tasks.md (unchanged)
│   │   │   └── status.md           # NEW — per-feature runtime state
│   │   ├── changes/                 # Active features (one folder each)
│   │   │   └── <YYYY-MM-DD-feature>/
│   │   │       ├── proposal.md          # What and why
│   │   │       ├── behavior_spec.md     # Given/When/Then
│   │   │       ├── test_spec.md         # Test specifications from behaviors
│   │   │       ├── tasks.md             # Granular checklist + assigned worktree
│   │   │       └── status.md            # Feature-local runtime state
│   │   └── archive/                 # Completed features moved here
│   ├── implementation/              # IR-xxx records
│   └── research/                    # Scratchpad
│
└── .agents/
    └── workflows/
        └── opsx.md                  # OpenSpec workflow commands
```

## 4. Project ↔ Registry Boundary

The project repo and the registry vault are strictly separated:

| Component | Lives in | Purpose |
|---|---|---|
| `CLAUDE.md` | **Project repo only** (actual file) | Agent behavior instructions. Points agents to the registry as SSoT. Auto-loaded by Claude Code. |
| `AGENTS.md` | **Project repo only** (actual file) | Same as above. |
| `.agents/` | **Project repo** → symlink → `mas-harness/blueprint/orchestrate-members/` | Agent role definitions. Single copy in registry, symlinked from project. |
| Registry vault | **Separate folder** (e.g., `proj-regs/mas-harness/`) | Pure knowledge base. No CLAUDE.md, no AGENTS.md. |

### Why no CLAUDE.md in the registry

Claude Code auto-loads `CLAUDE.md` when an agent enters a directory. If the registry contained one, any subagent that reads registry files would have the full MAS orchestration instructions injected into its context — polluting the context window when it only needs to read a specific file.

Instead:
- **Project repo's CLAUDE.md** tells agents how to behave and where the SSoT is
- **`context_map.json`** controls which registry files each role receives (minimum context)
- **Subagents never browse the registry directly** — the Orchestrator reads specific files and injects them into subagent prompts

This cleanly separates "how agents behave" (project repo) from "what agents know" (registry vault).

The harness CLI (M3) will automate project initialization (creating CLAUDE.md, AGENTS.md, and the .agents/ symlink).

## 5. Agent Roster

> **Delta from template:** The existing `tpl-proj/` has 7 agents (orchestrator, sonders, negator, team-lead, worker, sdet, auditor). This spec:
> - **Redefines** orchestrator (from active architect → pure delegator)
> - **Adds** behavior-spec-writer, test-spec-writer (new roles for the spec cascade)
> - **Splits** sdet → sdet-unit, sdet-integration, sdet-e2e (one generic tester → three specialized testers, because each test type has different inputs and scope)
> - **Adds** regression-runner (extracted from auditor to isolate test execution from architectural review)
> - **Unchanged** sonders, negator, team-lead, worker

### Orchestrator (Main Agent)
- **Strictly a delegator** — never reads/writes project files directly
- Only communicates with the user and dispatches subagents
- Dispatches subagents to read/write `active_sprint.md` and `milestones.md` for coordination
- Responsible for coupling detection: compares file scopes across active features before approving parallel execution

### Phase 0 — Design
| Agent | Role | Trigger | Input | Output |
|---|---|---|---|---|
| Sonders | Creative architect. Drafts architecture docs. Optimistic, visionary. | User initiates new feature design | User requirements | `blueprint/design/` docs (architecture, principles) |
| Negator | Red-team critic. Attacks Sonders' designs for flaws, security issues, scope creep. | After Sonders completes first draft | Sonders' design docs | `[Red Team Review]` annotations on design docs |

### Spec Cascade
| Agent | Role | Trigger | Input | Output |
|---|---|---|---|---|
| Behavior Spec Writer | Translates finalized design into Given/When/Then behavioral specifications | After Sonders/Negator reach consensus on design | Approved design docs + user requirements | `behavior_spec.md` in the feature's OpenSpec folder |
| Test Spec Writer | Derives test specifications from behavior specs | After `behavior_spec.md` is complete | `behavior_spec.md` | `test_spec.md` in the feature's OpenSpec folder |

### Execution
| Agent | Role | Trigger | Input | Output |
|---|---|---|---|---|
| Team Lead | Reads OpenSpec, performs file-scope analysis, breaks into tasks, delegates to workers in parallel worktrees | After OpenSpec is locked (all spec cascade files complete) | Full OpenSpec folder | `tasks.md` with file-scope declarations per task |
| Worker | Isolated coder. Executes in a single worktree. Sees only its feature's OpenSpec + blueprint. | Spawned by Team Lead per task | Single task from `tasks.md` + blueprint | Code implementation |
| SDET:Unit | Writes unit tests from test specs (before implementation) | After `test_spec.md` is complete, before Workers start | `test_spec.md` | Unit test files |
| SDET:Integration | Writes integration tests from test specs (before implementation) | After `test_spec.md` is complete, before Workers start | `test_spec.md` + `architecture_overview.md` | Integration test files |
| SDET:E2E | Writes end-to-end tests from behavior specs | After `behavior_spec.md` is complete, before Workers start | `behavior_spec.md` | E2E test files |

### Quality Gate
| Agent | Role | Trigger | Input | Output |
|---|---|---|---|---|
| Auditor | Reviews PRs against architecture + OpenSpec. Performs architectural review only (does not run tests). | After PR is created | PR diff + OpenSpec + blueprint | Approve / Request changes |
| Regression Runner | Executes the full test suite (unit + integration + E2E + regression) before any merge. Separate from Auditor to isolate concerns. | Before Auditor review begins | Full codebase on feature branch | Pass / Fail report |

## 6. Context Map (`context_map.json`)

The context map defines which registry documents each agent role receives when spawned with 0-state memory. This enforces the minimum context principle.

### Schema

```json
{
  "version": "2.0",
  "description": "Minimum-context injection rules per agent role.",
  "agent_role_context": {
    "<role-name>": {
      "required_docs": [
        "<path-relative-to-registry-root>"
      ]
    }
  },
  "path_based_rules": [
    {
      "project_path": "<glob-pattern-in-project-repo>",
      "inject_docs": [
        "<path-relative-to-registry-root>"
      ]
    }
  ]
}
```

### Agent Role Mappings

| Role | Required Docs |
|---|---|
| orchestrator | `00-Project-Memory.md`, `runtime/active_sprint.md`, `runtime/milestones.md` |
| sonders | `00-Project-Memory.md`, `blueprint/planning/roadmap.md`, `blueprint/design/architecture_overview.md` |
| negator | `00-Project-Memory.md`, `blueprint/design/architecture_overview.md`, `blueprint/design/design_principles.md` |
| behavior-spec-writer | `00-Project-Memory.md`, `blueprint/design/design_principles.md`, `<feature>/proposal.md` |
| test-spec-writer | `00-Project-Memory.md`, `<feature>/behavior_spec.md` |
| team-lead | `00-Project-Memory.md`, `blueprint/engineering/dev_workflow.md`, `<feature>/proposal.md`, `<feature>/tasks.md` |
| worker | `blueprint/engineering/dev_workflow.md`, `<feature>/tasks.md` (single task only) |
| sdet-unit | `blueprint/engineering/testing_strategy.md`, `<feature>/test_spec.md` |
| sdet-integration | `blueprint/engineering/testing_strategy.md`, `blueprint/design/architecture_overview.md`, `<feature>/test_spec.md` |
| sdet-e2e | `blueprint/engineering/testing_strategy.md`, `<feature>/behavior_spec.md` |
| auditor | `blueprint/design/architecture_overview.md`, `blueprint/design/design_principles.md`, `<feature>/proposal.md` |
| regression-runner | `blueprint/engineering/testing_strategy.md` |

`<feature>` resolves to the active OpenSpec folder: `runtime/openspec/changes/<YYYY-MM-DD-feature>/`

### How agents consume it
1. The Orchestrator reads `context_map.json` before dispatching any subagent
2. It resolves the role name to its `required_docs` list
3. It injects those documents (and only those) into the subagent's prompt/context
4. `path_based_rules` add additional docs when the subagent's task touches specific project paths (configured per-project)

## 7. Testing Model

### Per-Feature (Spec Cascade)
Every feature produces tests through the cascade:
1. Behavior specs define expected behaviors (Given/When/Then)
2. Test specs formalize those into testable assertions
3. SDET agents write tests before workers write code (TDD)

### Pre-Merge (Quality Gate)
Before any PR merges:
1. Feature-specific tests must pass (unit + integration + E2E)
2. Full regression suite must pass (all existing tests)
3. Linter must pass
4. Auditor reviews against architecture + OpenSpec
5. Post-PR hook polls remote GitHub PR for CI status + review bot feedback
6. All review comments must be resolved

### Parallel Feature Merge
When multiple features complete:
- Each opens its own PR
- Each must independently pass the full test suite
- First-merged wins; subsequent features rebase onto updated main and re-run
- No merge until all gates clear

## 8. Hooks

> **Current status:** Hooks are currently defined as **protocol instructions** (markdown specs that agents follow). In M1, they will be implemented as executable Claude Code hooks in `settings.json`. The markdown definitions in `blueprint/hooks/` serve as the behavioral specification for the executable implementations.

### `post-pr-wait`
**Trigger:** After local PR is created (`gh pr create`)
**Behavior:**
1. Poll remote GitHub PR status
2. Wait for CI checks to complete
3. Wait for review bot feedback
4. Collect all comments
5. Return collected feedback to the agent
6. Agent addresses all review issues before proceeding

The agent is blocked until all remote feedback is collected. This prevents premature merges.

## 9. Milestones vs Sprints

| Concept | Definition | Scope |
|---|---|---|
| **Milestone** | Grand vision checkpoint. A collection of completed sprints that achieve a larger goal. | Multiple features |
| **Sprint** | One feature's complete lifecycle through the spec cascade, from proposal to merge. | Single feature |

`milestones.md` tracks milestone-level progress with completion criteria.
`active_sprint.md` (orchestrator-only) indexes all currently active sprints/features.
Each feature's `status.md` tracks its own sprint-level progress.

## 10. Roadmap (Harness Development)

| Milestone | Description | Sprints (Features) |
|---|---|---|
| **M1: Enforcement Layer** | Stop agents from misbehaving | Hooks (path validation, spec cascade gate), Skills (`/opsx` as real flows), post-PR-wait hook |
| **M2: Execution Engine** | Deterministic automation | CLI scripts (Python/TS), JSON inter-flow data passing, state management |
| **M3: Scaling** | Project onboarding | Template automation (registry creation), project initialization (symlink setup) |

## 11. End-to-End Feature Workflow (Owner Map)

This clarifies who does what at each phase:

```
Phase 0: Design
  User → provides requirements
  Orchestrator → dispatches Sonders
  Sonders → drafts design docs in blueprint/design/
  Orchestrator → dispatches Negator
  Negator → red-team reviews Sonders' drafts
  Sonders + Negator → iterate until consensus (User breaks ties)
  Blueprint is updated and frozen

Phase 1: Spec Cascade (per-feature)
  Orchestrator → dispatches Behavior Spec Writer
  Behavior Spec Writer → writes behavior_spec.md in feature's OpenSpec folder
  Orchestrator → dispatches Test Spec Writer
  Test Spec Writer → writes test_spec.md from behavior_spec.md
  Orchestrator → dispatches SDET agents (unit, integration, E2E)
  SDET agents → write tests BEFORE any code exists (test files go to codebase, not OpenSpec folder)
  OpenSpec is now locked (= proposal.md + behavior_spec.md + test_spec.md are finalized and immutable)

Phase 2: Execution
  Orchestrator → dispatches Team Lead
  Team Lead → reads OpenSpec, performs file-scope analysis, writes tasks.md
  Orchestrator → approves file scopes (checks for coupling with other active features)
  Team Lead → spawns Workers in parallel worktrees
  Workers → implement code to pass SDET tests

Phase 3: Quality Gate
  Orchestrator → dispatches Regression Runner
  Regression Runner → runs full test suite (all tests, not just feature tests)
  Orchestrator → dispatches Auditor
  Auditor → architectural review of PR against blueprint + OpenSpec
  PR created → post-pr-wait hook fires → polls remote CI + reviews
  All review issues resolved → merge

Phase 4: Wrap-up
  Orchestrator → dispatches subagent to:
    Move OpenSpec to archive/
    Update openspec/index.md
    Update milestones.md
    Update active_sprint.md
```

> **Key rule:** The Orchestrator never performs any of these actions directly. It dispatches the appropriate agent for each step.

## 12. Key Design Decisions

| Decision | Rationale |
|---|---|
| No CLAUDE.md in registry | Prevents context pollution. Subagents accessing the registry won't auto-load heavy orchestration instructions. |
| Project ↔ Registry separation | CLAUDE.md/AGENTS.md live in project repo only. `.agents/` symlinks to registry. Registry is a pure knowledge base. |
| Orchestrator = pure delegator | Never reads/writes. Only talks to user + dispatches. Prevents context pollution. |
| Per-feature isolated runtime | Each OpenSpec folder is self-contained with `status.md`. Workers read only their folder. |
| Orchestrator-only `active_sprint.md` | Workers never see cross-feature state. Only orchestrator coordinates. |
| Spec cascade in every OpenSpec | `proposal` → `behavior_spec` → `test_spec` → `tasks`. All must exist before code. |
| `openspec/index.md` | Master table mapping all features (active + archived) with status, dates, milestone. |
| Coupled features = sequential | If two features touch same files, they run sequentially. Workers escalate if unexpected coupling. |
| Blueprint frozen during sprints | Architecture only evolves between milestone completions, through Sonders/Negator review. |
| Cyclical lifecycle | No "done" state. Completed milestone → triage → new milestone → repeat. |
| Enforcement first (M1) | Biggest pain point is agents misbehaving. Fix discipline before building machinery. |
| `blueprint/` (singular) | Consistent naming. The old template's CLAUDE.md/AGENTS.md used `blueprints/` (plural) inconsistently — this spec standardizes on singular. |
| "Sprint" = feature lifecycle | Non-standard usage. A sprint is one feature's complete lifecycle through the spec cascade. This must be defined in CLAUDE.md so agents don't assume industry-standard sprint semantics. |
