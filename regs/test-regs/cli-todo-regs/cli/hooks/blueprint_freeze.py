"""PreToolUse hook: blocks ALL writes to blueprint/** when a sprint is active."""

import json
import os
import sys
from pathlib import Path

from hooks.utils.config_loader import find_project_root, load_harness_config


def is_sprint_active(sprint_file: Path) -> bool:
    """Check if there is an active sprint by reading active_sprint.md.

    Returns True if the file contains indicators like "Current Feature:" or "Phase:".
    Returns False for empty, missing, or "No active sprint" content.
    """
    if not sprint_file.exists():
        return False

    content = sprint_file.read_text().strip()
    if not content:
        return False

    if "No active sprint" in content:
        return False

    if "Current Feature:" in content or "Phase:" in content:
        return True

    return False


def check_blueprint_freeze(file_path: str, sprint_file: Path) -> dict:
    """Check if a blueprint write should be blocked due to active sprint.

    If file_path starts with "blueprint/" AND sprint is active, block.
    Otherwise allow.
    """
    if not file_path.startswith("blueprint/"):
        return {"decision": "allow"}

    if not is_sprint_active(sprint_file):
        return {"decision": "allow"}

    return {
        "decision": "block",
        "reason": "Blueprint is frozen during an active sprint. Complete or close the sprint before modifying blueprint files.",
    }


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

    config = load_harness_config(project_root)
    if not config:
        json.dump({"decision": "allow"}, sys.stdout)
        return

    registry_path = config.get("registry_path")
    if not registry_path:
        json.dump({"decision": "allow"}, sys.stdout)
        return

    # Resolve file_path relative to the registry
    try:
        file_path = str(Path(file_path_abs).relative_to(registry_path))
    except ValueError:
        # File is not within the registry -- not a blueprint file
        json.dump({"decision": "allow"}, sys.stdout)
        return

    sprint_file = Path(registry_path) / "runtime" / "active_sprint.md"
    result = check_blueprint_freeze(file_path, sprint_file)
    json.dump(result, sys.stdout)


if __name__ == "__main__":
    main()
