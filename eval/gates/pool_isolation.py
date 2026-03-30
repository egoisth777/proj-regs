"""Validate that a pool worktree's sparse-checkout matches expected permissions."""

from pathlib import Path
from typing import Any, Optional

# Expected paths each pool can see, and paths that MUST be absent
POOL_SPARSE_CONFIGS = {
    "pool-e": {
        "mutate": {
            "include": ["tpls/snapshots/workspace/"],
            "exclude": ["eval/", "orchestrator/"],
        },
        "execute": {
            "include": ["tpls/", "regs/test-regs/"],
            "exclude": ["eval/", "orchestrator/"],
        },
    },
    "pool-t": {
        "default": {
            "include": ["eval/criteria/", "eval/tiers/", "eval/scripts/"],
            "exclude": ["tpls/", "regs/", "orchestrator/"],
        },
    },
    "pool-v": {
        "default": {
            "include": ["eval/scripts/", "regs/test-regs/"],
            "exclude": ["eval/criteria/", "tpls/", "orchestrator/"],
        },
    },
    "pool-r": {
        "default": {
            "include": ["regs/"],
            "exclude": ["eval/", "tpls/", "orchestrator/"],
        },
    },
}


def get_expected_paths(pool: str, phase: Optional[str] = None) -> list[str]:
    """Return the list of included paths for a pool/phase combination."""
    if pool not in POOL_SPARSE_CONFIGS:
        raise ValueError(f"unknown pool: {pool}")
    configs = POOL_SPARSE_CONFIGS[pool]
    key = phase if phase and phase in configs else "default"
    if key not in configs:
        raise ValueError(f"pool '{pool}' requires a phase, got '{phase}'")
    return configs[key]["include"]


def validate_pool_isolation(
    worktree_path: Path,
    pool: str,
    phase: Optional[str] = None,
) -> dict[str, Any]:
    """Check that a worktree contains only what the pool should see.

    Verifies that excluded directories are NOT present in the worktree.
    Returns {"valid": bool, "violations": list[str]}.
    """
    wt = Path(worktree_path)
    if pool not in POOL_SPARSE_CONFIGS:
        raise ValueError(f"unknown pool: {pool}")

    configs = POOL_SPARSE_CONFIGS[pool]
    key = phase if phase and phase in configs else "default"
    if key not in configs:
        raise ValueError(f"pool '{pool}' requires a phase, got '{phase}'")

    config = configs[key]
    violations: list[str] = []

    # Check excluded paths are absent
    for excluded in config["exclude"]:
        excluded_path = wt / excluded.rstrip("/")
        if excluded_path.exists():
            violations.append(f"excluded path present: {excluded}")

    return {"valid": len(violations) == 0, "violations": violations}
