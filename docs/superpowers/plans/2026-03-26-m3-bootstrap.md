# M3: Bootstrap — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a unified CLI command that creates a project registry from `mas-harness/` template and initializes a project with hooks in one step.

**Architecture:** Single Python module (`setup/bootstrap.py`) that copies `mas-harness/`, strips project-specific content via inline reset templates, then calls existing `init_project.py` functions to set up the target project.

**Tech Stack:** Python 3.10+ (pytest, shutil), reuses `setup/init_project.py` functions from M1

**Spec:** `docs/superpowers/specs/2026-03-26-m3-bootstrap-design.md`

**Task execution order:** Tasks MUST be executed sequentially (1 → 4).

---

## File Map

| File | Purpose |
|---|---|
| `harness-cli/setup/__init__.py` | NEW — package marker for imports |
| `harness-cli/setup/bootstrap.py` | NEW — unified bootstrap CLI |
| `harness-cli/tests/test_bootstrap.py` | NEW — unit + integration tests |

---

## Tasks

### Task 1: Package marker + tests (TDD red phase)

**Files:**
- Create: `harness-cli/setup/__init__.py`
- Create: `harness-cli/tests/test_bootstrap.py`

- [ ] **Step 1: Create setup package marker**

```python
# setup/__init__.py
# (empty file)
```

- [ ] **Step 2: Write all tests**

```python
# tests/test_bootstrap.py
"""Tests for the bootstrap CLI — creates a registry and initializes a project in one step."""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

# The real mas-harness template
MAS_HARNESS = Path(__file__).parent.parent.parent / "mas-harness"
BOOTSTRAP_SCRIPT = Path(__file__).parent.parent / "setup" / "bootstrap.py"


@pytest.fixture
def bootstrap_env(tmp_path):
    """Create a temp project (git repo) and a temp registry-dir."""
    project = tmp_path / "myproject"
    project.mkdir()
    subprocess.run(["git", "init", str(project)], capture_output=True)

    registry_dir = tmp_path / "registries"
    registry_dir.mkdir()

    return project, registry_dir


def _run_bootstrap(name, project, registry_dir):
    """Helper to run the bootstrap script."""
    result = subprocess.run(
        [
            "python", str(BOOTSTRAP_SCRIPT),
            "--name", name,
            "--project", str(project),
            "--registry-dir", str(registry_dir),
        ],
        capture_output=True, text=True,
    )
    return result


# --- Registry Creation Tests ---

class TestRegistryCreation:
    def test_creates_registry_at_correct_path(self, bootstrap_env):
        project, registry_dir = bootstrap_env
        _run_bootstrap("test-project", project, registry_dir)
        assert (registry_dir / "test-project").is_dir()

    def test_registry_has_expected_file_count(self, bootstrap_env):
        project, registry_dir = bootstrap_env
        _run_bootstrap("test-project", project, registry_dir)
        registry = registry_dir / "test-project"
        files = [f for f in registry.rglob("*") if f.is_file()]
        assert len(files) == 41

    def test_no_unexpected_files(self, bootstrap_env):
        project, registry_dir = bootstrap_env
        _run_bootstrap("test-project", project, registry_dir)
        registry = registry_dir / "test-project"
        files = [f for f in registry.rglob("*") if f.is_file()]
        for f in files:
            assert "__pycache__" not in str(f)
            assert ".DS_Store" not in f.name

    def test_context_map_has_12_roles(self, bootstrap_env):
        project, registry_dir = bootstrap_env
        _run_bootstrap("test-project", project, registry_dir)
        cm = json.loads((registry_dir / "test-project" / "context_map.json").read_text())
        assert len(cm["agent_role_context"]) == 12


# --- Reset File Verification (parameterized) ---

class TestResetFiles:
    def test_project_memory_has_project_name(self, bootstrap_env):
        project, registry_dir = bootstrap_env
        _run_bootstrap("my-cool-app", project, registry_dir)
        content = (registry_dir / "my-cool-app" / "00-Project-Memory.md").read_text()
        assert "my-cool-app" in content
        assert "MAS Harness" not in content

    def test_architecture_overview_reset(self, bootstrap_env):
        project, registry_dir = bootstrap_env
        _run_bootstrap("test-project", project, registry_dir)
        content = (registry_dir / "test-project" / "blueprint" / "design" / "architecture_overview.md").read_text()
        assert "<!-- Describe the system context here. -->" in content
        assert "Protocol Layer" not in content  # harness-specific content gone

    def test_api_mapping_reset(self, bootstrap_env):
        project, registry_dir = bootstrap_env
        _run_bootstrap("test-project", project, registry_dir)
        content = (registry_dir / "test-project" / "blueprint" / "design" / "api_mapping.md").read_text()
        assert "context_map.json" in content
        assert "OpenSpec Status (Planned" not in content  # harness-specific gone

    def test_performance_goals_reset(self, bootstrap_env):
        project, registry_dir = bootstrap_env
        _run_bootstrap("test-project", project, registry_dir)
        content = (registry_dir / "test-project" / "blueprint" / "engineering" / "performance_goals.md").read_text()
        assert "<!-- Define performance goals" in content
        assert "Hook execution time" not in content  # harness-specific gone

    def test_roadmap_reset(self, bootstrap_env):
        project, registry_dir = bootstrap_env
        _run_bootstrap("test-project", project, registry_dir)
        content = (registry_dir / "test-project" / "blueprint" / "planning" / "roadmap.md").read_text()
        assert "## Milestone 1: <Name>" in content
        assert "Enforcement Layer" not in content  # harness milestones gone

    def test_active_sprint_reset(self, bootstrap_env):
        project, registry_dir = bootstrap_env
        _run_bootstrap("test-project", project, registry_dir)
        content = (registry_dir / "test-project" / "runtime" / "active_sprint.md").read_text()
        assert "ORCHESTRATOR-ONLY" in content
        assert "## Statuses" in content

    def test_milestones_reset(self, bootstrap_env):
        project, registry_dir = bootstrap_env
        _run_bootstrap("test-project", project, registry_dir)
        content = (registry_dir / "test-project" / "runtime" / "milestones.md").read_text()
        assert "## Milestone 1: <Name>" in content
        assert "Enforcement Layer" not in content

    def test_backlog_reset(self, bootstrap_env):
        project, registry_dir = bootstrap_env
        _run_bootstrap("test-project", project, registry_dir)
        content = (registry_dir / "test-project" / "runtime" / "backlog.md").read_text()
        assert "## Features" in content
        assert "## Bugs" in content

    def test_resolved_bugs_reset(self, bootstrap_env):
        project, registry_dir = bootstrap_env
        _run_bootstrap("test-project", project, registry_dir)
        content = (registry_dir / "test-project" / "runtime" / "resolved_bugs.md").read_text()
        assert "| Bug | Resolution" in content

    def test_openspec_index_reset(self, bootstrap_env):
        project, registry_dir = bootstrap_env
        _run_bootstrap("test-project", project, registry_dir)
        content = (registry_dir / "test-project" / "runtime" / "openspec" / "index.md").read_text()
        assert "## Statuses" in content
        assert "| Feature | OpenSpec Path" in content


# --- Directory Clearing Tests ---

class TestDirectoryClearing:
    def test_openspec_changes_only_gitkeep(self, bootstrap_env):
        project, registry_dir = bootstrap_env
        _run_bootstrap("test-project", project, registry_dir)
        changes = registry_dir / "test-project" / "runtime" / "openspec" / "changes"
        files = list(changes.iterdir())
        assert len(files) == 1
        assert files[0].name == ".gitkeep"

    def test_openspec_archive_only_gitkeep(self, bootstrap_env):
        project, registry_dir = bootstrap_env
        _run_bootstrap("test-project", project, registry_dir)
        archive = registry_dir / "test-project" / "runtime" / "openspec" / "archive"
        files = list(archive.iterdir())
        assert len(files) == 1
        assert files[0].name == ".gitkeep"

    def test_implementation_only_gitkeep(self, bootstrap_env):
        project, registry_dir = bootstrap_env
        _run_bootstrap("test-project", project, registry_dir)
        impl = registry_dir / "test-project" / "runtime" / "implementation"
        files = list(impl.iterdir())
        assert len(files) == 1
        assert files[0].name == ".gitkeep"

    def test_research_only_gitkeep(self, bootstrap_env):
        project, registry_dir = bootstrap_env
        _run_bootstrap("test-project", project, registry_dir)
        research = registry_dir / "test-project" / "runtime" / "research"
        files = list(research.iterdir())
        assert len(files) == 1
        assert files[0].name == ".gitkeep"


# --- Project Initialization Tests ---

class TestProjectInitialization:
    def test_harness_json_points_to_new_registry(self, bootstrap_env):
        project, registry_dir = bootstrap_env
        _run_bootstrap("test-project", project, registry_dir)
        config = json.loads((project / ".harness.json").read_text())
        assert str(registry_dir / "test-project") in config["registry_path"]

    def test_claude_md_created(self, bootstrap_env):
        project, registry_dir = bootstrap_env
        _run_bootstrap("test-project", project, registry_dir)
        assert (project / "CLAUDE.md").exists()
        content = (project / "CLAUDE.md").read_text()
        assert str(registry_dir / "test-project") in content

    def test_agents_symlink_to_new_registry(self, bootstrap_env):
        project, registry_dir = bootstrap_env
        _run_bootstrap("test-project", project, registry_dir)
        agents = project / ".agents"
        assert agents.is_symlink()
        target = Path(os.readlink(str(agents)))
        assert "test-project" in str(target)
        assert "orchestrate-members" in str(target)

    def test_hooks_configured(self, bootstrap_env):
        project, registry_dir = bootstrap_env
        _run_bootstrap("test-project", project, registry_dir)
        settings = json.loads((project / ".claude" / "settings.local.json").read_text())
        assert "hooks" in settings
        assert len(settings["hooks"]["PreToolUse"]) == 2
        assert len(settings["hooks"]["PostToolUse"]) == 1


# --- Error Handling Tests ---

class TestErrorHandling:
    def test_name_collision_fails(self, bootstrap_env):
        project, registry_dir = bootstrap_env
        _run_bootstrap("test-project", project, registry_dir)
        result = _run_bootstrap("test-project", project, registry_dir)
        assert result.returncode == 1
        assert "already exists" in result.stderr or "already exists" in result.stdout

    def test_invalid_name_fails(self, bootstrap_env):
        project, registry_dir = bootstrap_env
        result = _run_bootstrap("my project!", project, registry_dir)
        assert result.returncode == 1

    def test_non_git_project_fails(self, tmp_path):
        project = tmp_path / "not-a-repo"
        project.mkdir()
        registry_dir = tmp_path / "registries"
        registry_dir.mkdir()
        result = _run_bootstrap("test-project", project, registry_dir)
        assert result.returncode != 0


# --- Integration Test ---

class TestIntegration:
    @pytest.mark.skipif(
        not MAS_HARNESS.exists(),
        reason="mas-harness template not available"
    )
    def test_full_bootstrap_with_real_template(self, bootstrap_env):
        project, registry_dir = bootstrap_env
        result = _run_bootstrap("integration-test", project, registry_dir)
        assert result.returncode == 0

        registry = registry_dir / "integration-test"
        assert registry.is_dir()

        # Registry has correct structure
        files = [f for f in registry.rglob("*") if f.is_file()]
        assert len(files) == 41

        # Project is initialized
        assert (project / ".harness.json").exists()
        assert (project / "CLAUDE.md").exists()
        assert (project / ".agents").is_symlink()
        assert (project / ".claude" / "settings.local.json").exists()
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd harness-cli && python -m pytest tests/test_bootstrap.py -v 2>&1 | tail -5`
Expected: FAIL — `No module named 'setup.bootstrap'` or `FileNotFoundError`

- [ ] **Step 4: Commit tests**

```bash
git add harness-cli/setup/__init__.py harness-cli/tests/test_bootstrap.py
git commit -m "test(harness-cli): add bootstrap tests (TDD red phase)"
```

---

### Task 2: Implement bootstrap.py

**Files:**
- Create: `harness-cli/setup/bootstrap.py`

- [ ] **Step 1: Implement the bootstrap CLI**

```python
# setup/bootstrap.py
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
```

- [ ] **Step 2: Run tests**

Run: `cd harness-cli && python -m pytest tests/test_bootstrap.py -v`
Expected: All pass

- [ ] **Step 3: Run ALL tests (M1 + M2 + M3)**

Run: `cd harness-cli && python -m pytest -v --tb=short`
Expected: All pass (no regressions)

- [ ] **Step 4: Commit**

```bash
git add harness-cli/setup/bootstrap.py
git commit -m "feat(harness-cli): add bootstrap CLI for one-step project onboarding"
```

---

### Task 3: Integration test — real bootstrap

- [ ] **Step 1: Run bootstrap against a real temp project**

```bash
TMPDIR=$(mktemp -d)
mkdir -p "$TMPDIR/test-project" && cd "$TMPDIR/test-project" && git init
cd /home/aeonli/repos/proj-regs
python harness-cli/setup/bootstrap.py \
  --name bootstrap-test \
  --project "$TMPDIR/test-project" \
  --registry-dir "$TMPDIR/registries"
```

Expected: Success message.

- [ ] **Step 2: Verify registry**

```bash
find "$TMPDIR/registries/bootstrap-test" -type f | wc -l
```
Expected: `41`

```bash
head -3 "$TMPDIR/registries/bootstrap-test/00-Project-Memory.md"
```
Expected: `# bootstrap-test — Project Memory`

```bash
grep -c "MAS Harness" "$TMPDIR/registries/bootstrap-test/00-Project-Memory.md"
```
Expected: `0` (no harness-specific references)

- [ ] **Step 3: Verify project**

```bash
cat "$TMPDIR/test-project/.harness.json" | python3 -m json.tool | head -5
ls -la "$TMPDIR/test-project/.agents"
cat "$TMPDIR/test-project/.claude/settings.local.json" | python3 -m json.tool | head -10
```

Expected: All configured correctly.

- [ ] **Step 4: Cleanup**

```bash
rm -rf "$TMPDIR"
```

---

### Task 4: Final verification

- [ ] **Step 1: Run full test suite**

Run: `cd harness-cli && python -m pytest -v --tb=short`
Expected: ALL tests pass (M1 + M2 + M3)

- [ ] **Step 2: Verify file structure**

Run: `find harness-cli/setup -type f -not -path '*__pycache__*' | sort`
Expected:
```
harness-cli/setup/__init__.py
harness-cli/setup/bootstrap.py
harness-cli/setup/init_project.py
harness-cli/setup/templates/AGENTS.md.tpl
harness-cli/setup/templates/CLAUDE.md.tpl
```
