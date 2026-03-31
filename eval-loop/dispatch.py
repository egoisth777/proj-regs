"""Pool worktree management — creates isolated workspaces for pool agents.

The orchestrator agent uses this module to:
1. Prepare a mutable workspace from the active snapshot (for pool-e mutation)
2. Get sparse-checkout configs for each pool (for agent dispatch)
3. Clean up workspaces after use
"""

import shutil
from pathlib import Path
from typing import Any, Optional


_CONFIGS = {
    "pool-e": {
        "mutate": {
            "include": ["tpls/snapshots/workspace/"],
            "exclude": ["eval/", "eval-loop/", "regs/"],
        },
        "execute": {
            "include": ["tpls/sys/", "tpls/cli/", "regs/test-regs/"],
            "exclude": ["eval/", "eval-loop/"],
        },
    },
    "pool-t": {
        "default": {
            "include": ["eval/criteria/", "eval/tiers/", "eval/scripts/"],
            "exclude": ["tpls/", "regs/", "eval-loop/"],
        },
    },
    "pool-v": {
        "default": {
            "include": ["eval/scripts/", "regs/test-regs/"],
            "exclude": ["eval/criteria/", "eval/tiers/", "tpls/", "eval-loop/"],
        },
    },
    "pool-r": {
        "default": {
            "include": ["regs/"],
            "exclude": ["eval/", "tpls/", "eval-loop/"],
        },
    },
}


def get_sparse_checkout_config(
    pool: str,
    phase: Optional[str] = None,
) -> dict[str, list[str]]:
    """Return the sparse-checkout include/exclude lists for a pool.

    Args:
        pool: Pool name (pool-e, pool-t, pool-v, pool-r).
        phase: Required for pool-e (mutate or execute). Ignored for others.

    Returns {"include": [...], "exclude": [...]}.
    """
    if pool not in _CONFIGS:
        raise ValueError(f"unknown pool: {pool}")
    configs = _CONFIGS[pool]
    key = phase if phase and phase in configs else "default"
    if key not in configs:
        raise ValueError(f"pool '{pool}' requires a phase, got '{phase}'")
    return configs[key]


def prepare_workspace(snapshots_dir: Path) -> Path:
    """Copy the active snapshot's sys/ and cli/ into workspace/.

    The workspace is a mutable copy that pool-e modifies during mutation.
    After mutation, snapshot_manager.create_candidate() captures and destroys it.

    Returns the workspace path.
    Raises FileExistsError if workspace/ already exists (stale from a crash).
    """
    sd = Path(snapshots_dir)
    workspace = sd / "workspace"
    if workspace.exists():
        raise FileExistsError(
            f"workspace already exists at {workspace} — "
            "clean up stale workspace before starting a new mutation"
        )

    active = sd / "active"
    if not active.exists():
        raise FileNotFoundError(f"no active symlink at {active}")

    active_resolved = active.resolve()

    workspace.mkdir()
    for subdir in ("sys", "cli"):
        src = active_resolved / subdir
        if src.is_dir():
            shutil.copytree(str(src), str(workspace / subdir))

    return workspace


def cleanup_workspace(workspace: Path) -> None:
    """Remove a workspace directory. No-op if it doesn't exist."""
    ws = Path(workspace)
    if ws.exists():
        shutil.rmtree(str(ws))
