#!/usr/bin/env python3
"""Check p2.1: Did the orchestrator produce zero direct file writes to the project?

Checks that the project structure shows proper role separation:
specs in ssot/ (or runtime/openspec/), code in artifacts/.
Also checks git blame for 'orchestrator' authorship on project files.
"""

import os
import subprocess
import sys
import yaml


def find_repo_root(project_path):
    """Find the git repo root from a project path."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, cwd=project_path, timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return project_path


def check_git_blame_for_orchestrator(repo_root, filepath):
    """Check if any line in a file was authored by 'orchestrator'."""
    try:
        result = subprocess.run(
            ["git", "blame", "--porcelain", "--", filepath],
            capture_output=True, text=True, cwd=repo_root, timeout=30
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.startswith("author ") and "orchestrator" in line.lower():
                    return True
                if line.startswith("committer ") and "orchestrator" in line.lower():
                    return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return False


def collect_source_files(directory):
    """Collect source code files (not specs) in a directory."""
    source_files = []
    if not os.path.isdir(directory):
        return source_files
    for root, _dirs, files in os.walk(directory):
        for f in files:
            if f.endswith((".py", ".js", ".ts", ".java", ".go", ".rs", ".c", ".cpp", ".h")):
                source_files.append(os.path.join(root, f))
    return source_files


def main():
    if len(sys.argv) < 2:
        print("Usage: check_p2_1.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])
    repo_root = find_repo_root(project_path)

    evidence = []
    all_pass = True

    # Check 1: Proper structure separation
    artifacts_dir = os.path.join(project_path, "artifacts")
    ssot_dir = os.path.join(project_path, "ssot")
    runtime_dir = os.path.join(project_path, "runtime")

    has_artifacts = os.path.isdir(artifacts_dir)
    has_spec_area = os.path.isdir(ssot_dir) or os.path.isdir(runtime_dir)

    if has_artifacts and has_spec_area:
        evidence.append({
            "type": "file_timestamp",
            "path": project_path,
            "detail": "Project shows proper role separation: artifacts/ and specs directories exist"
        })
    elif has_artifacts:
        evidence.append({
            "type": "file_timestamp",
            "path": project_path,
            "detail": "artifacts/ exists but no ssot/ or runtime/ spec directory found"
        })
    elif has_spec_area:
        evidence.append({
            "type": "file_timestamp",
            "path": project_path,
            "detail": "Spec directories exist but no artifacts/ directory found"
        })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": project_path,
            "detail": "Neither artifacts/ nor spec directories found -- cannot verify role separation"
        })
        all_pass = False

    # Check 2: Git blame for orchestrator writes on source files
    source_files = collect_source_files(artifacts_dir)
    orchestrator_files = []

    for sf in source_files:
        rel_sf = os.path.relpath(sf, repo_root)
        if check_git_blame_for_orchestrator(repo_root, rel_sf):
            orchestrator_files.append(rel_sf)

    if orchestrator_files:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": "artifacts/",
            "detail": (
                f"Found {len(orchestrator_files)} file(s) with orchestrator in git blame: "
                f"{', '.join(orchestrator_files[:5])}"
            )
        })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": "artifacts/",
            "detail": (
                f"Checked {len(source_files)} source file(s) in artifacts/: "
                f"no orchestrator authorship found in git blame"
            )
        })

    result = {
        "question": "p2.1",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
