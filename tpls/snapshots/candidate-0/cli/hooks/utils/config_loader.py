"""Load .harness.json, context_map.json, and resolve feature folders."""

import json
import os
import sys
from pathlib import Path
from typing import Optional


def find_project_root(start_path: str) -> Optional[str]:
    """Walk up from start_path to find directory containing .harness.json."""
    current = Path(start_path).resolve()
    while current != current.parent:
        if (current / ".harness.json").exists():
            return str(current)
        current = current.parent
    if (current / ".harness.json").exists():
        return str(current)
    return None


def load_harness_config(project_root: str) -> Optional[dict]:
    """Load .harness.json from project root. Returns None if missing."""
    config_path = Path(project_root) / ".harness.json"
    if not config_path.exists():
        return None
    with open(config_path) as f:
        config = json.load(f)
    # support both old and new field names
    if "cli_path" not in config and "harness_cli_path" in config:
        config["cli_path"] = config["harness_cli_path"]
    return config


def load_context_map(registry_path: str) -> dict:
    """Load context_map.json from registry. Raises FileNotFoundError if missing."""
    cm_path = Path(registry_path) / "context_map.json"
    if not cm_path.exists():
        raise FileNotFoundError(f"context_map.json not found at {cm_path}")
    with open(cm_path) as f:
        return json.load(f)


def resolve_feature_folder(registry_path: str, feature_name: str) -> Optional[str]:
    """Resolve feature name to OpenSpec folder, handling date prefixes.

    Scans runtime/openspec/changes/ for folders ending with -<feature_name>.
    Returns most recent (by date prefix) if multiple match. None if no match.
    """
    changes_dir = Path(registry_path) / "runtime" / "openspec" / "changes"
    if not changes_dir.exists():
        return None

    matches = []
    for entry in changes_dir.iterdir():
        if entry.is_dir() and entry.name.endswith(f"-{feature_name}"):
            matches.append(entry)
        elif entry.is_dir() and entry.name == feature_name:
            matches.append(entry)

    if not matches:
        return None

    matches.sort(key=lambda p: p.name, reverse=True)
    return str(matches[0])
