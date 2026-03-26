# M2: Context Injector — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a CLI tool that assembles minimum-context prompts for subagents by reading `context_map.json` and resolving role-specific documents from the registry.

**Architecture:** Single Python module (`context/inject.py`) that reuses M1's `config_loader` utilities. Reads `context_map.json`, resolves `<feature>` placeholders to real OpenSpec folders, reads doc contents, and outputs assembled JSON or text.

**Tech Stack:** Python 3.10+ (pytest), reuses `hooks/utils/config_loader.py` from M1

**Spec:** `docs/superpowers/specs/2026-03-25-m2-context-injector-design.md`

**Task execution order:** Tasks MUST be executed sequentially (1 → 4).

---

## File Map

| File | Purpose |
|---|---|
| `harness-cli/context/__init__.py` | Package marker |
| `harness-cli/context/inject.py` | CLI entry point + `assemble_context()` core logic |
| `harness-cli/tests/test_inject.py` | Unit + integration tests |

---

## Tasks

### Task 1: Scaffolding + package marker

**Files:**
- Create: `harness-cli/context/__init__.py`

- [ ] **Step 1: Create package marker**

```python
# context/__init__.py
# (empty file)
```

- [ ] **Step 2: Verify**

Run: `ls harness-cli/context/`
Expected: `__init__.py`

- [ ] **Step 3: Commit**

```bash
git add harness-cli/context/__init__.py
git commit -m "feat(harness-cli): add context package for M2 injector"
```

---

### Task 2: Tests (TDD)

**Files:**
- Create: `harness-cli/tests/test_inject.py`

- [ ] **Step 1: Write all tests**

```python
# tests/test_inject.py
import json
import os
import subprocess
from pathlib import Path

import pytest

from context.inject import assemble_context, build_prompt_prefix


# --- Fixtures ---

@pytest.fixture
def mock_registry(tmp_path):
    """Create a minimal registry with context_map.json and role definitions."""
    registry = tmp_path / "registry"
    registry.mkdir()

    # context_map.json with all 12 roles
    context_map = {
        "version": "2.0",
        "description": "Test context map",
        "agent_role_context": {
            "orchestrator": {
                "required_docs": ["00-Project-Memory.md", "runtime/active_sprint.md", "runtime/milestones.md"]
            },
            "sonders": {
                "required_docs": ["00-Project-Memory.md", "blueprint/planning/roadmap.md", "blueprint/design/architecture_overview.md"]
            },
            "negator": {
                "required_docs": ["00-Project-Memory.md", "blueprint/design/architecture_overview.md", "blueprint/design/design_principles.md"]
            },
            "behavior-spec-writer": {
                "required_docs": ["00-Project-Memory.md", "blueprint/design/design_principles.md", "<feature>/proposal.md"]
            },
            "test-spec-writer": {
                "required_docs": ["00-Project-Memory.md", "<feature>/behavior_spec.md"]
            },
            "team-lead": {
                "required_docs": ["00-Project-Memory.md", "blueprint/engineering/dev_workflow.md", "<feature>/proposal.md", "<feature>/tasks.md"]
            },
            "worker": {
                "required_docs": ["blueprint/engineering/dev_workflow.md", "<feature>/tasks.md"]
            },
            "sdet-unit": {
                "required_docs": ["blueprint/engineering/testing_strategy.md", "<feature>/test_spec.md"]
            },
            "sdet-integration": {
                "required_docs": ["blueprint/engineering/testing_strategy.md", "blueprint/design/architecture_overview.md", "<feature>/test_spec.md"]
            },
            "sdet-e2e": {
                "required_docs": ["blueprint/engineering/testing_strategy.md", "<feature>/behavior_spec.md"]
            },
            "auditor": {
                "required_docs": ["blueprint/design/architecture_overview.md", "blueprint/design/design_principles.md", "<feature>/proposal.md"]
            },
            "regression-runner": {
                "required_docs": ["blueprint/engineering/testing_strategy.md"]
            },
        },
        "path_based_rules": []
    }
    (registry / "context_map.json").write_text(json.dumps(context_map))

    # Create required doc files
    (registry / "00-Project-Memory.md").write_text("# Project Memory\nSSoT routing here.")
    (registry / "blueprint" / "design").mkdir(parents=True)
    (registry / "blueprint" / "design" / "architecture_overview.md").write_text("# Architecture\nOverview content.")
    (registry / "blueprint" / "design" / "design_principles.md").write_text("# Principles\nPrinciples content.")
    (registry / "blueprint" / "engineering").mkdir(parents=True)
    (registry / "blueprint" / "engineering" / "dev_workflow.md").write_text("# Dev Workflow\nWorkflow content.")
    (registry / "blueprint" / "engineering" / "testing_strategy.md").write_text("# Testing\nStrategy content.")
    (registry / "blueprint" / "planning").mkdir(parents=True)
    (registry / "blueprint" / "planning" / "roadmap.md").write_text("# Roadmap\nRoadmap content.")
    (registry / "runtime").mkdir()
    (registry / "runtime" / "active_sprint.md").write_text("# Active Sprints\nSprint data.")
    (registry / "runtime" / "milestones.md").write_text("# Milestones\nMilestone data.")

    # Create a feature OpenSpec folder
    feature_dir = registry / "runtime" / "openspec" / "changes" / "2026-03-25-auth"
    feature_dir.mkdir(parents=True)
    (feature_dir / "proposal.md").write_text("# Proposal\nAuth feature proposal.")
    (feature_dir / "behavior_spec.md").write_text("# Behavior Spec\nGiven/When/Then.")
    (feature_dir / "test_spec.md").write_text("# Test Spec\nTest specifications.")
    (feature_dir / "tasks.md").write_text("# Tasks\nTask checklist.")

    # Create role definition files
    members = registry / "blueprint" / "orchestrate-members"
    members.mkdir(parents=True)
    for role in ["orchestrator", "sonders", "negator", "behavior-spec-writer",
                 "test-spec-writer", "team-lead", "worker", "sdet-unit",
                 "sdet-integration", "sdet-e2e", "auditor", "regression-runner"]:
        (members / f"{role}.md").write_text(f"---\nname: {role}\n---\n# Role: {role}\nRole definition.")

    return registry


# --- Role Resolution Tests ---

class TestAssembleContextRoleResolution:
    def test_unknown_role_returns_error(self, mock_registry):
        result = assemble_context("nonexistent", None, str(mock_registry))
        assert "error" in result
        assert "not found" in result["error"]

    def test_orchestrator_resolves_without_feature(self, mock_registry):
        result = assemble_context("orchestrator", None, str(mock_registry))
        assert "error" not in result
        assert result["role"] == "orchestrator"
        assert len(result["docs"]) == 3

    def test_regression_runner_resolves_without_feature(self, mock_registry):
        result = assemble_context("regression-runner", None, str(mock_registry))
        assert "error" not in result
        assert len(result["docs"]) == 1

    def test_worker_with_feature_resolves(self, mock_registry):
        result = assemble_context("worker", "auth", str(mock_registry))
        assert "error" not in result
        assert len(result["docs"]) == 2
        paths = [d["path"] for d in result["docs"]]
        assert any("dev_workflow.md" in p for p in paths)
        assert any("tasks.md" in p for p in paths)

    def test_worker_without_feature_returns_error(self, mock_registry):
        result = assemble_context("worker", None, str(mock_registry))
        assert "error" in result
        assert "requires --feature" in result["error"]

    def test_feature_not_found_returns_error(self, mock_registry):
        result = assemble_context("worker", "nonexistent", str(mock_registry))
        assert "error" in result
        assert "No OpenSpec folder" in result["error"]

    def test_feature_silently_ignored_for_no_placeholder_roles(self, mock_registry):
        """Providing --feature for regression-runner should work fine (ignored)."""
        result = assemble_context("regression-runner", "auth", str(mock_registry))
        assert "error" not in result
        assert len(result["docs"]) == 1

    def test_all_12_roles_resolve(self, mock_registry):
        """Every role in context_map.json produces a valid result."""
        roles_without_feature = ["orchestrator", "sonders", "negator", "regression-runner"]
        roles_with_feature = [
            "behavior-spec-writer", "test-spec-writer", "team-lead",
            "worker", "sdet-unit", "sdet-integration", "sdet-e2e", "auditor"
        ]

        for role in roles_without_feature:
            result = assemble_context(role, None, str(mock_registry))
            assert "error" not in result, f"Role '{role}' failed: {result}"

        for role in roles_with_feature:
            result = assemble_context(role, "auth", str(mock_registry))
            assert "error" not in result, f"Role '{role}' failed: {result}"


# --- Doc Reading Tests ---

class TestAssembleContextDocReading:
    def test_existing_doc_has_content(self, mock_registry):
        result = assemble_context("orchestrator", None, str(mock_registry))
        doc = result["docs"][0]
        assert doc["content"] is not None
        assert "Project Memory" in doc["content"]

    def test_missing_doc_has_null_content(self, mock_registry):
        # Remove a doc that orchestrator needs
        (mock_registry / "runtime" / "milestones.md").unlink()
        result = assemble_context("orchestrator", None, str(mock_registry))
        milestones_doc = [d for d in result["docs"] if "milestones" in d["path"]][0]
        assert milestones_doc["content"] is None
        assert "error" in milestones_doc

    def test_role_definition_included(self, mock_registry):
        result = assemble_context("worker", "auth", str(mock_registry))
        assert result["role_definition"] is not None
        assert "Role: worker" in result["role_definition"]

    def test_missing_role_definition(self, mock_registry):
        (mock_registry / "blueprint" / "orchestrate-members" / "worker.md").unlink()
        result = assemble_context("worker", "auth", str(mock_registry))
        assert result["role_definition"] is None

    def test_resolved_paths_are_relative(self, mock_registry):
        result = assemble_context("worker", "auth", str(mock_registry))
        for doc in result["docs"]:
            assert not doc["path"].startswith("/"), f"Path should be relative: {doc['path']}"


# --- Prompt Assembly Tests ---

class TestBuildPromptPrefix:
    def test_contains_role_name(self):
        prefix = build_prompt_prefix("worker", "auth", "Role def here", [
            {"path": "doc.md", "content": "Doc content"}
        ])
        assert "worker" in prefix.lower() or "Worker" in prefix

    def test_contains_feature_name(self):
        prefix = build_prompt_prefix("worker", "auth", "Role def", [
            {"path": "doc.md", "content": "Content"}
        ])
        assert "auth" in prefix

    def test_contains_role_definition(self):
        prefix = build_prompt_prefix("worker", "auth", "# My Role Definition", [])
        assert "# My Role Definition" in prefix

    def test_contains_doc_content(self):
        prefix = build_prompt_prefix("worker", "auth", "Role", [
            {"path": "doc1.md", "content": "First doc content"},
            {"path": "doc2.md", "content": "Second doc content"},
        ])
        assert "First doc content" in prefix
        assert "Second doc content" in prefix
        assert "---" in prefix  # separator

    def test_no_feature_omits_feature_clause(self):
        prefix = build_prompt_prefix("orchestrator", None, "Role def", [
            {"path": "doc.md", "content": "Content"}
        ])
        assert "dispatched for feature" not in prefix

    def test_with_feature_includes_feature_clause(self):
        prefix = build_prompt_prefix("worker", "auth", "Role def", [])
        assert "dispatched for feature" in prefix
        assert "auth" in prefix

    def test_skips_null_content_docs(self):
        prefix = build_prompt_prefix("worker", "auth", "Role", [
            {"path": "good.md", "content": "Good content"},
            {"path": "missing.md", "content": None, "error": "File not found"},
        ])
        assert "Good content" in prefix
        assert "File not found" not in prefix or "missing.md" in prefix


# --- Integration Test ---

class TestIntegrationRealRegistry:
    """Run against the real voice-input-to-markdown registry."""

    REGISTRY = "/home/aeonli/repos/proj-regs/voice-input-to-markdown"

    @pytest.mark.skipif(
        not os.path.exists("/home/aeonli/repos/proj-regs/voice-input-to-markdown/context_map.json"),
        reason="Real registry not available"
    )
    def test_worker_with_real_registry(self):
        result = assemble_context("worker", "voice-capture", self.REGISTRY)
        assert "error" not in result
        assert any("dev_workflow" in d["path"] for d in result["docs"])
        assert any("tasks" in d["path"] for d in result["docs"])

    @pytest.mark.skipif(
        not os.path.exists("/home/aeonli/repos/proj-regs/voice-input-to-markdown/context_map.json"),
        reason="Real registry not available"
    )
    def test_all_12_roles_no_crash(self):
        roles_without_feature = ["orchestrator", "sonders", "negator", "regression-runner"]
        roles_with_feature = [
            "behavior-spec-writer", "test-spec-writer", "team-lead",
            "worker", "sdet-unit", "sdet-integration", "sdet-e2e", "auditor"
        ]
        for role in roles_without_feature:
            result = assemble_context(role, None, self.REGISTRY)
            assert "error" not in result, f"Role '{role}' failed: {result}"
        for role in roles_with_feature:
            result = assemble_context(role, "voice-capture", self.REGISTRY)
            # Some docs may not exist yet — that's OK, just shouldn't crash
            assert isinstance(result, dict), f"Role '{role}' returned non-dict"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd harness-cli && python -m pytest tests/test_inject.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'context.inject'`

- [ ] **Step 3: Commit**

```bash
git add harness-cli/tests/test_inject.py
git commit -m "test(harness-cli): add context injector tests (TDD red phase)"
```

---

### Task 3: Implement inject.py

**Files:**
- Create: `harness-cli/context/inject.py`

- [ ] **Step 1: Implement the context injector**

```python
# context/inject.py
"""CLI tool: assembles minimum-context prompts for subagents.

Usage:
    python context/inject.py --role <role> [--feature <feature>] [--project <path>] [--format json|text]
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

from hooks.utils.config_loader import (
    find_project_root,
    load_harness_config,
    load_context_map,
    resolve_feature_folder,
)


def _has_feature_placeholder(required_docs: list[str]) -> bool:
    """Check if any doc path contains <feature> placeholder."""
    return any("<feature>" in doc for doc in required_docs)


def _resolve_doc_path(doc_path: str, feature: Optional[str], registry_path: str) -> str:
    """Resolve <feature> placeholder in a doc path to actual registry-relative path."""
    if "<feature>" not in doc_path:
        return doc_path

    resolved_folder = resolve_feature_folder(registry_path, feature)
    if not resolved_folder:
        return doc_path  # Can't resolve — return as-is, will fail at read time

    # Convert absolute to registry-relative
    rel_folder = os.path.relpath(resolved_folder, registry_path)
    return doc_path.replace("<feature>", rel_folder)


def _read_file(registry_path: str, relative_path: str) -> dict:
    """Read a file from the registry. Returns dict with path, content, and optional error."""
    full_path = Path(registry_path) / relative_path
    if not full_path.exists():
        return {"path": relative_path, "content": None, "error": "File not found"}
    try:
        content = full_path.read_text()
        return {"path": relative_path, "content": content}
    except Exception as e:
        return {"path": relative_path, "content": None, "error": str(e)}


def build_prompt_prefix(
    role: str,
    feature: Optional[str],
    role_definition: Optional[str],
    docs: list[dict],
) -> str:
    """Assemble the prompt prefix from role definition and docs."""
    parts = []

    # Header
    if feature:
        parts.append(f"You are a {role} agent dispatched for feature '{feature}'.")
    else:
        parts.append(f"You are a {role} agent.")

    # Role definition
    if role_definition:
        parts.append("\n## Your Role")
        parts.append(role_definition)

    # Context documents
    readable_docs = [d for d in docs if d.get("content") is not None]
    if readable_docs:
        parts.append("\n## Context Documents")
        for i, doc in enumerate(readable_docs):
            if i > 0:
                parts.append("\n---")
            parts.append(f"\n### {doc['path']}")
            parts.append(doc["content"])

    return "\n".join(parts)


def assemble_context(role: str, feature: Optional[str], registry_path: str) -> dict:
    """Assemble context for a subagent based on its role.

    Returns dict with role, feature, role_definition, docs, prompt_prefix.
    On error, returns {"error": "message"}.
    """
    # Load context map
    try:
        context_map = load_context_map(registry_path)
    except FileNotFoundError as e:
        return {"error": str(e)}

    role_context = context_map.get("agent_role_context", {})

    # Validate role
    if role not in role_context:
        return {"error": f"Role '{role}' not found in context_map.json"}

    required_docs = role_context[role].get("required_docs", [])

    # Check if feature is needed
    needs_feature = _has_feature_placeholder(required_docs)
    if needs_feature and not feature:
        return {"error": f"Role '{role}' requires --feature but none provided"}

    # Resolve feature folder if needed
    if needs_feature:
        resolved_folder = resolve_feature_folder(registry_path, feature)
        if not resolved_folder:
            return {"error": f"No OpenSpec folder found for feature '{feature}'"}

    # Resolve doc paths and read contents
    docs = []
    for doc_path in required_docs:
        resolved_path = _resolve_doc_path(doc_path, feature, registry_path)
        doc_data = _read_file(registry_path, resolved_path)
        docs.append(doc_data)

    # Read role definition
    role_def_path = Path(registry_path) / "blueprint" / "orchestrate-members" / f"{role}.md"
    role_definition = None
    if role_def_path.exists():
        role_definition = role_def_path.read_text()

    # Build prompt prefix
    prompt_prefix = build_prompt_prefix(role, feature, role_definition, docs)

    return {
        "role": role,
        "feature": feature,
        "role_definition": role_definition,
        "docs": docs,
        "prompt_prefix": prompt_prefix,
    }


def main():
    parser = argparse.ArgumentParser(description="Assemble minimum-context prompt for a subagent")
    parser.add_argument("--role", required=True, help="Agent role name")
    parser.add_argument("--feature", default=None, help="Feature name (for roles with <feature> placeholders)")
    parser.add_argument("--project", default=None, help="Path to the project (defaults to CWD)")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
    args = parser.parse_args()

    # Find project root
    project_path = args.project or os.getcwd()
    project_root = find_project_root(project_path)
    if not project_root:
        json.dump({"error": "No .harness.json found. Run init_project.py first."}, sys.stdout)
        sys.exit(1)

    # Load config
    config = load_harness_config(project_root)
    if not config:
        json.dump({"error": "Failed to load .harness.json"}, sys.stdout)
        sys.exit(1)

    registry_path = config.get("registry_path")
    if not registry_path:
        json.dump({"error": "registry_path not found in .harness.json"}, sys.stdout)
        sys.exit(1)

    # Assemble context
    result = assemble_context(args.role, args.feature, registry_path)

    if "error" in result:
        if args.format == "json":
            json.dump(result, sys.stdout)
        else:
            print(result["error"], file=sys.stderr)
        sys.exit(1)

    # Output
    if args.format == "text":
        print(result["prompt_prefix"])
    else:
        json.dump(result, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd harness-cli && python -m pytest tests/test_inject.py -v`
Expected: All pass

- [ ] **Step 3: Run ALL tests (M1 + M2)**

Run: `cd harness-cli && python -m pytest -v`
Expected: All pass (M1 tests + M2 tests)

- [ ] **Step 4: Commit**

```bash
git add harness-cli/context/inject.py
git commit -m "feat(harness-cli): add context injector CLI tool"
```

---

### Task 4: Integration test against real registry + final verification

- [ ] **Step 1: Run integration tests with real registry**

Run: `cd harness-cli && python -m pytest tests/test_inject.py::TestIntegrationRealRegistry -v`
Expected: Tests pass (or skip if registry not available)

- [ ] **Step 2: Manual CLI test**

Run against the real voice-input-to-markdown project:
```bash
cd harness-cli && python context/inject.py \
  --role worker \
  --feature voice-capture \
  --project /home/aeonli/repos/voice-input-to-markdown-sample \
  --format text
```
Expected: Outputs a prompt containing the worker role definition + dev_workflow.md content + tasks.md content.

Run without feature for orchestrator:
```bash
cd harness-cli && python context/inject.py \
  --role orchestrator \
  --project /home/aeonli/repos/voice-input-to-markdown-sample \
  --format json
```
Expected: JSON with 3 docs (00-Project-Memory.md, active_sprint.md, milestones.md).

Run with unknown role:
```bash
cd harness-cli && python context/inject.py \
  --role fake-role \
  --project /home/aeonli/repos/voice-input-to-markdown-sample \
  --format json
echo "Exit code: $?"
```
Expected: Error JSON + exit code 1.

- [ ] **Step 3: Run full test suite**

Run: `cd harness-cli && python -m pytest -v --tb=short`
Expected: ALL tests pass (M1 + M2)

- [ ] **Step 4: Verify file structure**

Run: `find harness-cli/context -type f | sort`
Expected:
```
harness-cli/context/__init__.py
harness-cli/context/inject.py
```
