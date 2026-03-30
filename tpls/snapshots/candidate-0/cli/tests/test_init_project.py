import json
import os
import subprocess
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).parent.parent / "setup"
INIT_SCRIPT = SCRIPT_DIR / "init_project.py"


@pytest.fixture
def project_env(tmp_path):
    project = tmp_path / "myproject"
    project.mkdir()
    subprocess.run(["git", "init", str(project)], capture_output=True)

    registry = tmp_path / "registry"
    registry.mkdir()
    (registry / "context_map.json").write_text('{"version": "2.0", "agent_role_context": {}}')
    (registry / "blueprint" / "orchestrate-members").mkdir(parents=True)

    return project, registry


class TestInitProject:
    def _run_setup(self, project, registry):
        result = subprocess.run(
            ["python", str(INIT_SCRIPT), "--project", str(project), "--registry", str(registry)],
            capture_output=True, text=True
        )
        return result

    def test_creates_harness_json(self, project_env):
        project, registry = project_env
        self._run_setup(project, registry)
        harness_json = project / ".harness.json"
        assert harness_json.exists()
        config = json.loads(harness_json.read_text())
        assert config["registry_path"] == str(registry)
        assert config["version"] == "1.0.0"

    def test_creates_claude_md(self, project_env):
        project, registry = project_env
        self._run_setup(project, registry)
        claude_md = project / "CLAUDE.md"
        assert claude_md.exists()
        content = claude_md.read_text()
        assert str(registry) in content

    def test_creates_agents_md(self, project_env):
        project, registry = project_env
        self._run_setup(project, registry)
        assert (project / "AGENTS.md").exists()

    def test_creates_agents_symlink(self, project_env):
        project, registry = project_env
        self._run_setup(project, registry)
        agents_link = project / ".agents"
        assert agents_link.is_symlink()
        assert agents_link.resolve() == (registry / "blueprint" / "orchestrate-members").resolve()

    def test_configures_hooks(self, project_env):
        project, registry = project_env
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
        project, registry = project_env
        self._run_setup(project, registry)
        gitignore = project / ".gitignore"
        assert gitignore.exists()
        content = gitignore.read_text()
        assert "CLAUDE.md" in content
        assert ".harness.json" in content

    def test_idempotent_no_duplicates(self, project_env):
        project, registry = project_env
        self._run_setup(project, registry)
        self._run_setup(project, registry)
        content = (project / ".gitignore").read_text()
        assert content.count("CLAUDE.md") == 1
        settings = json.loads((project / ".claude" / "settings.local.json").read_text())
        assert len(settings["hooks"]["PreToolUse"]) == 2

    def test_skips_existing_agents_dir(self, project_env):
        project, registry = project_env
        (project / ".agents").mkdir()
        result = self._run_setup(project, registry)
        assert result.returncode == 0
