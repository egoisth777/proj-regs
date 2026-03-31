"""PreToolUse hook: enforces one-way layer dependencies for pool agents."""

import json
import os
import sys
from pathlib import Path
from typing import Optional

from hooks.utils.config_loader import find_project_root


# Layers identified by first path component
LAYER_NAMES = {"eval", "tpls", "regs", "eval-loop"}

# Tools that perform write operations
WRITE_TOOLS = {"Edit", "Write", "NotebookEdit"}

# Pool roles that this hook governs
POOL_ROLES = {"pool-e", "pool-t", "pool-v", "pool-r", "orchestrator"}

# Pools that cannot write anything at all
READ_ONLY_POOLS = {"pool-v", "pool-r"}

# eval subdirs that pool-t can READ
POOL_T_READABLE_EVAL_SUBDIRS = {"criteria", "tiers"}

# eval subdirs that pool-t can WRITE
POOL_T_WRITABLE_EVAL_SUBDIRS = {"scripts"}

# eval subdirs that pool-v can READ
POOL_V_READABLE_EVAL_SUBDIRS = {"scripts"}


def get_layer(file_path: str) -> Optional[str]:
    """Return the layer name based on the first path component.

    Returns "eval", "tpls", "regs", or "orchestrator", or None for other paths.
    """
    if not file_path:
        return None
    parts = Path(file_path).parts
    if not parts:
        return None
    first = parts[0]
    if first in LAYER_NAMES:
        return first
    return None


def _get_eval_subdir(file_path: str) -> Optional[str]:
    """Return the eval subdirectory (e.g. 'criteria', 'scripts') or None."""
    parts = Path(file_path).parts
    if len(parts) >= 2 and parts[0] == "eval":
        return parts[1]
    return None


def validate_layer_access(role: str, file_path: str, operation: str) -> dict:
    """Validate whether a pool role can access a file path.

    Args:
        role: The pool role (pool-e, pool-t, pool-v, pool-r, orchestrator) or any other role.
        file_path: Relative file path from project root.
        operation: "read" or "write".

    Returns:
        {"decision": "allow"} or {"decision": "block", "reason": "..."}.
    """
    # Non-pool roles pass through
    if role not in POOL_ROLES:
        return {"decision": "allow"}

    layer = get_layer(file_path)

    # Non-layer paths: pool roles can only read, not write
    if layer is None:
        if operation == "write":
            return {
                "decision": "block",
                "reason": f"Role '{role}' cannot write non-layer paths.",
            }
        return {"decision": "allow"}

    # ── pool-e: read+write tpls/ and regs/, cannot see eval/ at all ──
    if role == "pool-e":
        if layer in ("tpls", "regs"):
            return {"decision": "allow"}
        return {
            "decision": "block",
            "reason": f"Role '{role}' cannot {operation} '{layer}/' layer.",
        }

    # ── pool-t: nuanced eval access, no tpls/regs/orchestrator ──
    if role == "pool-t":
        if layer == "eval":
            subdir = _get_eval_subdir(file_path)
            if operation == "read":
                if subdir in POOL_T_READABLE_EVAL_SUBDIRS:
                    return {"decision": "allow"}
                return {
                    "decision": "block",
                    "reason": f"Role '{role}' cannot {operation} 'eval/{subdir}/'.",
                }
            if operation == "write":
                if subdir in POOL_T_WRITABLE_EVAL_SUBDIRS:
                    return {"decision": "allow"}
                return {
                    "decision": "block",
                    "reason": f"Role '{role}' cannot {operation} 'eval/{subdir or file_path}'.",
                }
        # tpls, regs, orchestrator blocked
        return {
            "decision": "block",
            "reason": f"Role '{role}' cannot {operation} '{layer}/' layer.",
        }

    # ── pool-v: read eval/scripts + regs, no writes at all ──
    if role == "pool-v":
        if operation == "write":
            return {
                "decision": "block",
                "reason": f"Role '{role}' cannot {operation} any files.",
            }
        # operation == "read"
        if layer == "eval":
            subdir = _get_eval_subdir(file_path)
            if subdir in POOL_V_READABLE_EVAL_SUBDIRS:
                return {"decision": "allow"}
            return {
                "decision": "block",
                "reason": f"Role '{role}' cannot {operation} 'eval/{subdir}/'.",
            }
        if layer == "regs":
            return {"decision": "allow"}
        return {
            "decision": "block",
            "reason": f"Role '{role}' cannot {operation} '{layer}/' layer.",
        }

    # ── pool-r: read regs/ only, no writes ──
    if role == "pool-r":
        if operation == "write":
            return {
                "decision": "block",
                "reason": f"Role '{role}' cannot {operation} any files.",
            }
        if layer == "regs":
            return {"decision": "allow"}
        return {
            "decision": "block",
            "reason": f"Role '{role}' cannot {operation} '{layer}/' layer.",
        }

    # ── orchestrator: read+write eval-loop/ only, cannot write eval/ ──
    if role == "orchestrator":
        if layer == "eval-loop":
            return {"decision": "allow"}
        return {
            "decision": "block",
            "reason": f"Role '{role}' cannot {operation} '{layer}/' layer.",
        }

    # Fallback (should not be reached)
    return {"decision": "allow"}


def main():
    """Entry point for Claude Code hook.

    Reads JSON from stdin, determines pool from OMNI_POOL env var,
    determines operation from tool_name, calls validate_layer_access.
    """
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        json.dump({"decision": "allow"}, sys.stdout)
        return

    file_path_abs = input_data.get("tool_input", {}).get("file_path", "")
    tool_name = input_data.get("tool_name", "")

    project_root = find_project_root(os.getcwd())
    if not project_root:
        json.dump({"decision": "allow"}, sys.stdout)
        return

    # Determine pool role from environment
    pool = os.environ.get("OMNI_POOL")
    if not pool:
        json.dump({"decision": "allow"}, sys.stdout)
        return

    # Make path relative to project root
    try:
        file_path = str(Path(file_path_abs).relative_to(project_root))
    except ValueError:
        file_path = file_path_abs

    # Determine operation from tool name
    operation = "write" if tool_name in WRITE_TOOLS else "read"

    result = validate_layer_access(pool, file_path, operation)
    json.dump(result, sys.stdout)


if __name__ == "__main__":
    main()
