"""PreToolUse hook: blocks source code writes until spec cascade is complete."""

import json
import os
import re
import sys
from pathlib import Path, PurePath
from typing import Optional

from hooks.utils.branch_parser import parse_branch
from hooks.utils.config_loader import (
    find_project_root,
    load_harness_config,
    resolve_feature_folder,
)

EXCLUSION_PATTERNS = [
    "tests/**/*", "test/**/*", "*_test.*", "test_*.*",
    "*.md",
    ".harness.json", ".gitignore", "*.toml", "*.json", "*.yaml", "*.yml",
    ".claude/**/*", ".claude/*", ".agents/**/*", ".agents/*", ".github/**/*", ".github/*",
]

ALLOWED_PHASES = {"execution", "quality-gate", "pr-review"}
MIN_SPEC_LENGTH = 50
REQUIRED_SPECS = ["proposal.md", "behavior_spec.md", "test_spec.md"]


def is_source_file(file_path: str, registry_path: Optional[str] = None, file_path_abs: Optional[str] = None) -> bool:
    """Check if a file is a source file (requires cascade check)."""
    for pattern in EXCLUSION_PATTERNS:
        if PurePath(file_path).match(pattern):
            return False

    if registry_path and file_path_abs:
        try:
            Path(file_path_abs).relative_to(registry_path)
            return False
        except ValueError:
            pass

    return True


def read_phase_from_status(status_content: str) -> Optional[str]:
    """Extract the current phase from status.md content."""
    match = re.search(r"`(\w[\w-]*)`", status_content)
    return match.group(1) if match else None


def check_spec_cascade(feature_folder: str) -> dict:
    """Check if the spec cascade is complete for a feature."""
    feature_path = Path(feature_folder)
    if not feature_path.exists():
        return {"decision": "block", "reason": f"OpenSpec folder not found: {feature_folder}"}

    missing = []
    for spec_file in REQUIRED_SPECS:
        spec_path = feature_path / spec_file
        if not spec_path.exists():
            missing.append(f"{spec_file} (missing)")
        elif len(spec_path.read_text().strip()) < MIN_SPEC_LENGTH:
            missing.append(f"{spec_file} (too short, likely template)")

    if missing:
        return {"decision": "block", "reason": f"Spec cascade incomplete. Issues: {', '.join(missing)}"}

    status_path = feature_path / "status.md"
    if not status_path.exists():
        return {"decision": "block", "reason": "status.md not found in OpenSpec folder."}

    phase = read_phase_from_status(status_path.read_text())
    if phase not in ALLOWED_PHASES:
        return {"decision": "block", "reason": f"Current phase is '{phase}'. Code requires phase 'execution' or later."}

    return {"decision": "allow"}


def main():
    """Entry point for Claude Code hook."""
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        json.dump({"decision": "allow"}, sys.stdout)
        return

    file_path_abs = input_data.get("tool_input", {}).get("file_path", "")

    project_root = find_project_root(os.getcwd())
    if not project_root:
        json.dump({"decision": "allow"}, sys.stdout)
        return

    try:
        file_path = str(Path(file_path_abs).relative_to(project_root))
    except ValueError:
        file_path = file_path_abs

    config = load_harness_config(project_root)
    if not config:
        json.dump({"decision": "allow"}, sys.stdout)
        return

    registry_path = config.get("registry_path")

    if not is_source_file(file_path, registry_path=registry_path, file_path_abs=file_path_abs):
        json.dump({"decision": "allow"}, sys.stdout)
        return

    branch_info = parse_branch()
    feature = branch_info["feature"]
    if not feature:
        json.dump({"decision": "allow"}, sys.stdout)
        return

    if not registry_path:
        json.dump({"decision": "allow"}, sys.stdout)
        return

    feature_folder = resolve_feature_folder(registry_path, feature)
    if not feature_folder:
        json.dump({"decision": "block", "reason": f"No OpenSpec found for feature '{feature}'."}, sys.stdout)
        return

    result = check_spec_cascade(feature_folder)
    json.dump(result, sys.stdout)


if __name__ == "__main__":
    main()
