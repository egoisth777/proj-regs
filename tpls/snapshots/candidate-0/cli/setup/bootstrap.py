"""Unified bootstrap: creates a project registry and initializes a project in one step."""

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

# Ensure harness-cli root is on sys.path
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

# Default template: mas-harness/ sibling of harness-cli/
DEFAULT_TEMPLATE = Path(__file__).parent.parent.parent / "mas-harness"
DEFAULT_REGISTRY_DIR = Path(__file__).parent.parent.parent  # proj-regs/

NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

# --- Reset content templates ---

RESET_ARCHITECTURE = """# Architecture Overview

This document provides a high-level overview of the system architecture.

## 1. System Context

<!-- Describe the system context here. -->

## 2. Core Components

<!-- List core components. -->

## 3. Data Flow

<!-- Describe how data flows through the system. -->

## 4. Key Architectural Decisions

<!-- Document major decisions. -->
"""

RESET_API_MAPPING = """# API / Data Contracts

This document defines the data contracts and API interfaces for the project.

## 1. context_map.json

See `context_map.json` at the registry root.
"""

RESET_PERFORMANCE = """# Performance Goals

Performance targets for the project.

<!-- Define performance goals as the project evolves. -->
"""

RESET_ROADMAP = """# Roadmap

This document outlines the milestones and sprints for the project.

> **Reminder:** A "sprint" here means one feature's complete lifecycle through the spec cascade (proposal → merge). A "milestone" is a collection of completed sprints that achieve a larger goal.

## Milestone 1: <Name>
**Goal:** <Description>
**Completion criteria:** <Criteria>

### Sprints (Features)
- [ ] <Feature 1>
"""

RESET_ACTIVE_SPRINT = """---
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
"""

RESET_MILESTONES = """---
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
"""

RESET_BACKLOG = """---
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

"""

RESET_RESOLVED_BUGS = """---
description: Track resolved bugs and issues
tags:
  - tracking
related: "backlog.md"
---

# Resolved Bugs

| Bug | Resolution | Date | Related OpenSpec |
|---|---|---|---|
|  |  |  |  |
"""

RESET_OPENSPEC_INDEX = """---
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
"""


def _reset_project_memory(content: str, name: str) -> str:
    """Generate 00-Project-Memory.md with <name> substituted."""
    template = """# {name} — Project Memory

## Context Protocol
- This Registry acts as the Single Source of Truth (SSoT) for the {name} project codebase.
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
"""
    return template.format(name=name)


def _clear_directory(dir_path: Path):
    """Remove all contents of a directory except .gitkeep."""
    if not dir_path.exists():
        return
    for item in dir_path.iterdir():
        if item.name == ".gitkeep":
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def create_registry(name: str, registry_dir: Path, template_path: Path) -> Path:
    """Create a new registry by copying template and stripping project-specific content."""
    registry_path = registry_dir / name

    # Validate
    if not template_path.exists():
        print(f"Error: Template not found at {template_path}", file=sys.stderr)
        sys.exit(1)

    if registry_path.exists():
        print(f"Error: Registry '{name}' already exists at {registry_path}", file=sys.stderr)
        sys.exit(1)

    # Copy template
    shutil.copytree(
        str(template_path), str(registry_path),
        ignore=shutil.ignore_patterns(".git", "__pycache__", ".DS_Store"),
    )

    # --- Strip project-specific content ---

    # Reset files with inline templates
    (registry_path / "00-Project-Memory.md").write_text(_reset_project_memory("", name))
    (registry_path / "blueprint" / "design" / "architecture_overview.md").write_text(RESET_ARCHITECTURE)
    (registry_path / "blueprint" / "design" / "api_mapping.md").write_text(RESET_API_MAPPING)
    (registry_path / "blueprint" / "engineering" / "performance_goals.md").write_text(RESET_PERFORMANCE)
    (registry_path / "blueprint" / "planning" / "roadmap.md").write_text(RESET_ROADMAP)
    (registry_path / "runtime" / "active_sprint.md").write_text(RESET_ACTIVE_SPRINT)
    (registry_path / "runtime" / "milestones.md").write_text(RESET_MILESTONES)
    (registry_path / "runtime" / "backlog.md").write_text(RESET_BACKLOG)
    (registry_path / "runtime" / "resolved_bugs.md").write_text(RESET_RESOLVED_BUGS)
    (registry_path / "runtime" / "openspec" / "index.md").write_text(RESET_OPENSPEC_INDEX)

    # Clear directories (keep only .gitkeep)
    _clear_directory(registry_path / "runtime" / "openspec" / "changes")
    _clear_directory(registry_path / "runtime" / "openspec" / "archive")
    _clear_directory(registry_path / "runtime" / "implementation")
    _clear_directory(registry_path / "runtime" / "research")

    return registry_path


def bootstrap(name: str, project_path: Path, registry_dir: Path):
    """Create a registry and initialize a project in one step."""
    # Validate name
    if not NAME_PATTERN.match(name):
        print(f"Error: Invalid name '{name}'. Must match [a-zA-Z0-9_-]+", file=sys.stderr)
        sys.exit(1)

    # Resolve template path
    template_path = DEFAULT_TEMPLATE
    if not template_path.exists():
        print(f"Error: Template not found at {template_path}", file=sys.stderr)
        sys.exit(1)

    # Create registry-dir if needed
    registry_dir.mkdir(parents=True, exist_ok=True)

    print(f"Bootstrapping MAS Harness for: {project_path}")
    print(f"  Registry: {registry_dir / name}")

    # Step 1: Create registry
    registry_path = create_registry(name, registry_dir, template_path)
    print(f"  Registry created: {registry_path}")

    # Step 2: Validate project
    project = project_path.resolve()
    registry = registry_path.resolve()

    if not project.exists():
        print(f"Error: Project directory does not exist: {project}", file=sys.stderr)
        sys.exit(1)
    if not (project / ".git").exists():
        print(f"Error: Project is not a git repository: {project}", file=sys.stderr)
        sys.exit(1)

    # Step 3: Initialize project (reuse init_project functions)
    create_harness_json(project, registry)
    copy_templates(project, registry)
    create_agents_symlink(project, registry)
    configure_hooks(project)
    update_gitignore(project)

    print(f"\nDone! MAS Harness bootstrapped.")
    print(f"  Registry: {registry_path}")
    print(f"  Project: {project_path}")


def main():
    parser = argparse.ArgumentParser(description="Bootstrap MAS Harness: create registry + initialize project")
    parser.add_argument("--name", required=True, help="Registry name (folder name)")
    parser.add_argument("--project", required=True, help="Path to the target project repo")
    parser.add_argument("--registry-dir", default=None, help="Where to create the registry (default: proj-regs/)")
    args = parser.parse_args()

    project_path = Path(args.project).resolve()
    registry_dir = Path(args.registry_dir).resolve() if args.registry_dir else DEFAULT_REGISTRY_DIR

    bootstrap(args.name, project_path, registry_dir)


if __name__ == "__main__":
    main()
