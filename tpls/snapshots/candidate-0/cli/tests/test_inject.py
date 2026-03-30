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
