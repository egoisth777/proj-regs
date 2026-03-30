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
