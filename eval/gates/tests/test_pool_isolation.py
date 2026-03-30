"""Tests for pool_isolation — validates sparse-checkout matches pool permissions."""

import pytest
from pathlib import Path

from pool_isolation import (
    get_expected_paths,
    validate_pool_isolation,
    POOL_SPARSE_CONFIGS,
)


class TestGetExpectedPaths:
    def test_pool_e_mutate_paths(self):
        paths = get_expected_paths("pool-e", "mutate")
        assert "tpls/snapshots/workspace/" in paths
        assert "eval/" not in paths

    def test_pool_e_execute_paths(self):
        paths = get_expected_paths("pool-e", "execute")
        assert any("tpls/" in p for p in paths)
        assert any("regs/test-regs/" in p for p in paths)
        assert "eval/" not in paths

    def test_pool_t_paths(self):
        paths = get_expected_paths("pool-t")
        assert any("eval/criteria/" in p for p in paths)
        assert any("eval/tiers/" in p for p in paths)
        assert any("eval/scripts/" in p for p in paths)

    def test_pool_v_paths(self):
        paths = get_expected_paths("pool-v")
        assert any("eval/scripts/" in p for p in paths)
        assert any("regs/test-regs/" in p for p in paths)

    def test_pool_r_paths(self):
        paths = get_expected_paths("pool-r")
        assert any("regs/" in p for p in paths)

    def test_unknown_pool_raises(self):
        with pytest.raises(ValueError, match="unknown pool"):
            get_expected_paths("pool-x")


class TestValidatePoolIsolation:
    def test_valid_pool_e_worktree(self, tmp_path):
        """Simulate a pool-e mutate worktree with only workspace/ present."""
        (tmp_path / "tpls" / "snapshots" / "workspace").mkdir(parents=True)
        result = validate_pool_isolation(tmp_path, "pool-e", "mutate")
        assert result["valid"] is True

    def test_pool_e_with_eval_present_fails(self, tmp_path):
        """If eval/ exists in a pool-e worktree, isolation is violated."""
        (tmp_path / "tpls" / "snapshots" / "workspace").mkdir(parents=True)
        (tmp_path / "eval" / "criteria").mkdir(parents=True)
        result = validate_pool_isolation(tmp_path, "pool-e", "mutate")
        assert result["valid"] is False
        assert any("eval" in v for v in result["violations"])

    def test_pool_t_without_tpls(self, tmp_path):
        """pool-t worktree should not contain tpls/."""
        (tmp_path / "eval" / "criteria").mkdir(parents=True)
        (tmp_path / "eval" / "tiers").mkdir(parents=True)
        (tmp_path / "eval" / "scripts").mkdir(parents=True)
        result = validate_pool_isolation(tmp_path, "pool-t")
        assert result["valid"] is True

    def test_pool_t_with_tpls_fails(self, tmp_path):
        (tmp_path / "eval" / "criteria").mkdir(parents=True)
        (tmp_path / "tpls").mkdir()
        result = validate_pool_isolation(tmp_path, "pool-t")
        assert result["valid"] is False
        assert any("tpls" in v for v in result["violations"])
