# M1.0 Enforcement Layer — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the enforcement hooks (path validation, spec cascade gate, post-PR-wait) and a setup script that installs them into target projects.

**Architecture:** Python hooks for synchronous file validation (path_validator, spec_cascade_gate), TypeScript hook for async GitHub polling (post_pr_wait). Shared utilities handle branch parsing and config loading. A setup script wires everything into a target project's `.claude/settings.local.json`.

**Tech Stack:** Python 3.10+ (pytest), TypeScript (vitest), Claude Code hooks protocol

**Spec:** `docs/superpowers/specs/2026-03-25-m1-enforcement-layer-design.md`

**Task execution order:** Tasks MUST be executed sequentially (1 → 8). Each task builds on prior ones.

---

## File Map

All paths relative to `harness-cli/` in the repo root.

| File | Purpose |
|---|---|
| `pyproject.toml` | Python project config with pytest |
| `package.json` | Node project config with vitest |
| `tsconfig.json` | TypeScript compiler config |
| `hooks/__init__.py` | Package marker |
| `hooks/utils/__init__.py` | Utils package marker |
| `hooks/utils/branch_parser.py` | Git branch → role + feature |
| `hooks/utils/config_loader.py` | .harness.json + context_map.json + feature folder resolver |
| `hooks/path_validator.py` | PreToolUse hook: block unauthorized writes |
| `hooks/spec_cascade_gate.py` | PreToolUse hook: block code before spec cascade |
| `hooks/post_pr_wait.ts` | PostToolUse hook: poll GitHub PR |
| `setup/init_project.py` | Setup script entry point |
| `setup/templates/CLAUDE.md.tpl` | Template for project's CLAUDE.md |
| `setup/templates/AGENTS.md.tpl` | Template for project's AGENTS.md |
| `tests/__init__.py` | Tests package marker |
| `tests/test_branch_parser.py` | Branch parser unit tests |
| `tests/test_config_loader.py` | Config loader unit tests |
| `tests/test_path_validator.py` | Path validator unit tests |
| `tests/test_spec_cascade_gate.py` | Spec cascade gate unit tests |
| `tests/test_post_pr_wait.ts` | Post-PR-wait unit tests |
| `tests/test_init_project.py` | Setup script integration tests |

---

## Tasks

### Task 1: Project scaffolding

**Files:**
- Create: `harness-cli/pyproject.toml`
- Create: `harness-cli/package.json`
- Create: `harness-cli/tsconfig.json`
- Create: `harness-cli/hooks/__init__.py`
- Create: `harness-cli/hooks/utils/__init__.py`
- Create: `harness-cli/tests/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "harness-cli"
version = "1.0.0"
description = "MAS Harness enforcement hooks and setup tooling"
requires-python = ">=3.10"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

- [ ] **Step 2: Create package.json**

```json
{
  "name": "harness-cli",
  "version": "1.0.0",
  "description": "MAS Harness enforcement hooks (TypeScript components)",
  "type": "module",
  "scripts": {
    "build": "tsc",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "devDependencies": {
    "typescript": "^5.4.0",
    "vitest": "^2.0.0",
    "@types/node": "^20.0.0"
  }
}
```

- [ ] **Step 3: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "moduleResolution": "bundler",
    "outDir": "./dist",
    "rootDir": ".",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "declaration": true
  },
  "include": ["hooks/**/*.ts", "tests/**/*.ts"],
  "exclude": ["node_modules", "dist"]
}
```

- [ ] **Step 4: Create package markers**

```python
# hooks/__init__.py
# (empty file)
```

```python
# hooks/utils/__init__.py
# (empty file)
```

```python
# tests/__init__.py
# (empty file)
```

- [ ] **Step 5: Install dependencies**

Run: `cd harness-cli && pip install pytest && npm install`

- [ ] **Step 6: Verify**

Run: `cd harness-cli && python -m pytest --collect-only 2>&1 | head -5`
Expected: `no tests ran` (no test files yet, but pytest runs)

Run: `cd harness-cli && npx vitest run 2>&1 | head -5`
Expected: No test files found (but vitest runs)

- [ ] **Step 7: Commit**

```bash
git add harness-cli/pyproject.toml harness-cli/package.json harness-cli/tsconfig.json harness-cli/hooks/__init__.py harness-cli/hooks/utils/__init__.py harness-cli/tests/__init__.py
git commit -m "feat(harness-cli): scaffold project with python + typescript config"
```

---

### Task 2: Shared utilities — branch_parser.py + tests

**Files:**
- Create: `harness-cli/hooks/utils/branch_parser.py`
- Create: `harness-cli/tests/test_branch_parser.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_branch_parser.py
import subprocess
from unittest.mock import patch

from hooks.utils.branch_parser import parse_branch


class TestParseBranch:
    """Branch parser: feat/<feature>/<role>[-<instance>]"""

    def test_worker_with_instance(self):
        with patch("hooks.utils.branch_parser._get_current_branch", return_value="feat/path-validation/worker-1"):
            result = parse_branch()
        assert result == {"feature": "path-validation", "role": "worker"}

    def test_sdet_unit(self):
        with patch("hooks.utils.branch_parser._get_current_branch", return_value="feat/my-feature/sdet-unit"):
            result = parse_branch()
        assert result == {"feature": "my-feature", "role": "sdet-unit"}

    def test_team_lead(self):
        with patch("hooks.utils.branch_parser._get_current_branch", return_value="feat/my-feature/team-lead"):
            result = parse_branch()
        assert result == {"feature": "my-feature", "role": "team-lead"}

    def test_main_branch_fallback(self):
        with patch("hooks.utils.branch_parser._get_current_branch", return_value="main"):
            result = parse_branch()
        assert result == {"feature": None, "role": "orchestrator"}

    def test_develop_branch_fallback(self):
        with patch("hooks.utils.branch_parser._get_current_branch", return_value="develop"):
            result = parse_branch()
        assert result == {"feature": None, "role": "orchestrator"}

    def test_missing_role_segment(self):
        with patch("hooks.utils.branch_parser._get_current_branch", return_value="feat/no-role"):
            result = parse_branch()
        assert result == {"feature": "no-role", "role": "orchestrator"}

    def test_extra_segments_ignored(self):
        with patch("hooks.utils.branch_parser._get_current_branch", return_value="feat/my-feature/worker/extra"):
            result = parse_branch()
        assert result == {"feature": "my-feature", "role": "worker"}

    def test_special_characters_in_feature(self):
        with patch("hooks.utils.branch_parser._get_current_branch", return_value="feat/fix-#123/worker-1"):
            result = parse_branch()
        assert result == {"feature": "fix-#123", "role": "worker"}

    def test_detached_head(self):
        with patch("hooks.utils.branch_parser._get_current_branch", return_value=""):
            result = parse_branch()
        assert result == {"feature": None, "role": "orchestrator"}

    def test_sonders_role(self):
        with patch("hooks.utils.branch_parser._get_current_branch", return_value="feat/new-arch/sonders"):
            result = parse_branch()
        assert result == {"feature": "new-arch", "role": "sonders"}

    def test_behavior_spec_writer(self):
        with patch("hooks.utils.branch_parser._get_current_branch", return_value="feat/auth/behavior-spec-writer"):
            result = parse_branch()
        assert result == {"feature": "auth", "role": "behavior-spec-writer"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd harness-cli && python -m pytest tests/test_branch_parser.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'hooks.utils.branch_parser'`

- [ ] **Step 3: Implement branch_parser.py**

```python
# hooks/utils/branch_parser.py
"""Parse git branch name to extract agent role and feature."""

import re
import subprocess
import sys


def _get_current_branch() -> str:
    """Get the current git branch name. Returns empty string on detached HEAD."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def parse_branch() -> dict:
    """Parse current branch into feature and role.

    Convention: feat/<feature-name>/<role>[-<instance>]

    Returns:
        {"feature": str|None, "role": str}
        Fallback: {"feature": None, "role": "orchestrator"}
    """
    branch = _get_current_branch()
    if not branch:
        return {"feature": None, "role": "orchestrator"}

    # Match: feat/<feature>/<role>[-<instance>][/extra...]
    match = re.match(r"^feat/([^/]+)/([^/]+?)(?:-\d+)?(?:/.*)?$", branch)
    if not match:
        # Check if it's feat/<feature> without a role
        feat_only = re.match(r"^feat/([^/]+)$", branch)
        if feat_only:
            return {"feature": feat_only.group(1), "role": "orchestrator"}
        return {"feature": None, "role": "orchestrator"}

    feature = match.group(1)
    role = match.group(2)
    return {"feature": feature, "role": role}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd harness-cli && python -m pytest tests/test_branch_parser.py -v`
Expected: 11 passed

- [ ] **Step 5: Commit**

```bash
git add harness-cli/hooks/utils/branch_parser.py harness-cli/tests/test_branch_parser.py
git commit -m "feat(harness-cli): add branch parser utility with tests"
```

---

### Task 3: Shared utilities — config_loader.py + tests

**Files:**
- Create: `harness-cli/hooks/utils/config_loader.py`
- Create: `harness-cli/tests/test_config_loader.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_config_loader.py
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from hooks.utils.config_loader import (
    find_project_root,
    load_harness_config,
    load_context_map,
    resolve_feature_folder,
)


class TestFindProjectRoot:
    def test_finds_harness_json(self, tmp_path):
        harness_json = tmp_path / ".harness.json"
        harness_json.write_text('{"version": "1.0.0"}')
        subdir = tmp_path / "src" / "deep"
        subdir.mkdir(parents=True)
        result = find_project_root(str(subdir))
        assert result == str(tmp_path)

    def test_returns_none_when_missing(self, tmp_path):
        result = find_project_root(str(tmp_path))
        assert result is None


class TestLoadHarnessConfig:
    def test_loads_valid_config(self, tmp_path):
        config = {
            "registry_path": "/path/to/registry",
            "harness_cli_path": "/path/to/cli",
            "version": "1.0.0"
        }
        (tmp_path / ".harness.json").write_text(json.dumps(config))
        result = load_harness_config(str(tmp_path))
        assert result["registry_path"] == "/path/to/registry"
        assert result["harness_cli_path"] == "/path/to/cli"

    def test_returns_none_when_missing(self, tmp_path):
        result = load_harness_config(str(tmp_path))
        assert result is None


class TestLoadContextMap:
    def test_loads_all_12_roles(self, tmp_path):
        registry = tmp_path / "registry"
        registry.mkdir()
        context_map = {
            "version": "2.0",
            "agent_role_context": {
                "orchestrator": {"required_docs": []},
                "sonders": {"required_docs": []},
                "negator": {"required_docs": []},
                "behavior-spec-writer": {"required_docs": []},
                "test-spec-writer": {"required_docs": []},
                "team-lead": {"required_docs": []},
                "worker": {"required_docs": []},
                "sdet-unit": {"required_docs": []},
                "sdet-integration": {"required_docs": []},
                "sdet-e2e": {"required_docs": []},
                "auditor": {"required_docs": []},
                "regression-runner": {"required_docs": []},
            },
            "path_based_rules": []
        }
        (registry / "context_map.json").write_text(json.dumps(context_map))
        result = load_context_map(str(registry))
        assert len(result["agent_role_context"]) == 12

    def test_raises_on_missing_file(self, tmp_path):
        import pytest
        with pytest.raises(FileNotFoundError):
            load_context_map(str(tmp_path))


class TestResolveFeatureFolder:
    def test_resolves_with_date_prefix(self, tmp_path):
        changes = tmp_path / "runtime" / "openspec" / "changes"
        changes.mkdir(parents=True)
        (changes / "2026-03-25-path-validation").mkdir()
        result = resolve_feature_folder(str(tmp_path), "path-validation")
        assert result == str(changes / "2026-03-25-path-validation")

    def test_returns_most_recent_on_multiple(self, tmp_path):
        changes = tmp_path / "runtime" / "openspec" / "changes"
        changes.mkdir(parents=True)
        (changes / "2026-03-20-auth").mkdir()
        (changes / "2026-03-25-auth").mkdir()
        result = resolve_feature_folder(str(tmp_path), "auth")
        assert "2026-03-25-auth" in result

    def test_returns_none_when_no_match(self, tmp_path):
        changes = tmp_path / "runtime" / "openspec" / "changes"
        changes.mkdir(parents=True)
        result = resolve_feature_folder(str(tmp_path), "nonexistent")
        assert result is None

    def test_returns_none_when_no_changes_dir(self, tmp_path):
        result = resolve_feature_folder(str(tmp_path), "anything")
        assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd harness-cli && python -m pytest tests/test_config_loader.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement config_loader.py**

```python
# hooks/utils/config_loader.py
"""Load .harness.json, context_map.json, and resolve feature folders."""

import json
import os
import sys
from pathlib import Path
from typing import Optional


def find_project_root(start_path: str) -> Optional[str]:
    """Walk up from start_path to find directory containing .harness.json."""
    current = Path(start_path).resolve()
    while current != current.parent:
        if (current / ".harness.json").exists():
            return str(current)
        current = current.parent
    # Check root
    if (current / ".harness.json").exists():
        return str(current)
    return None


def load_harness_config(project_root: str) -> Optional[dict]:
    """Load .harness.json from project root. Returns None if missing."""
    config_path = Path(project_root) / ".harness.json"
    if not config_path.exists():
        return None
    with open(config_path) as f:
        return json.load(f)


def load_context_map(registry_path: str) -> dict:
    """Load context_map.json from registry. Raises FileNotFoundError if missing."""
    cm_path = Path(registry_path) / "context_map.json"
    if not cm_path.exists():
        raise FileNotFoundError(f"context_map.json not found at {cm_path}")
    with open(cm_path) as f:
        return json.load(f)


def resolve_feature_folder(registry_path: str, feature_name: str) -> Optional[str]:
    """Resolve feature name to OpenSpec folder, handling date prefixes.

    Scans runtime/openspec/changes/ for folders ending with -<feature_name>.
    Returns most recent (by date prefix) if multiple match. None if no match.
    """
    changes_dir = Path(registry_path) / "runtime" / "openspec" / "changes"
    if not changes_dir.exists():
        return None

    matches = []
    for entry in changes_dir.iterdir():
        if entry.is_dir() and entry.name.endswith(f"-{feature_name}"):
            matches.append(entry)
        elif entry.is_dir() and entry.name == feature_name:
            matches.append(entry)

    if not matches:
        return None

    # Sort by name (date prefix ensures chronological order) — take most recent
    matches.sort(key=lambda p: p.name, reverse=True)
    return str(matches[0])
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd harness-cli && python -m pytest tests/test_config_loader.py -v`
Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add harness-cli/hooks/utils/config_loader.py harness-cli/tests/test_config_loader.py
git commit -m "feat(harness-cli): add config loader utility with tests"
```

---

### Task 4: Path validation hook + tests

**Files:**
- Create: `harness-cli/hooks/path_validator.py`
- Create: `harness-cli/tests/test_path_validator.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_path_validator.py
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from hooks.path_validator import validate_path, get_allowed_paths, parse_worker_file_scope


class TestParseWorkerFileScope:
    """Parse tasks.md to extract file scope for a specific worker."""

    def test_parses_task_1_scope(self):
        tasks_md = """# Tasks: Auth

## Task Checklist

### Task 1: Add auth handler

**File scope:**
- `src/auth/handler.py`
- `src/auth/utils.py`

**Assignee:** @Worker

### Task 2: Add auth tests

**File scope:**
- `tests/test_auth.py`

**Assignee:** @Worker
"""
        result = parse_worker_file_scope(tasks_md, worker_instance=1)
        assert result == ["src/auth/handler.py", "src/auth/utils.py"]

    def test_parses_task_2_scope(self):
        tasks_md = """### Task 1: First
**File scope:**
- `src/a.py`

### Task 2: Second
**File scope:**
- `src/b.py`
- `src/c.py`
"""
        result = parse_worker_file_scope(tasks_md, worker_instance=2)
        assert result == ["src/b.py", "src/c.py"]

    def test_returns_empty_for_out_of_range(self):
        tasks_md = """### Task 1: Only one
**File scope:**
- `src/a.py`
"""
        result = parse_worker_file_scope(tasks_md, worker_instance=5)
        assert result == []

    def test_returns_empty_for_empty_input(self):
        result = parse_worker_file_scope("", worker_instance=1)
        assert result == []


class TestGetAllowedPaths:
    """Determine allowed write paths per role."""

    def test_orchestrator_blocked(self):
        result = get_allowed_paths("orchestrator", feature=None, registry_path=None)
        assert result == []

    def test_auditor_blocked(self):
        result = get_allowed_paths("auditor", feature=None, registry_path=None)
        assert result == []

    def test_regression_runner_blocked(self):
        result = get_allowed_paths("regression-runner", feature=None, registry_path=None)
        assert result == []

    def test_sonders_allowed_blueprint_design(self):
        paths, is_abs = get_allowed_paths("sonders", feature=None, registry_path="/reg")
        assert is_abs is True
        assert any("blueprint/design" in p for p in paths)

    def test_sdet_unit_allowed_tests(self):
        paths, is_abs = get_allowed_paths("sdet-unit", feature=None, registry_path=None)
        assert is_abs is False
        assert "tests/**/*" in paths
        assert "test/**/*" in paths

    def test_behavior_spec_writer_scoped(self, tmp_path):
        registry = tmp_path / "reg"
        changes = registry / "runtime" / "openspec" / "changes" / "2026-03-25-auth"
        changes.mkdir(parents=True)
        paths, is_abs = get_allowed_paths("behavior-spec-writer", feature="auth", registry_path=str(registry))
        assert is_abs is True
        assert any("behavior_spec.md" in p for p in paths)


class TestValidatePath:
    """End-to-end path validation."""

    def test_worker_allowed_in_scope(self, tmp_path):
        registry = tmp_path / "registry"
        changes = registry / "runtime" / "openspec" / "changes" / "2026-03-25-auth"
        changes.mkdir(parents=True)
        (changes / "tasks.md").write_text(
            "### Task 1: Handler\n**File scope:**\n- `src/handler.py`\n"
        )
        project_root = str(tmp_path / "project")
        result = validate_path(
            role="worker", feature="auth", file_path="src/handler.py",
            registry_path=str(registry), worker_instance=1, project_root=project_root
        )
        assert result["decision"] == "allow"

    def test_worker_blocked_outside_scope(self, tmp_path):
        registry = tmp_path / "registry"
        changes = registry / "runtime" / "openspec" / "changes" / "2026-03-25-auth"
        changes.mkdir(parents=True)
        (changes / "tasks.md").write_text(
            "### Task 1: Handler\n**File scope:**\n- `src/handler.py`\n"
        )
        project_root = str(tmp_path / "project")
        result = validate_path(
            role="worker", feature="auth", file_path="src/other.py",
            registry_path=str(registry), worker_instance=1, project_root=project_root
        )
        assert result["decision"] == "block"

    def test_worker_1_blocked_from_task_2_scope(self, tmp_path):
        registry = tmp_path / "registry"
        changes = registry / "runtime" / "openspec" / "changes" / "2026-03-25-auth"
        changes.mkdir(parents=True)
        (changes / "tasks.md").write_text(
            "### Task 1: A\n**File scope:**\n- `src/a.py`\n\n### Task 2: B\n**File scope:**\n- `src/b.py`\n"
        )
        project_root = str(tmp_path / "project")
        result = validate_path(
            role="worker", feature="auth", file_path="src/b.py",
            registry_path=str(registry), worker_instance=1, project_root=project_root
        )
        assert result["decision"] == "block"

    def test_worker_blocked_no_tasks(self):
        result = validate_path(
            role="worker", feature="auth", file_path="src/foo.py",
            registry_path="/nonexistent", worker_instance=1, project_root="/project"
        )
        assert result["decision"] == "block"

    def test_orchestrator_always_blocked(self):
        result = validate_path(
            role="orchestrator", feature=None, file_path="anything.py",
            registry_path=None, worker_instance=None, project_root="/project"
        )
        assert result["decision"] == "block"

    def test_sonders_allowed_blueprint_design(self, tmp_path):
        registry = tmp_path / "reg"
        (registry / "blueprint" / "design").mkdir(parents=True)
        result = validate_path(
            role="sonders", feature=None, file_path="blueprint/design/arch.md",
            registry_path=str(registry), worker_instance=None, project_root="/project",
            file_path_abs=str(registry / "blueprint" / "design" / "arch.md"),
        )
        assert result["decision"] == "allow"

    def test_sonders_blocked_src(self, tmp_path):
        registry = tmp_path / "reg"
        registry.mkdir()
        result = validate_path(
            role="sonders", feature=None, file_path="src/app.py",
            registry_path=str(registry), worker_instance=None, project_root="/project",
            file_path_abs="/project/src/app.py",
        )
        assert result["decision"] == "block"

    def test_sdet_allowed_tests(self):
        result = validate_path(
            role="sdet-unit", feature=None, file_path="tests/test_auth.py",
            registry_path=None, worker_instance=None, project_root="/project"
        )
        assert result["decision"] == "allow"

    def test_sdet_blocked_src(self):
        result = validate_path(
            role="sdet-unit", feature=None, file_path="src/auth.py",
            registry_path=None, worker_instance=None, project_root="/project"
        )
        assert result["decision"] == "block"

    def test_degraded_mode_no_config(self):
        """When .harness.json is not found, allow (non-breaking degradation)."""
        result = validate_path(
            role=None, feature=None, file_path="anything.py",
            registry_path=None, worker_instance=None, project_root=None
        )
        assert result["decision"] == "allow"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd harness-cli && python -m pytest tests/test_path_validator.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement path_validator.py**

```python
# hooks/path_validator.py
"""PreToolUse hook: validates write paths based on agent role.

Reads tool use context from stdin, outputs decision to stdout.
"""

import json
import re
import sys
from pathlib import Path, PurePath
from typing import Optional

from hooks.utils.branch_parser import parse_branch, _get_current_branch
from hooks.utils.config_loader import (
    find_project_root,
    load_harness_config,
    resolve_feature_folder,
)


def matches_pattern(file_path: str, pattern: str) -> bool:
    """Match a file path against a glob pattern, supporting ** for recursion."""
    return PurePath(file_path).match(pattern)


# Roles that are never allowed to write
NO_WRITE_ROLES = {"orchestrator", "auditor", "regression-runner"}

# Roles that write to the REGISTRY (not the project)
REGISTRY_WRITE_ROLES = {"behavior-spec-writer", "test-spec-writer", "team-lead", "sonders", "negator"}

# Static path patterns per role (project-relative)
ROLE_PATHS = {
    "sdet-unit": ["tests/**/*", "test/**/*", "*_test.*", "test_*.*"],
    "sdet-integration": ["tests/**/*", "test/**/*", "*_test.*", "test_*.*"],
    "sdet-e2e": ["tests/**/*", "test/**/*", "*_test.*", "test_*.*"],
}


def parse_worker_file_scope(tasks_md: str, worker_instance: int) -> list[str]:
    """Parse tasks.md and return file scope for the given worker instance.

    worker_instance maps to task number: worker-1 → Task 1, worker-2 → Task 2.
    """
    if not tasks_md.strip():
        return []

    # Split into task blocks by ### Task N: headings
    task_blocks = re.split(r"(?=### Task \d+:)", tasks_md)
    task_blocks = [b for b in task_blocks if b.strip().startswith("### Task")]

    if worker_instance < 1 or worker_instance > len(task_blocks):
        return []

    block = task_blocks[worker_instance - 1]

    # Extract file scope lines: - `path/to/file`
    scope = []
    in_file_scope = False
    for line in block.split("\n"):
        if "**File scope:**" in line:
            in_file_scope = True
            continue
        if in_file_scope:
            match = re.match(r"\s*-\s*`([^`]+)`", line)
            if match:
                scope.append(match.group(1))
            elif line.strip() and not line.strip().startswith("-"):
                in_file_scope = False

    return scope


def get_allowed_paths(
    role: str, feature: Optional[str], registry_path: Optional[str]
) -> tuple[list[str], bool]:
    """Return (allowed_path_patterns, is_absolute).

    is_absolute=True means paths are absolute (registry-based roles).
    is_absolute=False means paths are project-relative patterns.
    """
    if role in NO_WRITE_ROLES:
        return [], False

    if role in ROLE_PATHS:
        return ROLE_PATHS[role], False

    # Registry-based roles — return ABSOLUTE paths
    if role in REGISTRY_WRITE_ROLES and registry_path:
        if role in ("sonders", "negator"):
            return [str(Path(registry_path) / "blueprint" / "design" / "*")], True

        if feature:
            feature_folder = resolve_feature_folder(registry_path, feature)
            if feature_folder:
                if role == "behavior-spec-writer":
                    return [str(Path(feature_folder) / "behavior_spec.md")], True
                elif role == "test-spec-writer":
                    return [str(Path(feature_folder) / "test_spec.md")], True
                elif role == "team-lead":
                    return [
                        str(Path(feature_folder) / "tasks.md"),
                        str(Path(feature_folder) / "status.md"),
                    ], True

    # For roles that need feature context but don't have it
    if role in ("behavior-spec-writer", "test-spec-writer", "team-lead", "worker"):
        return [], False

    # Unknown role — allow (non-breaking)
    return ["**/*"], False


def validate_path(
    role: Optional[str],
    feature: Optional[str],
    file_path: str,
    registry_path: Optional[str],
    worker_instance: Optional[int],
    project_root: Optional[str],
    file_path_abs: Optional[str] = None,
) -> dict:
    """Validate whether a role can write to a file path.

    file_path: project-relative path (for project-based roles)
    file_path_abs: absolute path (for registry-based roles)

    Returns: {"decision": "allow"} or {"decision": "block", "reason": "..."}
    """
    file_path_abs = file_path_abs or file_path

    # Degraded mode — no config, allow everything
    if role is None and project_root is None:
        return {"decision": "allow"}

    if role in NO_WRITE_ROLES:
        return {
            "decision": "block",
            "reason": f"Role '{role}' is not allowed to write any files.",
        }

    # Worker — dynamic file scope from tasks.md
    if role == "worker":
        if not registry_path or not feature:
            return {
                "decision": "block",
                "reason": "Worker has no feature context. Cannot determine file scope.",
            }
        feature_folder = resolve_feature_folder(registry_path, feature)
        if not feature_folder:
            return {
                "decision": "block",
                "reason": f"No OpenSpec folder found for feature '{feature}'.",
            }
        tasks_path = Path(feature_folder) / "tasks.md"
        if not tasks_path.exists():
            return {
                "decision": "block",
                "reason": f"tasks.md not found for feature '{feature}'.",
            }
        instance = worker_instance or 1
        allowed = parse_worker_file_scope(tasks_path.read_text(), instance)
        if not allowed:
            return {
                "decision": "block",
                "reason": f"No file scope found for worker-{instance} in tasks.md.",
            }
        if file_path in allowed:
            return {"decision": "allow"}
        return {
            "decision": "block",
            "reason": f"Role 'worker-{instance}' is not allowed to write to '{file_path}'. Allowed: {allowed}",
        }

    # Static and registry-based roles
    allowed_patterns, is_absolute = get_allowed_paths(role, feature, registry_path)
    if not allowed_patterns:
        return {
            "decision": "block",
            "reason": f"Role '{role}' has no allowed write paths.",
        }

    # For absolute patterns (registry roles), compare against the absolute file path
    compare_path = file_path_abs if is_absolute else file_path
    for pattern in allowed_patterns:
        if matches_pattern(compare_path, pattern):
            return {"decision": "allow"}

    return {
        "decision": "block",
        "reason": f"Role '{role}' is not allowed to write to '{file_path}'. Allowed patterns: {allowed_patterns}",
    }


def main():
    """Entry point for Claude Code hook. Reads stdin, writes stdout."""
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        # Can't parse input — allow (non-breaking)
        json.dump({"decision": "allow"}, sys.stdout)
        return

    file_path_abs = input_data.get("tool_input", {}).get("file_path", "")

    # Find project root and load config
    project_root = find_project_root(os.getcwd())
    if not project_root:
        # No .harness.json — degraded mode, allow
        json.dump({"decision": "allow"}, sys.stdout)
        return

    config = load_harness_config(project_root)
    registry_path = config.get("registry_path") if config else None

    # Convert absolute path to project-relative
    try:
        file_path = str(Path(file_path_abs).relative_to(project_root))
    except ValueError:
        file_path = file_path_abs

    # Parse branch for role, feature, and worker instance (single git call)
    raw_branch = _get_current_branch()
    branch_info = parse_branch()
    role = branch_info["role"]
    feature = branch_info["feature"]

    worker_instance = None
    if role == "worker":
        match = re.search(r"worker-(\d+)", raw_branch)
        worker_instance = int(match.group(1)) if match else 1

    result = validate_path(
        role, feature, file_path, registry_path,
        worker_instance, project_root, file_path_abs=file_path_abs,
    )
    json.dump(result, sys.stdout)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd harness-cli && python -m pytest tests/test_path_validator.py -v`
Expected: All passed

- [ ] **Step 5: Commit**

```bash
git add harness-cli/hooks/path_validator.py harness-cli/tests/test_path_validator.py
git commit -m "feat(harness-cli): add path validation hook with tests"
```

---

### Task 5: Spec cascade gate hook + tests

**Files:**
- Create: `harness-cli/hooks/spec_cascade_gate.py`
- Create: `harness-cli/tests/test_spec_cascade_gate.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_spec_cascade_gate.py
import json
from pathlib import Path
from unittest.mock import patch

from hooks.spec_cascade_gate import (
    is_source_file,
    check_spec_cascade,
    read_phase_from_status,
)


class TestIsSourceFile:
    """Determine if a file is a source file (requires cascade check)."""

    def test_python_source(self):
        assert is_source_file("src/app.py") is True

    def test_test_file_excluded(self):
        assert is_source_file("tests/test_app.py") is False

    def test_test_dir_excluded(self):
        assert is_source_file("test/test_app.py") is False

    def test_markdown_excluded(self):
        assert is_source_file("docs/readme.md") is False

    def test_json_config_excluded(self):
        assert is_source_file("package.json") is False

    def test_yaml_excluded(self):
        assert is_source_file(".github/workflows/ci.yml") is False

    def test_gitignore_excluded(self):
        assert is_source_file(".gitignore") is False

    def test_harness_json_excluded(self):
        assert is_source_file(".harness.json") is False

    def test_claude_dir_excluded(self):
        assert is_source_file(".claude/settings.json") is False

    def test_agents_dir_excluded(self):
        assert is_source_file(".agents/orchestrator.md") is False

    def test_toml_excluded(self):
        assert is_source_file("pyproject.toml") is False

    def test_tsx_source(self):
        assert is_source_file("src/components/App.tsx") is True

    def test_test_suffix_excluded(self):
        assert is_source_file("app_test.py") is False

    def test_test_prefix_excluded(self):
        assert is_source_file("test_app.py") is False

    def test_registry_file_excluded(self):
        assert is_source_file(
            "runtime/openspec/changes/auth/proposal.md",
            registry_path="/reg",
            file_path_abs="/reg/runtime/openspec/changes/auth/proposal.md"
        ) is False

    def test_nested_test_dir_excluded(self):
        """PurePath.match supports ** for recursive matching."""
        assert is_source_file("tests/unit/deep/test_auth.py") is False


class TestReadPhaseFromStatus:
    def test_reads_execution_phase(self):
        status_md = "## Current Phase\n`execution`\n"
        assert read_phase_from_status(status_md) == "execution"

    def test_reads_design_phase(self):
        status_md = "## Current Phase\n`design`\n"
        assert read_phase_from_status(status_md) == "design"

    def test_reads_testing_phase(self):
        status_md = "## Current Phase\n`testing`\n"
        assert read_phase_from_status(status_md) == "testing"

    def test_returns_none_for_empty(self):
        assert read_phase_from_status("") is None


class TestCheckSpecCascade:
    """Check if spec cascade is complete for a feature."""

    def test_all_complete_execution_phase(self, tmp_path):
        feature = tmp_path / "feature"
        feature.mkdir()
        (feature / "proposal.md").write_text("A" * 60)
        (feature / "behavior_spec.md").write_text("B" * 60)
        (feature / "test_spec.md").write_text("C" * 60)
        (feature / "status.md").write_text("## Current Phase\n`execution`\n")
        result = check_spec_cascade(str(feature))
        assert result["decision"] == "allow"

    def test_missing_behavior_spec(self, tmp_path):
        feature = tmp_path / "feature"
        feature.mkdir()
        (feature / "proposal.md").write_text("A" * 60)
        (feature / "test_spec.md").write_text("C" * 60)
        (feature / "status.md").write_text("## Current Phase\n`execution`\n")
        result = check_spec_cascade(str(feature))
        assert result["decision"] == "block"
        assert "behavior_spec.md" in result["reason"]

    def test_empty_test_spec(self, tmp_path):
        feature = tmp_path / "feature"
        feature.mkdir()
        (feature / "proposal.md").write_text("A" * 60)
        (feature / "behavior_spec.md").write_text("B" * 60)
        (feature / "test_spec.md").write_text("short")  # <50 chars
        (feature / "status.md").write_text("## Current Phase\n`execution`\n")
        result = check_spec_cascade(str(feature))
        assert result["decision"] == "block"

    def test_design_phase_blocks(self, tmp_path):
        feature = tmp_path / "feature"
        feature.mkdir()
        (feature / "proposal.md").write_text("A" * 60)
        (feature / "behavior_spec.md").write_text("B" * 60)
        (feature / "test_spec.md").write_text("C" * 60)
        (feature / "status.md").write_text("## Current Phase\n`design`\n")
        result = check_spec_cascade(str(feature))
        assert result["decision"] == "block"

    def test_spec_cascade_phase_blocks(self, tmp_path):
        feature = tmp_path / "feature"
        feature.mkdir()
        (feature / "proposal.md").write_text("A" * 60)
        (feature / "behavior_spec.md").write_text("B" * 60)
        (feature / "test_spec.md").write_text("C" * 60)
        (feature / "status.md").write_text("## Current Phase\n`spec-cascade`\n")
        result = check_spec_cascade(str(feature))
        assert result["decision"] == "block"

    def test_testing_phase_blocks(self, tmp_path):
        feature = tmp_path / "feature"
        feature.mkdir()
        (feature / "proposal.md").write_text("A" * 60)
        (feature / "behavior_spec.md").write_text("B" * 60)
        (feature / "test_spec.md").write_text("C" * 60)
        (feature / "status.md").write_text("## Current Phase\n`testing`\n")
        result = check_spec_cascade(str(feature))
        assert result["decision"] == "block"

    def test_quality_gate_phase_allows(self, tmp_path):
        feature = tmp_path / "feature"
        feature.mkdir()
        (feature / "proposal.md").write_text("A" * 60)
        (feature / "behavior_spec.md").write_text("B" * 60)
        (feature / "test_spec.md").write_text("C" * 60)
        (feature / "status.md").write_text("## Current Phase\n`quality-gate`\n")
        result = check_spec_cascade(str(feature))
        assert result["decision"] == "allow"

    def test_no_feature_folder(self):
        result = check_spec_cascade("/nonexistent/path")
        assert result["decision"] == "block"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd harness-cli && python -m pytest tests/test_spec_cascade_gate.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement spec_cascade_gate.py**

```python
# hooks/spec_cascade_gate.py
"""PreToolUse hook: blocks source code writes until spec cascade is complete.

Reads tool use context from stdin, outputs decision to stdout.
"""

import json
import os
import re
import sys
from pathlib import Path, PurePath
from typing import Optional

from hooks.utils.branch_parser import parse_branch
from hooks.utils.config_loader import (
    find_project_root,
    load_harness_config,
    resolve_feature_folder,
)

# Files excluded from the cascade check (not source code)
EXCLUSION_PATTERNS = [
    "tests/**/*", "test/**/*", "*_test.*", "test_*.*",
    "*.md",
    ".harness.json", ".gitignore", "*.toml", "*.json", "*.yaml", "*.yml",
    ".claude/**/*", ".agents/**/*", ".github/**/*",
]

# Phases that allow source code writes
ALLOWED_PHASES = {"execution", "quality-gate", "pr-review"}

# Minimum content length to consider a spec file non-empty (not just template)
MIN_SPEC_LENGTH = 50

# Required spec files for the cascade
REQUIRED_SPECS = ["proposal.md", "behavior_spec.md", "test_spec.md"]


def is_source_file(file_path: str, registry_path: Optional[str] = None, file_path_abs: Optional[str] = None) -> bool:
    """Check if a file is a source file (requires cascade check).

    Returns False if the file matches any exclusion pattern or is inside the registry.
    """
    for pattern in EXCLUSION_PATTERNS:
        if PurePath(file_path).match(pattern):
            return False

    # Exclude files inside the registry directory
    if registry_path and file_path_abs:
        try:
            Path(file_path_abs).relative_to(registry_path)
            return False  # File is inside the registry
        except ValueError:
            pass

    return True


def read_phase_from_status(status_content: str) -> Optional[str]:
    """Extract the current phase from status.md content."""
    match = re.search(r"`(\w[\w-]*)`", status_content)
    return match.group(1) if match else None


def check_spec_cascade(feature_folder: str) -> dict:
    """Check if the spec cascade is complete for a feature.

    Returns: {"decision": "allow"} or {"decision": "block", "reason": "..."}
    """
    feature_path = Path(feature_folder)
    if not feature_path.exists():
        return {
            "decision": "block",
            "reason": f"OpenSpec folder not found: {feature_folder}",
        }

    # Check required spec files exist and are non-empty
    missing = []
    for spec_file in REQUIRED_SPECS:
        spec_path = feature_path / spec_file
        if not spec_path.exists():
            missing.append(f"{spec_file} (missing)")
        elif len(spec_path.read_text().strip()) < MIN_SPEC_LENGTH:
            missing.append(f"{spec_file} (too short, likely template)")

    if missing:
        return {
            "decision": "block",
            "reason": f"Spec cascade incomplete. Issues: {', '.join(missing)}",
        }

    # Check phase
    status_path = feature_path / "status.md"
    if not status_path.exists():
        return {
            "decision": "block",
            "reason": "status.md not found in OpenSpec folder.",
        }

    phase = read_phase_from_status(status_path.read_text())
    if phase not in ALLOWED_PHASES:
        return {
            "decision": "block",
            "reason": f"Current phase is '{phase}'. Code implementation requires phase 'execution' or later.",
        }

    return {"decision": "allow"}


def main():
    """Entry point for Claude Code hook."""
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        json.dump({"decision": "allow"}, sys.stdout)
        return

    file_path_abs = input_data.get("tool_input", {}).get("file_path", "")

    # Find project root
    project_root = find_project_root(os.getcwd())
    if not project_root:
        json.dump({"decision": "allow"}, sys.stdout)
        return

    # Convert to relative path
    try:
        file_path = str(Path(file_path_abs).relative_to(project_root))
    except ValueError:
        file_path = file_path_abs

    # Load config early — needed for registry path exclusion
    config = load_harness_config(project_root)
    if not config:
        json.dump({"decision": "allow"}, sys.stdout)
        return

    registry_path = config.get("registry_path")

    # Check if it's a source file (excludes tests, config, registry files)
    if not is_source_file(file_path, registry_path=registry_path, file_path_abs=file_path_abs):
        json.dump({"decision": "allow"}, sys.stdout)
        return

    # Parse branch
    branch_info = parse_branch()
    feature = branch_info["feature"]
    if not feature:
        # Not on a feature branch — allow (no cascade to check)
        json.dump({"decision": "allow"}, sys.stdout)
        return

    if not registry_path:
        json.dump({"decision": "allow"}, sys.stdout)
        return

    feature_folder = resolve_feature_folder(registry_path, feature)
    if not feature_folder:
        json.dump({
            "decision": "block",
            "reason": f"No OpenSpec found for feature '{feature}'.",
        }, sys.stdout)
        return

    result = check_spec_cascade(feature_folder)
    json.dump(result, sys.stdout)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd harness-cli && python -m pytest tests/test_spec_cascade_gate.py -v`
Expected: All passed

- [ ] **Step 5: Run all Python tests**

Run: `cd harness-cli && python -m pytest -v`
Expected: All tests pass (branch_parser + config_loader + path_validator + spec_cascade_gate)

- [ ] **Step 6: Commit**

```bash
git add harness-cli/hooks/spec_cascade_gate.py harness-cli/tests/test_spec_cascade_gate.py
git commit -m "feat(harness-cli): add spec cascade gate hook with tests"
```

---

### Task 6: Post-PR-wait hook (TypeScript) + tests

**Files:**
- Create: `harness-cli/hooks/post_pr_wait.ts`
- Create: `harness-cli/tests/test_post_pr_wait.ts`

- [ ] **Step 1: Write failing tests**

```typescript
// tests/test_post_pr_wait.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  parsePrUrl,
  buildFeedbackReport,
  PostPrWaitResult,
} from '../hooks/post_pr_wait.js';

describe('parsePrUrl', () => {
  it('extracts owner, repo, and PR number from URL', () => {
    const result = parsePrUrl('https://github.com/acme/myrepo/pull/42');
    expect(result).toEqual({ owner: 'acme', repo: 'myrepo', pr_number: 42 });
  });

  it('handles URL with trailing newline', () => {
    const result = parsePrUrl('https://github.com/acme/myrepo/pull/42\n');
    expect(result).toEqual({ owner: 'acme', repo: 'myrepo', pr_number: 42 });
  });

  it('returns null for non-PR output', () => {
    const result = parsePrUrl('Created branch feat/auth');
    expect(result).toBeNull();
  });

  it('returns null for empty string', () => {
    const result = parsePrUrl('');
    expect(result).toBeNull();
  });

  it('extracts from multi-line output', () => {
    const output = 'Creating pull request...\nhttps://github.com/acme/repo/pull/99\n';
    const result = parsePrUrl(output);
    expect(result).toEqual({ owner: 'acme', repo: 'repo', pr_number: 99 });
  });
});

describe('buildFeedbackReport', () => {
  it('builds success report', () => {
    const result = buildFeedbackReport({
      checks_passed: true,
      reviews: [{ state: 'APPROVED', user: 'bot' }],
      comments: [{ body: 'LGTM', user: 'reviewer' }],
    });
    expect(result.decision).toBe('allow');
    expect(result.feedback.checks_passed).toBe(true);
    expect(result.feedback.summary).toContain('1 review');
    expect(result.feedback.summary).toContain('1 comment');
  });

  it('builds failure report', () => {
    const result = buildFeedbackReport({
      checks_passed: false,
      reviews: [],
      comments: [],
    });
    expect(result.decision).toBe('allow');
    expect(result.feedback.checks_passed).toBe(false);
    expect(result.feedback.summary).toContain('FAILED');
  });

  it('builds timeout report', () => {
    const result = buildFeedbackReport({ timeout: true });
    expect(result.decision).toBe('allow');
    expect(result.feedback.timeout).toBe(true);
    expect(result.feedback.summary).toContain('timed out');
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd harness-cli && npx vitest run tests/test_post_pr_wait.ts`
Expected: FAIL — cannot find module

- [ ] **Step 3: Implement post_pr_wait.ts**

```typescript
// hooks/post_pr_wait.ts
/**
 * PostToolUse hook: polls GitHub PR for CI checks and reviews.
 *
 * Reads tool use result from stdin, outputs feedback to stdout.
 * Triggers when Bash output contains a GitHub PR URL.
 */

import { execSync } from 'child_process';

const POLL_INTERVAL_MS = 30_000; // 30 seconds
const TIMEOUT_MS = 30 * 60_000;  // 30 minutes

export interface PrInfo {
  owner: string;
  repo: string;
  pr_number: number;
}

export interface FeedbackInput {
  checks_passed?: boolean;
  reviews?: Array<{ state: string; user: string }>;
  comments?: Array<{ body: string; user: string }>;
  timeout?: boolean;
}

export interface PostPrWaitResult {
  decision: string;
  feedback: {
    checks_passed?: boolean;
    reviews?: Array<{ state: string; user: string }>;
    comments?: Array<{ body: string; user: string }>;
    timeout?: boolean;
    summary: string;
  };
}

export function parsePrUrl(output: string): PrInfo | null {
  const match = output.match(/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/);
  if (!match) return null;
  return {
    owner: match[1],
    repo: match[2],
    pr_number: parseInt(match[3], 10),
  };
}

export function buildFeedbackReport(input: FeedbackInput): PostPrWaitResult {
  if (input.timeout) {
    return {
      decision: 'allow',
      feedback: {
        timeout: true,
        summary: 'Polling timed out after 30 minutes. Manual review required.',
      },
    };
  }

  const reviewCount = input.reviews?.length ?? 0;
  const commentCount = input.comments?.length ?? 0;
  const checksStatus = input.checks_passed ? 'passed' : 'FAILED';

  return {
    decision: 'allow',
    feedback: {
      checks_passed: input.checks_passed ?? false,
      reviews: input.reviews ?? [],
      comments: input.comments ?? [],
      summary: `CI checks ${checksStatus}. ${reviewCount} review(s) received. ${commentCount} comment(s) to address.`,
    },
  };
}

function runGh(args: string): string | null {
  try {
    return execSync(`gh ${args}`, { encoding: 'utf-8', timeout: 15_000 });
  } catch {
    return null;
  }
}

interface CheckResult {
  name: string;
  state: string;
  conclusion: string;
}

async function pollChecks(prNumber: number): Promise<boolean | 'timeout'> {
  const startTime = Date.now();

  while (Date.now() - startTime < TIMEOUT_MS) {
    const output = runGh(`pr checks ${prNumber} --json name,state,conclusion`);
    if (!output) return 'timeout';

    try {
      const checks: CheckResult[] = JSON.parse(output);
      const hasFailure = checks.some(c => c.conclusion === 'FAILURE');
      if (hasFailure) return false;

      const allDone = checks.every(c => c.state === 'COMPLETED');
      if (allDone) return true;
    } catch {
      // Parse error — continue polling
    }

    await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL_MS));
  }

  return 'timeout';
}

function fetchReviews(owner: string, repo: string, prNumber: number): Array<{ state: string; user: string }> {
  const output = runGh(`api repos/${owner}/${repo}/pulls/${prNumber}/reviews`);
  if (!output) return [];
  try {
    const data = JSON.parse(output);
    return data.map((r: any) => ({ state: r.state, user: r.user?.login ?? 'unknown' }));
  } catch {
    return [];
  }
}

function fetchComments(owner: string, repo: string, prNumber: number): Array<{ body: string; user: string }> {
  const output = runGh(`api repos/${owner}/${repo}/pulls/${prNumber}/comments`);
  if (!output) return [];
  try {
    const data = JSON.parse(output);
    return data.map((c: any) => ({ body: c.body ?? '', user: c.user?.login ?? 'unknown' }));
  } catch {
    return [];
  }
}

async function main() {
  let inputData: any;
  try {
    const stdin = await new Promise<string>((resolve) => {
      let data = '';
      process.stdin.on('data', (chunk) => { data += chunk; });
      process.stdin.on('end', () => resolve(data));
    });
    inputData = JSON.parse(stdin);
  } catch {
    process.stdout.write(JSON.stringify({ decision: 'allow' }));
    return;
  }

  const toolOutput = inputData.tool_output ?? inputData.result ?? '';
  const prInfo = parsePrUrl(toolOutput);
  if (!prInfo) {
    // No PR URL in output — not a PR creation, pass through
    process.stdout.write(JSON.stringify({ decision: 'allow' }));
    return;
  }

  const { owner, repo, pr_number } = prInfo;

  // Poll CI checks
  const checksResult = await pollChecks(pr_number);

  if (checksResult === 'timeout') {
    const report = buildFeedbackReport({ timeout: true });
    process.stdout.write(JSON.stringify(report));
    return;
  }

  // Fetch reviews and comments
  const reviews = fetchReviews(owner, repo, pr_number);
  const comments = fetchComments(owner, repo, pr_number);

  const report = buildFeedbackReport({
    checks_passed: checksResult,
    reviews,
    comments,
  });

  process.stdout.write(JSON.stringify(report));
}

main();
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd harness-cli && npx vitest run tests/test_post_pr_wait.ts`
Expected: All passed

- [ ] **Step 5: Build TypeScript**

Run: `cd harness-cli && npx tsc`
Expected: No errors. `dist/hooks/post_pr_wait.js` created.

- [ ] **Step 6: Commit**

```bash
git add harness-cli/hooks/post_pr_wait.ts harness-cli/tests/test_post_pr_wait.ts
git commit -m "feat(harness-cli): add post-PR-wait hook with tests"
```

---

### Task 7: CLAUDE.md and AGENTS.md templates

**Files:**
- Create: `harness-cli/setup/templates/CLAUDE.md.tpl`
- Create: `harness-cli/setup/templates/AGENTS.md.tpl`

- [ ] **Step 1: Create CLAUDE.md.tpl**

```markdown
# Project Memory
## MAS Agent Configuration (Root)

1. This repository is managed by a **Multi-Agent System (MAS)**.
2. You are an executive AGENT with **0-state Memory**.
3. **All context, planning, tracking, and design docs live EXCLUSIVELY in the Project Registry.**

## SSoT Routing
You MUST first _read_ the **Project Registry** as **SSoT**: `{{REGISTRY_PATH}}`

## Definitions
- **Sprint**: One feature's complete lifecycle through the spec cascade (proposal → merge). NOT the industry-standard time-boxed sprint.
- **Milestone**: A collection of completed sprints that achieve a larger goal.

## Roles
You must **IDENTIFY** your role:
- Main Agent (Orchestrator):
    - You are a **pure delegator**
    - You NEVER read or write project files directly
    - ONLY communicate with user, dispatch subagents, coordinate across features
- Sub Agent:
    - You are dispatched by the Orchestrator with a specific role
    - Follow your role definition in `.agents/`

## Branch Naming Convention
All feature work uses: `feat/<feature-name>/<role>[-<instance>]`
Examples: `feat/auth/worker-1`, `feat/auth/sdet-unit`, `feat/auth/team-lead`

## Core Disciplines
### DOs
- **Require spec cascade** before any code: proposal → behavior_spec → test_spec → tests → code
- **Pass lint and tests** before opening a PR
- **Use feature branches** with PR + squash merge for every feature
- **Follow Conventional Commits** for all commit messages
- **Use git worktrees** for parallel task isolation

### DON'Ts
- **Never push to main** directly
- **Never mention AI/assistant/generated** in commits
- **Never write or review code** from the main agent — delegate to subagents
- **Never skip the spec cascade** — all code must have completed specs first
- **Never write to paths outside your role's scope** — hooks enforce this
```

- [ ] **Step 2: Create AGENTS.md.tpl**

The AGENTS.md content is identical to CLAUDE.md.tpl (Claude Code reads both for different agent types):

```markdown
# Project Memory
## MAS Agent Configuration (Root)

1. This repository is managed by a **Multi-Agent System (MAS)**.
2. You are an executive AGENT with **0-state Memory**.
3. **All context, planning, tracking, and design docs live EXCLUSIVELY in the Project Registry.**

## SSoT Routing
You MUST first _read_ the **Project Registry** as **SSoT**: `{{REGISTRY_PATH}}`

## Definitions
- **Sprint**: One feature's complete lifecycle through the spec cascade (proposal → merge). NOT the industry-standard time-boxed sprint.
- **Milestone**: A collection of completed sprints that achieve a larger goal.

## Roles
You must **IDENTIFY** your role:
- Main Agent (Orchestrator):
    - You are a **pure delegator**
    - You NEVER read or write project files directly
    - ONLY communicate with user, dispatch subagents, coordinate across features
- Sub Agent:
    - You are dispatched by the Orchestrator with a specific role
    - Follow your role definition in `.agents/`

## Branch Naming Convention
All feature work uses: `feat/<feature-name>/<role>[-<instance>]`
Examples: `feat/auth/worker-1`, `feat/auth/sdet-unit`, `feat/auth/team-lead`

## Core Disciplines
### DOs
- **Require spec cascade** before any code: proposal → behavior_spec → test_spec → tests → code
- **Pass lint and tests** before opening a PR
- **Use feature branches** with PR + squash merge for every feature
- **Follow Conventional Commits** for all commit messages
- **Use git worktrees** for parallel task isolation

### DON'Ts
- **Never push to main** directly
- **Never mention AI/assistant/generated** in commits
- **Never write or review code** from the main agent — delegate to subagents
- **Never skip the spec cascade** — all code must have completed specs first
- **Never write to paths outside your role's scope** — hooks enforce this
```

- [ ] **Step 3: Verify**

Run: `ls harness-cli/setup/templates/`
Expected: `AGENTS.md.tpl  CLAUDE.md.tpl`

- [ ] **Step 4: Commit**

```bash
git add harness-cli/setup/templates/
git commit -m "feat(harness-cli): add CLAUDE.md and AGENTS.md templates"
```

---

### Task 8: Setup script + integration test

**Files:**
- Create: `harness-cli/setup/init_project.py`
- Create: `harness-cli/tests/test_init_project.py`

- [ ] **Step 1: Write failing integration tests**

```python
# tests/test_init_project.py
import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

# Path to the setup script
SCRIPT_DIR = Path(__file__).parent.parent / "setup"
INIT_SCRIPT = SCRIPT_DIR / "init_project.py"


@pytest.fixture
def project_env(tmp_path):
    """Create a mock project and registry for testing."""
    project = tmp_path / "myproject"
    project.mkdir()
    subprocess.run(["git", "init", str(project)], capture_output=True)

    registry = tmp_path / "registry"
    registry.mkdir()
    (registry / "context_map.json").write_text('{"version": "2.0", "agent_role_context": {}}')
    (registry / "blueprint" / "orchestrate-members").mkdir(parents=True)

    harness_cli = Path(__file__).parent.parent
    return project, registry, harness_cli


class TestInitProject:
    def _run_setup(self, project, registry):
        harness_cli = Path(__file__).parent.parent
        result = subprocess.run(
            ["python", str(INIT_SCRIPT), "--project", str(project), "--registry", str(registry)],
            capture_output=True, text=True, cwd=str(harness_cli)
        )
        return result

    def test_creates_harness_json(self, project_env):
        project, registry, _ = project_env
        self._run_setup(project, registry)
        harness_json = project / ".harness.json"
        assert harness_json.exists()
        config = json.loads(harness_json.read_text())
        assert config["registry_path"] == str(registry)
        assert config["version"] == "1.0.0"

    def test_creates_claude_md(self, project_env):
        project, registry, _ = project_env
        self._run_setup(project, registry)
        claude_md = project / "CLAUDE.md"
        assert claude_md.exists()
        content = claude_md.read_text()
        assert str(registry) in content
        assert "spec cascade" in content.lower() or "Spec cascade" in content or "spec_cascade" in content

    def test_creates_agents_md(self, project_env):
        project, registry, _ = project_env
        self._run_setup(project, registry)
        assert (project / "AGENTS.md").exists()

    def test_creates_agents_symlink(self, project_env):
        project, registry, _ = project_env
        self._run_setup(project, registry)
        agents_link = project / ".agents"
        assert agents_link.is_symlink()
        assert agents_link.resolve() == (registry / "blueprint" / "orchestrate-members").resolve()

    def test_configures_hooks(self, project_env):
        project, registry, _ = project_env
        self._run_setup(project, registry)
        settings_path = project / ".claude" / "settings.local.json"
        assert settings_path.exists()
        settings = json.loads(settings_path.read_text())
        assert "hooks" in settings
        assert "PreToolUse" in settings["hooks"]
        assert "PostToolUse" in settings["hooks"]
        assert len(settings["hooks"]["PreToolUse"]) == 2
        assert len(settings["hooks"]["PostToolUse"]) == 1

    def test_updates_gitignore(self, project_env):
        project, registry, _ = project_env
        self._run_setup(project, registry)
        gitignore = project / ".gitignore"
        assert gitignore.exists()
        content = gitignore.read_text()
        assert "CLAUDE.md" in content
        assert ".harness.json" in content

    def test_idempotent_no_duplicates(self, project_env):
        project, registry, _ = project_env
        self._run_setup(project, registry)
        self._run_setup(project, registry)
        # Check .gitignore doesn't have duplicate entries
        content = (project / ".gitignore").read_text()
        assert content.count("CLAUDE.md") == 1
        # Check hooks aren't duplicated
        settings = json.loads((project / ".claude" / "settings.local.json").read_text())
        assert len(settings["hooks"]["PreToolUse"]) == 2

    def test_skips_existing_agents_symlink(self, project_env):
        project, registry, _ = project_env
        # Create .agents manually
        (project / ".agents").mkdir()
        result = self._run_setup(project, registry)
        # Should warn but not crash
        assert result.returncode == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd harness-cli && python -m pytest tests/test_init_project.py -v`
Expected: FAIL — script doesn't exist

- [ ] **Step 3: Implement init_project.py**

```python
# setup/init_project.py
"""Setup script: installs MAS Harness hooks and config into a target project."""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).parent
TEMPLATES_DIR = SCRIPT_DIR / "templates"
HARNESS_CLI_DIR = SCRIPT_DIR.parent

GITIGNORE_ENTRIES = [
    "CLAUDE.md",
    "AGENTS.md",
    ".claude/",
    ".harness.json",
]


def validate_inputs(project: Path, registry: Path):
    """Validate project and registry paths."""
    if not project.exists():
        sys.exit(f"Error: Project directory does not exist: {project}")
    if not (project / ".git").exists():
        sys.exit(f"Error: Project is not a git repository: {project}")
    if not registry.exists():
        sys.exit(f"Error: Registry directory does not exist: {registry}")
    if not (registry / "context_map.json").exists():
        sys.exit(f"Error: Registry missing context_map.json: {registry}")


def create_harness_json(project: Path, registry: Path):
    """Create .harness.json in project root."""
    config = {
        "registry_path": str(registry.resolve()),
        "harness_cli_path": str(HARNESS_CLI_DIR.resolve()),
        "version": "1.0.0",
    }
    config_path = project / ".harness.json"
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    print(f"  .harness.json: created")


def copy_templates(project: Path, registry: Path):
    """Copy CLAUDE.md and AGENTS.md templates with substitution."""
    project_name = project.name
    registry_path = str(registry.resolve())

    for tpl_name, out_name in [("CLAUDE.md.tpl", "CLAUDE.md"), ("AGENTS.md.tpl", "AGENTS.md")]:
        tpl_path = TEMPLATES_DIR / tpl_name
        if not tpl_path.exists():
            print(f"  Warning: Template not found: {tpl_path}")
            continue
        content = tpl_path.read_text()
        content = content.replace("{{REGISTRY_PATH}}", registry_path)
        content = content.replace("{{PROJECT_NAME}}", project_name)
        (project / out_name).write_text(content)
        print(f"  {out_name}: created")


def create_agents_symlink(project: Path, registry: Path):
    """Symlink .agents/ to registry's orchestrate-members/."""
    agents_path = project / ".agents"
    target = registry / "blueprint" / "orchestrate-members"

    if agents_path.exists() or agents_path.is_symlink():
        print(f"  .agents/: already exists, skipping")
        return

    os.symlink(str(target.resolve()), str(agents_path))
    print(f"  .agents/: symlinked → {target}")


def configure_hooks(project: Path):
    """Configure hooks in .claude/settings.local.json."""
    claude_dir = project / ".claude"
    claude_dir.mkdir(exist_ok=True)
    settings_path = claude_dir / "settings.local.json"

    cli_path = str(HARNESS_CLI_DIR.resolve())

    hooks_config = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Write|Edit",
                    "command": f"python {cli_path}/hooks/path_validator.py",
                },
                {
                    "matcher": "Write|Edit",
                    "command": f"python {cli_path}/hooks/spec_cascade_gate.py",
                },
            ],
            "PostToolUse": [
                {
                    "matcher": "Bash",
                    "command": f"node {cli_path}/dist/hooks/post_pr_wait.js",
                },
            ],
        }
    }

    if settings_path.exists():
        existing = json.loads(settings_path.read_text())
        # Merge — replace hooks section entirely to avoid duplicates
        existing["hooks"] = hooks_config["hooks"]
        settings_path.write_text(json.dumps(existing, indent=2) + "\n")
    else:
        settings_path.write_text(json.dumps(hooks_config, indent=2) + "\n")

    print(f"  Hooks: path_validator, spec_cascade_gate, post_pr_wait")


def update_gitignore(project: Path):
    """Add harness entries to .gitignore."""
    gitignore_path = project / ".gitignore"

    existing_lines = set()
    if gitignore_path.exists():
        existing_lines = set(gitignore_path.read_text().splitlines())

    new_entries = [e for e in GITIGNORE_ENTRIES if e not in existing_lines]
    if new_entries:
        with open(gitignore_path, "a") as f:
            if existing_lines and not gitignore_path.read_text().endswith("\n"):
                f.write("\n")
            f.write("\n".join(new_entries) + "\n")
        print(f"  .gitignore: updated")
    else:
        print(f"  .gitignore: already up to date")


def main():
    parser = argparse.ArgumentParser(description="Initialize MAS Harness in a project")
    parser.add_argument("--project", required=True, help="Path to the target project")
    parser.add_argument("--registry", required=True, help="Path to the MAS registry vault")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    registry = Path(args.registry).resolve()

    validate_inputs(project, registry)

    print(f"MAS Harness initializing for: {project}")
    print(f"  Registry: {registry}")

    create_harness_json(project, registry)
    copy_templates(project, registry)
    create_agents_symlink(project, registry)
    configure_hooks(project)
    update_gitignore(project)

    print(f"\nDone! MAS Harness installed.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd harness-cli && python -m pytest tests/test_init_project.py -v`
Expected: All passed

- [ ] **Step 5: Run full test suite**

Run: `cd harness-cli && python -m pytest -v`
Expected: All Python tests pass

- [ ] **Step 6: Commit**

```bash
git add harness-cli/setup/ harness-cli/tests/test_init_project.py
git commit -m "feat(harness-cli): add setup script with integration tests"
```

---

### Task 9: Final verification

- [ ] **Step 1: Verify full directory structure**

Run: `find harness-cli -type f -not -path '*/node_modules/*' -not -path '*/dist/*' -not -path '*/__pycache__/*' | sort`

Expected 20 files:
```
harness-cli/hooks/__init__.py
harness-cli/hooks/path_validator.py
harness-cli/hooks/post_pr_wait.ts
harness-cli/hooks/spec_cascade_gate.py
harness-cli/hooks/utils/__init__.py
harness-cli/hooks/utils/branch_parser.py
harness-cli/hooks/utils/config_loader.py
harness-cli/package.json
harness-cli/pyproject.toml
harness-cli/setup/init_project.py
harness-cli/setup/templates/AGENTS.md.tpl
harness-cli/setup/templates/CLAUDE.md.tpl
harness-cli/tests/__init__.py
harness-cli/tests/test_branch_parser.py
harness-cli/tests/test_config_loader.py
harness-cli/tests/test_init_project.py
harness-cli/tests/test_path_validator.py
harness-cli/tests/test_post_pr_wait.ts
harness-cli/tests/test_spec_cascade_gate.py
harness-cli/tsconfig.json
```

- [ ] **Step 2: Run all Python tests**

Run: `cd harness-cli && python -m pytest -v --tb=short`
Expected: All pass

- [ ] **Step 3: Run TypeScript tests**

Run: `cd harness-cli && npx vitest run`
Expected: All pass

- [ ] **Step 4: Build TypeScript**

Run: `cd harness-cli && npx tsc`
Expected: No errors

- [ ] **Step 5: Test setup script end-to-end**

Run against a real temp project:
```bash
TMPDIR=$(mktemp -d)
mkdir -p "$TMPDIR/test-project" && cd "$TMPDIR/test-project" && git init
python /home/aeonli/repos/proj-regs/harness-cli/setup/init_project.py \
  --project "$TMPDIR/test-project" \
  --registry /home/aeonli/repos/proj-regs/mas-harness
ls -la "$TMPDIR/test-project"
cat "$TMPDIR/test-project/.harness.json"
cat "$TMPDIR/test-project/.claude/settings.local.json"
rm -rf "$TMPDIR"
```

Expected: All files created, hooks configured, symlink correct.
