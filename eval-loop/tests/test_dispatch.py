"""Tests for dispatch.py — pool worktree management."""

import json
import os
import pytest
import shutil
from pathlib import Path

from dispatch import (
    get_sparse_checkout_config,
    prepare_workspace,
    cleanup_workspace,
)


class TestGetSparseCheckoutConfig:
    def test_pool_e_mutate_includes_workspace(self):
        config = get_sparse_checkout_config("pool-e", "mutate")
        assert any("workspace" in p for p in config["include"])
        assert any("eval" in p for p in config["exclude"])

    def test_pool_e_execute_includes_tpls_and_regs(self):
        config = get_sparse_checkout_config("pool-e", "execute")
        assert any("tpls" in p for p in config["include"])
        assert any("regs" in p for p in config["include"])

    def test_pool_t_config(self):
        config = get_sparse_checkout_config("pool-t")
        assert any("criteria" in p for p in config["include"])
        assert any("tpls" in p for p in config["exclude"])

    def test_pool_v_config(self):
        config = get_sparse_checkout_config("pool-v")
        assert any("scripts" in p for p in config["include"])
        assert any("criteria" in p for p in config["exclude"])

    def test_pool_r_config(self):
        config = get_sparse_checkout_config("pool-r")
        assert any("regs" in p for p in config["include"])

    def test_unknown_pool_raises(self):
        with pytest.raises(ValueError, match="unknown pool"):
            get_sparse_checkout_config("pool-x")


class TestPrepareWorkspace:
    def test_copies_active_snapshot_to_workspace(self, tmp_path):
        snapshots = tmp_path / "tpls" / "snapshots"
        c0 = snapshots / "candidate-0"
        (c0 / "sys").mkdir(parents=True)
        (c0 / "sys" / "role.md").write_text("# role")
        (c0 / "cli").mkdir(parents=True)
        (c0 / "cli" / "hook.py").write_text("print('hook')")

        (snapshots / "active").symlink_to("candidate-0")

        workspace = prepare_workspace(snapshots)
        assert (workspace / "sys" / "role.md").read_text() == "# role"
        assert (workspace / "cli" / "hook.py").read_text() == "print('hook')"
        assert workspace.name == "workspace"

    def test_raises_if_workspace_already_exists(self, tmp_path):
        snapshots = tmp_path / "tpls" / "snapshots"
        c0 = snapshots / "candidate-0"
        (c0 / "sys").mkdir(parents=True)
        (snapshots / "active").symlink_to("candidate-0")
        (snapshots / "workspace").mkdir()

        with pytest.raises(FileExistsError, match="workspace already exists"):
            prepare_workspace(snapshots)


class TestCleanupWorkspace:
    def test_removes_workspace(self, tmp_path):
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        (workspace / "file.txt").write_text("data")
        cleanup_workspace(workspace)
        assert not workspace.exists()

    def test_no_error_if_missing(self, tmp_path):
        workspace = tmp_path / "nonexistent"
        cleanup_workspace(workspace)  # should not raise
