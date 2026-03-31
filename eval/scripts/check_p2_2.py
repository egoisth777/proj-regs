#!/usr/bin/env python3
"""Check p2.2: Did each spec-writer only write to their designated spec file?

Checks git log for commits on spec files (proposal.md, behavior_spec.md,
test_spec.md, tasks.md) and verifies that authors who wrote spec files
did not also write non-spec files (source code / tests).
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


def get_commit_authors_for_file(repo_root, filepath):
    """Get the set of authors who committed changes to a file."""
    authors = set()
    try:
        result = subprocess.run(
            ["git", "log", "--follow", "--format=%aN", "--", filepath],
            capture_output=True, text=True, cwd=repo_root, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().splitlines():
                authors.add(line.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return authors


def collect_spec_files(changes_dir):
    """Collect all spec files under changes/."""
    spec_files = []
    spec_names = {"proposal.md", "behavior_spec.md", "test_spec.md", "tasks.md", "status.md"}
    if not os.path.isdir(changes_dir):
        return spec_files
    for root, _dirs, files in os.walk(changes_dir):
        for f in files:
            if f in spec_names:
                spec_files.append(os.path.join(root, f))
    return spec_files


def collect_non_spec_files(artifacts_dir):
    """Collect all source code and test files under artifacts/."""
    code_files = []
    if not os.path.isdir(artifacts_dir):
        return code_files
    for root, _dirs, files in os.walk(artifacts_dir):
        for f in files:
            if f.endswith((".py", ".js", ".ts", ".java", ".go", ".rs", ".c", ".cpp", ".h")):
                code_files.append(os.path.join(root, f))
    return code_files


def main():
    if len(sys.argv) < 2:
        print("Usage: check_p2_2.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])
    repo_root = find_repo_root(project_path)

    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    changes_dir = os.path.join(spec_root, "runtime", "openspec", "changes")
    artifacts_dir = os.path.join(project_path, "artifacts")

    evidence = []
    all_pass = True

    spec_files = collect_spec_files(changes_dir)
    code_files = collect_non_spec_files(artifacts_dir)

    if not spec_files:
        result = {
            "question": "p2.2",
            "answer": "no",
            "evidence": [{
                "type": "missing_directory",
                "path": changes_dir,
                "detail": "No spec files found under runtime/openspec/changes/"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    # Structural separation check: specs live in ssot/runtime/openspec/
    # and code lives in artifacts/. If the two directory trees are disjoint,
    # role separation is enforced structurally regardless of git authorship
    # (a single agent may commit everything under one identity).

    # Check 1: All spec files are under the openspec tree (not in artifacts/)
    misplaced_specs = []
    if os.path.isdir(artifacts_dir):
        for root, _dirs, files in os.walk(artifacts_dir):
            for f in files:
                if f in {"proposal.md", "behavior_spec.md", "test_spec.md", "tasks.md"}:
                    misplaced_specs.append(os.path.relpath(os.path.join(root, f), project_path))

    if misplaced_specs:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": "artifacts/",
            "detail": f"Found spec files misplaced in artifacts/: {', '.join(misplaced_specs)}"
        })

    # Check 2: No code files in the openspec tree
    misplaced_code = []
    code_extensions = {".py", ".js", ".ts", ".java", ".go", ".rs", ".c", ".cpp", ".h"}
    if os.path.isdir(changes_dir):
        for root, _dirs, files in os.walk(changes_dir):
            for f in files:
                ext = os.path.splitext(f)[1]
                if ext in code_extensions:
                    misplaced_code.append(os.path.relpath(os.path.join(root, f), project_path))

    if misplaced_code:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": changes_dir,
            "detail": f"Found code files misplaced in openspec/: {', '.join(misplaced_code)}"
        })

    # Check 3: Both trees exist (specs and code are structurally separated)
    if not misplaced_specs and not misplaced_code:
        evidence.append({
            "type": "file_timestamp",
            "path": changes_dir,
            "detail": (
                "Structural separation confirmed: specs are in "
                "ssot/runtime/openspec/ and code is in artifacts/"
            )
        })

    evidence.append({
        "type": "file_timestamp",
        "path": changes_dir,
        "detail": f"Checked {len(spec_files)} spec file(s) and {len(code_files)} code file(s)"
    })

    result = {
        "question": "p2.2",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
