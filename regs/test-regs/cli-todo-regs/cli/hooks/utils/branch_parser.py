"""Parse git branch name to extract agent role and feature."""

import re
import subprocess
import sys


def _get_current_branch() -> str:
    """Get the current git branch name. Returns empty string on detached HEAD."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def parse_branch() -> dict:
    """Parse current branch into feature and role.

    Convention: feat/<feature-name>/<role>[-<instance>]

    Returns:
        {"feature": str|None, "role": str}
        Fallback: {"feature": None, "role": "orchestrator"}
    """
    branch = _get_current_branch()
    if not branch:
        return {"feature": None, "role": "orchestrator"}

    match = re.match(r"^feat/([^/]+)/([^/]+?)(?:-\d+)?(?:/.*)?$", branch)
    if not match:
        feat_only = re.match(r"^feat/([^/]+)$", branch)
        if feat_only:
            return {"feature": feat_only.group(1), "role": "orchestrator"}
        return {"feature": None, "role": "orchestrator"}

    feature = match.group(1)
    role = match.group(2)
    return {"feature": feature, "role": role}
