#!/usr/bin/env python3
"""Check p3.5: Was the total agent count within the expected range for the project scope?

Counts unique agent roles mentioned in tasks.md and git commit messages.
Expected range: 2-10 agents for a typical project.
"""

import os
import re
import subprocess
import sys
import yaml


EXPECTED_MIN = 2
EXPECTED_MAX = 10


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


def extract_roles_from_tasks(spec_root):
    """Extract unique role names from tasks.md files."""
    roles = set()

    # Search for tasks.md in runtime and feature directories
    search_dirs = [
        os.path.join(spec_root, "runtime"),
        os.path.join(spec_root, "runtime", "openspec", "changes"),
    ]

    role_patterns = [
        re.compile(r"(?:role|agent|assigned[\s_-]*to|worker|sdet|team[\s_-]*lead|orchestrator)\s*[:\-=]\s*(\S+)", re.IGNORECASE),
        re.compile(r"(worker[-_]?\d+|sdet[-_]?\w+|team[-_]?lead|orchestrator|spec[-_]?writer)", re.IGNORECASE),
    ]

    for search_dir in search_dirs:
        if not os.path.isdir(search_dir):
            continue
        for root, _dirs, files in os.walk(search_dir):
            for fname in files:
                if fname == "tasks.md" or fname == "active_sprint.md":
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                            content = f.read()
                    except OSError:
                        continue

                    for pattern in role_patterns:
                        for match in pattern.finditer(content):
                            role = match.group(1) if match.lastindex else match.group(0)
                            roles.add(role.strip().lower())

    return roles


def extract_roles_from_commits(repo_root):
    """Extract unique role/agent names from commit messages and branch names."""
    roles = set()
    try:
        result = subprocess.run(
            ["git", "log", "--all", "--format=%s%n%D", "--max-count=200"],
            capture_output=True, text=True, cwd=repo_root, timeout=30
        )
        if result.returncode == 0:
            content = result.stdout
            # Look for branch-based roles: feat/<name>/<role>
            branch_pattern = re.compile(r"feat/[\w-]+/([\w-]+)")
            for m in branch_pattern.finditer(content):
                roles.add(m.group(1).lower())

            # Look for role mentions in commit messages
            role_pattern = re.compile(r"(worker[-_]?\d+|sdet[-_]?\w+|team[-_]?lead|orchestrator|spec[-_]?writer)", re.IGNORECASE)
            for m in role_pattern.finditer(content):
                roles.add(m.group(1).lower())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return roles


def main():
    if len(sys.argv) < 2:
        print("Usage: check_p3_5.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])
    repo_root = find_repo_root(project_path)

    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    evidence = []
    all_pass = True

    tasks_roles = extract_roles_from_tasks(spec_root)
    commit_roles = extract_roles_from_commits(repo_root)

    all_roles = tasks_roles | commit_roles
    agent_count = len(all_roles)

    evidence.append({
        "type": "file_timestamp",
        "path": project_path,
        "detail": (
            f"Found {agent_count} unique agent role(s): "
            f"{', '.join(sorted(all_roles)) if all_roles else 'none'}"
        )
    })

    if tasks_roles:
        evidence.append({
            "type": "file_timestamp",
            "path": "tasks.md",
            "detail": f"Roles from tasks/sprint files: {', '.join(sorted(tasks_roles))}"
        })

    if commit_roles:
        evidence.append({
            "type": "file_timestamp",
            "path": "git log",
            "detail": f"Roles from commits/branches: {', '.join(sorted(commit_roles))}"
        })

    if agent_count < EXPECTED_MIN:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": project_path,
            "detail": (
                f"Agent count ({agent_count}) is below expected minimum "
                f"({EXPECTED_MIN}) -- too few agents for project scope"
            )
        })
    elif agent_count > EXPECTED_MAX:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": project_path,
            "detail": (
                f"Agent count ({agent_count}) exceeds expected maximum "
                f"({EXPECTED_MAX}) -- too many agents for project scope"
            )
        })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": project_path,
            "detail": (
                f"Agent count ({agent_count}) is within expected range "
                f"[{EXPECTED_MIN}, {EXPECTED_MAX}] -- OK"
            )
        })

    result = {
        "question": "p3.5",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
