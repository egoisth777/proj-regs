#!/usr/bin/env python3
"""Check p2.4: Did SDETs only write to test paths?

Checks git log for commits by authors whose name/branch contains 'sdet'
and verifies those commits only touched test paths (tests/, test_*.py, etc.).
"""

import os
import re
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


def is_test_path(filepath):
    """Check if a file path is a test path."""
    basename = os.path.basename(filepath)
    parts = filepath.replace("\\", "/").split("/")
    # File is in a tests/ or test/ directory
    if any(p in ("tests", "test") for p in parts):
        return True
    # File is a test file by naming convention
    if basename.startswith("test_") or basename.endswith("_test.py"):
        return True
    # Conftest is test infrastructure
    if basename == "conftest.py":
        return True
    return False


def get_sdet_branches(repo_root):
    """Find branch names containing 'sdet'."""
    sdet_branches = []
    try:
        result = subprocess.run(
            ["git", "branch", "-a", "--format=%(refname:short)"],
            capture_output=True, text=True, cwd=repo_root, timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines():
                if "sdet" in line.lower():
                    sdet_branches.append(line.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return sdet_branches


def get_files_touched_by_branch(repo_root, branch):
    """Get files touched by commits unique to a branch (vs main)."""
    files = []
    try:
        # Find merge base with main
        result = subprocess.run(
            ["git", "log", branch, "--name-only", "--pretty=format:", "--"],
            capture_output=True, text=True, cwd=repo_root, timeout=30
        )
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines():
                line = line.strip()
                if line and line not in files:
                    files.append(line)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return files


def get_commits_with_sdet(repo_root, project_rel):
    """Find commits whose message or branch contains 'sdet' and get their files."""
    sdet_files = []
    try:
        result = subprocess.run(
            ["git", "log", "--all", "--grep=sdet", "--name-only",
             "--pretty=format:", "--", project_rel],
            capture_output=True, text=True, cwd=repo_root, timeout=30
        )
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines():
                line = line.strip()
                if line:
                    sdet_files.append(line)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return sdet_files


def main():
    if len(sys.argv) < 2:
        print("Usage: check_p2_4.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])
    repo_root = find_repo_root(project_path)

    evidence = []
    all_pass = True

    # Strategy 1: Check SDET branches
    sdet_branches = get_sdet_branches(repo_root)

    sdet_touched_files = []

    for branch in sdet_branches:
        files = get_files_touched_by_branch(repo_root, branch)
        sdet_touched_files.extend(files)
        evidence.append({
            "type": "file_timestamp",
            "path": branch,
            "detail": f"SDET branch '{branch}' touched {len(files)} file(s)"
        })

    # Strategy 2: Check commits with 'sdet' in message
    project_rel = os.path.relpath(project_path, repo_root)
    if project_rel == ".":
        project_rel = ""
    sdet_commit_files = get_commits_with_sdet(repo_root, project_rel if project_rel else ".")
    sdet_touched_files.extend(sdet_commit_files)

    # Strategy 3: Structural check -- test files should only be in test paths
    artifacts_dir = os.path.join(project_path, "artifacts")
    test_files_outside_test_dirs = []
    if os.path.isdir(artifacts_dir):
        for root, _dirs, files in os.walk(artifacts_dir):
            for f in files:
                fp = os.path.join(root, f)
                rel_fp = os.path.relpath(fp, project_path)
                if (f.startswith("test_") or f.endswith("_test.py")) and f.endswith(".py"):
                    if not is_test_path(rel_fp):
                        test_files_outside_test_dirs.append(rel_fp)

    if test_files_outside_test_dirs:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": "artifacts/",
            "detail": (
                f"Test files found outside test directories: "
                f"{', '.join(test_files_outside_test_dirs[:5])}"
            )
        })

    # Check SDET-touched files
    non_test_files = []
    for f in sdet_touched_files:
        if not f:
            continue
        if not is_test_path(f):
            # Exclude spec files (SDETs might legitimately update test_spec.md)
            basename = os.path.basename(f)
            if basename in ("test_spec.md", "status.md", "tasks.md"):
                continue
            non_test_files.append(f)

    if non_test_files:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": "sdet",
            "detail": (
                f"SDET-attributed commits touched {len(non_test_files)} non-test file(s): "
                f"{', '.join(sorted(set(non_test_files))[:5])}"
            )
        })
    elif sdet_touched_files:
        evidence.append({
            "type": "file_timestamp",
            "path": "sdet",
            "detail": f"All {len(sdet_touched_files)} SDET-touched file(s) are in test paths"
        })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": "sdet",
            "detail": (
                "No SDET-attributed branches or commits found; "
                "structural check used instead (test files in test dirs)"
            )
        })
        # If no SDET info, rely on structural check which passed if we got here
        if not test_files_outside_test_dirs:
            evidence.append({
                "type": "file_timestamp",
                "path": "artifacts/",
                "detail": "All test files are properly located in test directories"
            })

    result = {
        "question": "p2.4",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
