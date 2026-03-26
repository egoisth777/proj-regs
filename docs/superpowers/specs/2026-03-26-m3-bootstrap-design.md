# M3: Bootstrap — Design Spec

**Date:** 2026-03-26
**Status:** Approved
**Subject:** Unified CLI command that creates a project registry and initializes a project in one step
**Parent spec:** `docs/superpowers/specs/2026-03-24-mas-harness-registry-design.md`

> **Scope:** This spec covers the bootstrap command — the core deliverable of M3. Template evolution (backporting to `tpl-proj/`) is out of scope; `mas-harness/` is used directly as the template.

---

## 1. Overview

The bootstrap command is a single CLI that onboards a new project into the MAS Harness system. It:

1. Creates a new project registry by copying `mas-harness/` and stripping project-specific content
2. Initializes the target project with hooks, CLAUDE.md, AGENTS.md, and symlinks

This replaces the two-step manual process (copy registry + run `init_project.py`) with one command.

## 2. CLI Interface

**Invocation:**
```bash
python harness-cli/setup/bootstrap.py \
  --name <registry-name> \
  --project <path-to-project> \
  [--registry-dir <path-to-registry-store>]
```

**Arguments:**

| Arg | Required | Default | Description |
|---|---|---|---|
| `--name` | Yes | — | Registry name (becomes folder name under registry-dir) |
| `--project` | Yes | — | Path to the target project repo (must be a git repo) |
| `--registry-dir` | No | Parent of `harness-cli/` (i.e., `proj-regs/`) | Where to create the registry folder |

**Example:**
```bash
python harness-cli/setup/bootstrap.py \
  --name voice-input-to-markdown \
  --project ~/repos/voice-input-to-markdown-sample
```

Creates `proj-regs/voice-input-to-markdown/` and initializes `~/repos/voice-input-to-markdown-sample/`.

## 3. Architecture

### New Files

```
harness-cli/
├── setup/
│   ├── __init__.py            # NEW — package marker (needed for imports)
│   ├── bootstrap.py           # NEW — unified bootstrap CLI
│   ├── init_project.py        # EXISTING — functions reused via import
│   └── templates/             # EXISTING — CLAUDE.md.tpl, AGENTS.md.tpl
└── tests/
    └── test_bootstrap.py      # NEW — unit + integration tests
```

### Importing `init_project.py`

Since `bootstrap.py` and `init_project.py` are siblings in `setup/`, `bootstrap.py` uses a `sys.path` insert (same pattern as `context/inject.py`):

```python
# bootstrap.py
import sys
from pathlib import Path
_harness_cli_root = str(Path(__file__).parent.parent)
if _harness_cli_root not in sys.path:
    sys.path.insert(0, _harness_cli_root)

from setup.init_project import (
    create_harness_json,
    copy_templates,
    create_agents_symlink,
    configure_hooks,
    update_gitignore,
)
```

A `setup/__init__.py` is also needed for pytest to discover test imports.

**Known limitation:** `init_project.py`'s `validate_inputs()` calls `sys.exit()` on error rather than raising exceptions. When called from `bootstrap.py`, validation failures will exit the process directly. This is acceptable for M3 — `bootstrap.py` wraps the call in a try/except for `SystemExit` if needed. A future refactor could change `validate_inputs()` to raise exceptions instead.

## 4. Core Logic

### `create_registry(name, registry_dir, template_path) -> Path`

1. **Validate:** Check `template_path` exists (default: `mas-harness/` sibling of `harness-cli/`)
2. **Check name collision:** If `registry_dir/name/` already exists, return error
3. **Copy template:** `shutil.copytree(template_path, registry_dir/name/)`, ignoring `.git/` if present
4. **Strip project-specific content:** Apply the stripping rules (see Section 5)
5. **Return:** Path to the newly created registry

### `bootstrap(name, project_path, registry_dir) -> None`

1. Resolve `template_path` — `mas-harness/` in the same parent as `harness-cli/`
2. Call `create_registry(name, registry_dir, template_path)` → get `registry_path`
3. Call `validate_inputs(project_path, registry_path)` from `init_project.py`
4. Call all `init_project.py` functions in order:
   - `create_harness_json(project, registry)`
   - `copy_templates(project, registry)`
   - `create_agents_symlink(project, registry)`
   - `configure_hooks(project)`
   - `update_gitignore(project)`
5. Print summary

### `main()`

1. Parse CLI args
2. Resolve `registry_dir` (default: parent of `harness-cli/`)
3. Call `bootstrap(name, project_path, registry_dir)`
4. Exit 0 on success, 1 on error

## 5. Template Stripping Rules

When copying `mas-harness/` to a new registry, files are handled in three categories:

### Files to RESET (strip project-specific content)

| File | Reset Action |
|---|---|
| `00-Project-Memory.md` | Replace first heading with `# <name> — Project Memory` |
| `blueprint/design/architecture_overview.md` | Replace content with template placeholder (keep headings, clear body) |
| `blueprint/design/api_mapping.md` | Replace content with template placeholder |
| `blueprint/engineering/performance_goals.md` | Replace content with template placeholder |
| `blueprint/planning/roadmap.md` | Clear milestone checklists, keep structure |
| `runtime/active_sprint.md` | Clear table rows, keep headers and status definitions |
| `runtime/milestones.md` | Clear checklist items, keep structure headings |
| `runtime/backlog.md` | Clear items, keep section headings |
| `runtime/resolved_bugs.md` | Clear table rows, keep header |
| `runtime/openspec/index.md` | Clear table rows, keep headers and status definitions |

### Directories to CLEAR

| Directory | Action |
|---|---|
| `runtime/openspec/changes/` | Delete all contents except `.gitkeep` |
| `runtime/openspec/archive/` | Delete all contents except `.gitkeep` |
| `runtime/implementation/` | Delete all contents except `.gitkeep` |
| `runtime/research/` | Delete all contents except `.gitkeep` |

### Files to COPY AS-IS (generic, apply to all projects)

- `blueprint/design/design_principles.md`
- `blueprint/engineering/dev_workflow.md`
- `blueprint/engineering/testing_strategy.md`
- `blueprint/orchestrate-members/*` (all 12 agent roles)
- `blueprint/hooks/*`
- `runtime/openspec/template/*` (5 template files)
- `.obsidian/*`
- `.agents/workflows/opsx.md`
- `IR_INDEX.md`
- `context_map.json` (keep all 12 roles, `path_based_rules` already empty)

### Reset Content Templates

For files that get reset, the replacement content preserves structure but clears specifics:

**`architecture_overview.md` reset:**
```markdown
# Architecture Overview

This document provides a high-level overview of the system architecture.

## 1. System Context

<!-- Describe the system context here. -->

## 2. Core Components

<!-- List core components. -->

## 3. Data Flow

<!-- Describe how data flows through the system. -->

## 4. Key Architectural Decisions

<!-- Document major decisions. -->
```

**`api_mapping.md` reset:**
```markdown
# API / Data Contracts

This document defines the data contracts and API interfaces for the project.

## 1. context_map.json

See `context_map.json` at the registry root.
```

**`performance_goals.md` reset:**
```markdown
# Performance Goals

Performance targets for the project.

<!-- Define performance goals as the project evolves. -->
```

**`roadmap.md` reset:**
```markdown
# Roadmap

This document outlines the milestones and sprints for the project.

> **Reminder:** A "sprint" here means one feature's complete lifecycle through the spec cascade (proposal → merge). A "milestone" is a collection of completed sprints that achieve a larger goal.

## Milestone 1: <Name>
**Goal:** <Description>
**Completion criteria:** <Criteria>

### Sprints (Features)
- [ ] <Feature 1>
```

**Runtime files — explicit reset content for each:**

**`active_sprint.md` reset:**
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

**`milestones.md` reset:**
```markdown
---
description: Milestone checklist with completion criteria
tags:
  - tracking
---

# Milestones

> A milestone is a collection of completed sprints that achieve a larger goal. Blueprint may evolve between milestone completions.

## Milestone 1: <Name>
**Goal:** <Description>
**Completion criteria:** <Criteria>

- [ ] <Feature 1>
```

**`backlog.md` reset:**
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


## Bugs


## Tech Debt


## Open Issues

```

**`resolved_bugs.md` reset:**
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

**`openspec/index.md` reset:**
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

**`00-Project-Memory.md` reset — full content:**
```markdown
# <name> — Project Memory

## Context Protocol
- This Registry acts as the Single Source of Truth (SSoT) for the <name> project codebase.
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

All `<name>` tokens are replaced with the `--name` argument value at bootstrap time.

## 6. Edge Cases

| Scenario | Behavior |
|---|---|
| Registry name already exists | Return error: `"Registry '<name>' already exists at <path>"`, exit code 1 |
| Name with special characters | Validate `--name` matches `[a-zA-Z0-9_-]+`. Reject spaces, slashes, unicode. |
| Project is not a git repo | Return error (delegated to `init_project.validate_inputs()`) |
| `mas-harness/` template not found | Return error: `"Template not found at <path>"`, exit code 1 |
| `--registry-dir` doesn't exist | Create it |
| Project already has `.harness.json` | Overwrite (re-bootstrap is allowed) |
| Project already has `.agents/` | Skip symlink (existing `init_project.py` behavior) |

## 7. Testing Strategy

### Unit Tests (`test_bootstrap.py`)

**Registry creation:**
- Creates registry at correct path (`<registry-dir>/<name>/`)
- Registry contains all expected files (41 files), no unexpected files (no `__pycache__`, `.DS_Store`)
- `context_map.json` has all 12 roles

**All 10 RESET files verified (parameterized test):**
- `00-Project-Memory.md` — heading contains project name, body references `<name>` not "MAS Harness"
- `architecture_overview.md` — reset to template (no harness component table)
- `api_mapping.md` — reset to template (no OpenSpec Status / Hook Payloads sections)
- `performance_goals.md` — reset to template
- `roadmap.md` — reset (no M1/M2/M3 harness milestones)
- `active_sprint.md` — table body empty, headers and status definitions preserved
- `milestones.md` — generic milestone template, no harness-specific items
- `backlog.md` — section headings preserved, items cleared
- `resolved_bugs.md` — table header preserved, rows empty
- `openspec/index.md` — table header preserved, rows empty, status definitions preserved

**Directories cleared:**
- `openspec/changes/` contains only `.gitkeep`
- `openspec/archive/` contains only `.gitkeep`
- `implementation/` contains only `.gitkeep`
- `research/` contains only `.gitkeep`

**Project initialization:**
- `.harness.json` points to the new registry
- `CLAUDE.md` exists with registry path
- `.agents/` symlinks to new registry's orchestrate-members
- Hooks configured in `.claude/settings.local.json`

**Error handling:**
- Registry name collision → error, exit code 1
- Missing template → error, exit code 1
- Non-git project → error, exit code 1

**Idempotency:**
- Running bootstrap twice with same name → error on second run (name collision)
- Running bootstrap twice with different names → both registries created

**Integration test:**
- Full bootstrap against a temp project → verify complete setup

## 8. Delivery Order

```
1. Write tests (TDD)
2. Implement bootstrap.py (registry creation + stripping + call init_project functions)
3. Integration test
4. Commit
```

## 9. Key Design Decisions

| Decision | Rationale |
|---|---|
| Use `mas-harness/` as template, not `tpl-proj/` | `mas-harness/` is the evolved, proven structure. `tpl-proj/` is the old template. Skip the middleman. |
| One unified command | Two-step process is error-prone. One command = one mental model. |
| Import `init_project.py` functions, don't refactor | Functions are already well-factored. No unnecessary changes. |
| Strip by replacing content, not by templating | Simpler than maintaining a separate template system. The reset content is inline in the code. |
| Error on name collision | Prevents accidental overwrites. Re-bootstrap a project by using a different name or deleting the old registry. |
| `--registry-dir` defaults to `proj-regs/` | Central registry store convention. Override for non-standard setups. |
