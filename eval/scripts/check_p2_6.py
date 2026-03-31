#!/usr/bin/env python3
"""Check p2.6: Did no agent write outside the project registry boundary?

Inspects git log to verify that all committed file paths fall within
the expected registry boundary (regs/<name>-regs/ or the project_path itself).
Files outside the project root are flagged as boundary violations.
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


def get_all_committed_files(repo_root):
    """Get all files ever committed in the repo."""
    try:
        result = subprocess.run(
            ["git", "log", "--all", "--name-only", "--pretty=format:"],
            capture_output=True, text=True, cwd=repo_root, timeout=60
        )
        if result.returncode == 0:
            files = set()
            for line in result.stdout.strip().splitlines():
                line = line.strip()
                if line:
                    files.add(line)
            return files
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return set()


def main():
    if len(sys.argv) < 2:
        print("Usage: check_p2_6.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])
    repo_root = find_repo_root(project_path)

    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    evidence = []
    all_pass = True

    # Determine the project's relative path within the repo
    rel_project = os.path.relpath(project_path, repo_root)
    if rel_project == ".":
        # Project IS the repo root; all files are within boundary
        evidence.append({
            "type": "file_timestamp",
            "path": project_path,
            "detail": "Project path is the repo root; all files are within boundary by definition"
        })
        result = {
            "question": "p2.6",
            "answer": "yes",
            "evidence": evidence
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    committed_files = get_all_committed_files(repo_root)

    if not committed_files:
        evidence.append({
            "type": "file_timestamp",
            "path": project_path,
            "detail": "No committed files found in repository"
        })
        result = {
            "question": "p2.6",
            "answer": "yes",
            "evidence": evidence
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    # Allowed paths: anything under the project registry path
    # Also allow top-level config files (.harness.json, .agents/, eval/, etc.)
    allowed_prefixes = [
        rel_project + "/",
        ".harness.json",
        ".agents/",
        "eval/",
        "CLAUDE.md",
        ".gitignore",
    ]

    # Also allow regs/ directory broadly (registries)
    if not rel_project.startswith("regs/"):
        allowed_prefixes.append("regs/")

    violations = []
    for fpath in sorted(committed_files):
        in_boundary = any(
            fpath == prefix or fpath.startswith(prefix)
            for prefix in allowed_prefixes
        )
        if not in_boundary:
            violations.append(fpath)

    if violations:
        all_pass = False
        shown = violations[:20]
        evidence.append({
            "type": "file_timestamp",
            "path": project_path,
            "detail": (
                f"Found {len(violations)} file(s) committed outside project boundary "
                f"({rel_project}/): {', '.join(shown)}"
                + (f" ... and {len(violations) - 20} more" if len(violations) > 20 else "")
            )
        })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": project_path,
            "detail": (
                f"All {len(committed_files)} committed file(s) are within the project "
                f"boundary ({rel_project}/) or allowed top-level paths"
            )
        })

    result = {
        "question": "p2.6",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
