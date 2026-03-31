#!/usr/bin/env python3
"""Check p2.5: Were there zero hook violations (blocked writes) during the sprint?

Checks for hook violation indicators:
- .git/hooks/ scripts that enforce path boundaries
- Log files or records of blocked writes
- Git stash or rejected commit evidence
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


def check_hook_violation_logs(project_path):
    """Search for hook violation log files."""
    violations = []
    # Common locations for hook violation logs
    candidates = [
        os.path.join(project_path, ".hook-violations.log"),
        os.path.join(project_path, "hook-violations.log"),
        os.path.join(project_path, ".harness", "violations.log"),
        os.path.join(project_path, "logs", "hook-violations.log"),
    ]

    # Also search recursively for violation logs
    for root, _dirs, files in os.walk(project_path):
        # Skip .git directory
        if ".git" in root.split(os.sep):
            continue
        for f in files:
            if "violation" in f.lower() and f.endswith((".log", ".txt", ".md")):
                fp = os.path.join(root, f)
                if fp not in candidates:
                    candidates.append(fp)

    for candidate in candidates:
        if os.path.isfile(candidate):
            try:
                with open(candidate, "r", encoding="utf-8", errors="replace") as fh:
                    content = fh.read()
                if content.strip():
                    # Count violation entries
                    violation_lines = [
                        l for l in content.splitlines()
                        if any(kw in l.lower() for kw in ["blocked", "violation", "rejected", "denied"])
                    ]
                    if violation_lines:
                        violations.append({
                            "file": candidate,
                            "count": len(violation_lines),
                            "sample": violation_lines[0][:200]
                        })
            except OSError:
                pass

    return violations


def check_git_commit_messages(repo_root, project_rel):
    """Check git commit messages for hook violation indicators."""
    violations = []
    try:
        result = subprocess.run(
            ["git", "log", "--all", "--oneline", "-100", "--", project_rel if project_rel else "."],
            capture_output=True, text=True, cwd=repo_root, timeout=30
        )
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines():
                lower = line.lower()
                if any(kw in lower for kw in ["hook violation", "blocked write", "scope violation"]):
                    violations.append(line.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return violations


def check_hooks_exist(repo_root):
    """Check if pre-commit hooks exist that enforce scope."""
    hooks_dir = os.path.join(repo_root, ".git", "hooks")
    harness_hooks = os.path.join(repo_root, ".harness", "hooks")

    hook_info = []
    for hdir in [hooks_dir, harness_hooks]:
        if os.path.isdir(hdir):
            for f in os.listdir(hdir):
                fp = os.path.join(hdir, f)
                if os.path.isfile(fp) and os.access(fp, os.X_OK):
                    hook_info.append(os.path.relpath(fp, repo_root))

    return hook_info


def main():
    if len(sys.argv) < 2:
        print("Usage: check_p2_5.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])
    repo_root = find_repo_root(project_path)
    project_rel = os.path.relpath(project_path, repo_root)
    if project_rel == ".":
        project_rel = ""

    evidence = []
    all_pass = True

    # Check 1: Look for violation logs
    log_violations = check_hook_violation_logs(project_path)
    if log_violations:
        all_pass = False
        for v in log_violations:
            evidence.append({
                "type": "file_timestamp",
                "path": v["file"],
                "detail": f"Violation log found: {v['count']} violation(s). Sample: {v['sample']}"
            })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": project_path,
            "detail": "No hook violation log files found"
        })

    # Check 2: Look for violation mentions in commit messages
    commit_violations = check_git_commit_messages(repo_root, project_rel)
    if commit_violations:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": "git_log",
            "detail": (
                f"Found {len(commit_violations)} commit(s) mentioning hook violations: "
                f"{'; '.join(commit_violations[:3])}"
            )
        })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": "git_log",
            "detail": "No hook violation references found in commit messages"
        })

    # Check 3: Verify hooks exist (informational)
    hooks = check_hooks_exist(repo_root)
    if hooks:
        evidence.append({
            "type": "file_timestamp",
            "path": ".git/hooks/",
            "detail": f"Found {len(hooks)} executable hook(s): {', '.join(hooks[:5])}"
        })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": ".git/hooks/",
            "detail": "No executable hooks found (scope enforcement may be external)"
        })

    result = {
        "question": "p2.5",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
