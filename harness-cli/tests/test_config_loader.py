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
