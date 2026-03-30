import json
from pathlib import Path, PurePath
from unittest.mock import patch

from hooks.spec_cascade_gate import is_source_file, check_spec_cascade, read_phase_from_status


class TestIsSourceFile:
    def test_python_source(self):
        assert is_source_file("src/app.py") is True

    def test_test_file_excluded(self):
        assert is_source_file("tests/test_app.py") is False

    def test_test_dir_excluded(self):
        assert is_source_file("test/test_app.py") is False

    def test_nested_test_dir_excluded(self):
        assert is_source_file("tests/unit/deep/test_auth.py") is False

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

    def test_github_dir_excluded(self):
        assert is_source_file(".github/CODEOWNERS") is False


class TestReadPhaseFromStatus:
    def test_reads_execution_phase(self):
        assert read_phase_from_status("## Current Phase\n`execution`\n") == "execution"

    def test_reads_design_phase(self):
        assert read_phase_from_status("## Current Phase\n`design`\n") == "design"

    def test_reads_testing_phase(self):
        assert read_phase_from_status("## Current Phase\n`testing`\n") == "testing"

    def test_reads_quality_gate(self):
        assert read_phase_from_status("## Current Phase\n`quality-gate`\n") == "quality-gate"

    def test_returns_none_for_empty(self):
        assert read_phase_from_status("") is None


class TestCheckSpecCascade:
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
        (feature / "test_spec.md").write_text("short")
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
