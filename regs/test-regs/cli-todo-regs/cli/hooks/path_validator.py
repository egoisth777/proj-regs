"""PreToolUse hook: validates write paths based on agent role."""

import json
import os
import re
import sys
from pathlib import Path, PurePath
from typing import Optional

from hooks.utils.branch_parser import parse_branch, _get_current_branch
from hooks.utils.config_loader import (
    find_project_root,
    load_harness_config,
    resolve_feature_folder,
)


def matches_pattern(file_path: str, pattern: str) -> bool:
    """Match a file path against a glob pattern, supporting ** for recursion."""
    return PurePath(file_path).match(pattern)


NO_WRITE_ROLES = {"orchestrator", "auditor", "regression-runner"}

REGISTRY_WRITE_ROLES = {"behavior-spec-writer", "test-spec-writer", "team-lead", "sonders", "negator"}

ROLE_PATHS = {
    "sdet-unit": ["tests/**/*", "test/**/*", "*_test.*", "test_*.*"],
    "sdet-integration": ["tests/**/*", "test/**/*", "*_test.*", "test_*.*"],
    "sdet-e2e": ["tests/**/*", "test/**/*", "*_test.*", "test_*.*"],
}


def parse_worker_file_scope(tasks_md: str, worker_instance: int) -> list[str]:
    """Parse tasks.md and return file scope for the given worker instance."""
    if not tasks_md.strip():
        return []

    task_blocks = re.split(r"(?=### Task \d+:)", tasks_md)
    task_blocks = [b for b in task_blocks if b.strip().startswith("### Task")]

    if worker_instance < 1 or worker_instance > len(task_blocks):
        return []

    block = task_blocks[worker_instance - 1]
    scope = []
    in_file_scope = False
    for line in block.split("\n"):
        if "**File scope:**" in line:
            in_file_scope = True
            continue
        if in_file_scope:
            match = re.match(r"\s*-\s*`([^`]+)`", line)
            if match:
                scope.append(match.group(1))
            elif line.strip() and not line.strip().startswith("-"):
                in_file_scope = False

    return scope


def get_allowed_paths(
    role: str, feature: Optional[str], registry_path: Optional[str]
) -> tuple[list[str], bool]:
    """Return (allowed_path_patterns, is_absolute)."""
    if role in NO_WRITE_ROLES:
        return [], False

    if role in ROLE_PATHS:
        return ROLE_PATHS[role], False

    if role in REGISTRY_WRITE_ROLES and registry_path:
        if role in ("sonders", "negator"):
            return [str(Path(registry_path) / "blueprint" / "design" / "*")], True

        if feature:
            feature_folder = resolve_feature_folder(registry_path, feature)
            if feature_folder:
                if role == "behavior-spec-writer":
                    return [str(Path(feature_folder) / "behavior_spec.md")], True
                elif role == "test-spec-writer":
                    return [str(Path(feature_folder) / "test_spec.md")], True
                elif role == "team-lead":
                    return [
                        str(Path(feature_folder) / "tasks.md"),
                        str(Path(feature_folder) / "status.md"),
                    ], True

    if role in ("behavior-spec-writer", "test-spec-writer", "team-lead", "worker"):
        return [], False

    return ["**/*"], False


def validate_path(
    role: Optional[str],
    feature: Optional[str],
    file_path: str,
    registry_path: Optional[str],
    worker_instance: Optional[int],
    project_root: Optional[str],
    file_path_abs: Optional[str] = None,
) -> dict:
    """Validate whether a role can write to a file path."""
    file_path_abs = file_path_abs or file_path

    if role is None and project_root is None:
        return {"decision": "allow"}

    if role in NO_WRITE_ROLES:
        return {"decision": "block", "reason": f"Role '{role}' is not allowed to write any files."}

    if role == "worker":
        if not registry_path or not feature:
            return {"decision": "block", "reason": "Worker has no feature context."}
        feature_folder = resolve_feature_folder(registry_path, feature)
        if not feature_folder:
            return {"decision": "block", "reason": f"No OpenSpec folder found for feature '{feature}'."}
        tasks_path = Path(feature_folder) / "tasks.md"
        if not tasks_path.exists():
            return {"decision": "block", "reason": f"tasks.md not found for feature '{feature}'."}
        instance = worker_instance or 1
        allowed = parse_worker_file_scope(tasks_path.read_text(), instance)
        if not allowed:
            return {"decision": "block", "reason": f"No file scope found for worker-{instance}."}
        if file_path in allowed:
            return {"decision": "allow"}
        return {"decision": "block", "reason": f"Role 'worker-{instance}' not allowed to write '{file_path}'. Allowed: {allowed}"}

    allowed_patterns, is_absolute = get_allowed_paths(role, feature, registry_path)
    if not allowed_patterns:
        return {"decision": "block", "reason": f"Role '{role}' has no allowed write paths."}

    compare_path = file_path_abs if is_absolute else file_path
    for pattern in allowed_patterns:
        if matches_pattern(compare_path, pattern):
            return {"decision": "allow"}

    return {"decision": "block", "reason": f"Role '{role}' not allowed to write '{file_path}'. Allowed: {allowed_patterns}"}


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
    registry_path = config.get("registry_path") if config else None

    try:
        file_path = str(Path(file_path_abs).relative_to(project_root))
    except ValueError:
        file_path = file_path_abs

    raw_branch = _get_current_branch()
    branch_info = parse_branch()
    role = branch_info["role"]
    feature = branch_info["feature"]

    worker_instance = None
    if role == "worker":
        match = re.search(r"worker-(\d+)", raw_branch)
        worker_instance = int(match.group(1)) if match else 1

    result = validate_path(role, feature, file_path, registry_path, worker_instance, project_root, file_path_abs=file_path_abs)
    json.dump(result, sys.stdout)


if __name__ == "__main__":
    main()
