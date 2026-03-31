#!/usr/bin/env python3
"""Check p3.2: Were independent tasks dispatched in parallel?

Checks for indicators of parallel dispatch:
- Multiple feature branches or worktrees active at the same time
- Overlapping commit timestamps across different roles/branches
- tasks.md mentioning parallel or concurrent dispatch
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


def get_branch_commit_times(repo_root):
    """Get commit timestamps per branch for feat/* branches."""
    branch_times = {}
    try:
        result = subprocess.run(
            ["git", "branch", "-a", "--format=%(refname:short)"],
            capture_output=True, text=True, cwd=repo_root, timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines():
                branch = line.strip()
                if not branch.startswith("feat/"):
                    continue
                # Get first and last commit times on this branch
                ts_result = subprocess.run(
                    ["git", "log", branch, "--format=%ct", "-20"],
                    capture_output=True, text=True, cwd=repo_root, timeout=15
                )
                if ts_result.returncode == 0 and ts_result.stdout.strip():
                    times = [int(t) for t in ts_result.stdout.strip().splitlines() if t.strip()]
                    if times:
                        branch_times[branch] = {
                            "earliest": min(times),
                            "latest": max(times),
                            "count": len(times)
                        }
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        pass
    return branch_times


def check_overlapping_branches(branch_times):
    """Check if any branches have overlapping commit time ranges."""
    branches = sorted(branch_times.keys())
    overlaps = []
    for i in range(len(branches)):
        for j in range(i + 1, len(branches)):
            b1, b2 = branches[i], branches[j]
            t1, t2 = branch_times[b1], branch_times[b2]
            # Check if time ranges overlap
            if t1["earliest"] <= t2["latest"] and t2["earliest"] <= t1["latest"]:
                overlaps.append((b1, b2))
    return overlaps


def check_tasks_for_parallel_keywords(changes_dir):
    """Search tasks.md files for parallel dispatch indicators."""
    indicators = []
    if not os.path.isdir(changes_dir):
        return indicators

    parallel_keywords = [
        "parallel", "concurrent", "simultaneous", "worktree",
        "dispatch", "independent", "in parallel"
    ]

    for root, _dirs, files in os.walk(changes_dir):
        for f in files:
            if f == "tasks.md":
                fp = os.path.join(root, f)
                try:
                    with open(fp, "r", encoding="utf-8", errors="replace") as fh:
                        content = fh.read().lower()
                    found = [kw for kw in parallel_keywords if kw in content]
                    if found:
                        feature = os.path.basename(os.path.dirname(fp))
                        indicators.append({
                            "feature": feature,
                            "keywords": found
                        })
                except OSError:
                    pass

    return indicators


def main():
    if len(sys.argv) < 2:
        print("Usage: check_p3_2.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])
    repo_root = find_repo_root(project_path)

    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    changes_dir = os.path.join(spec_root, "runtime", "openspec", "changes")

    evidence = []
    all_pass = True

    # Check 1: Look for overlapping feature branches
    branch_times = get_branch_commit_times(repo_root)

    if len(branch_times) >= 2:
        overlaps = check_overlapping_branches(branch_times)
        if overlaps:
            evidence.append({
                "type": "file_timestamp",
                "path": "git_branches",
                "detail": (
                    f"Found {len(overlaps)} overlapping branch pair(s) indicating parallel work: "
                    f"{'; '.join(f'{a} <-> {b}' for a, b in overlaps[:3])}"
                )
            })
        else:
            evidence.append({
                "type": "file_timestamp",
                "path": "git_branches",
                "detail": (
                    f"Found {len(branch_times)} feat/ branches but no overlapping time ranges; "
                    f"tasks may have been sequential"
                )
            })
            all_pass = False
    elif len(branch_times) == 1:
        evidence.append({
            "type": "file_timestamp",
            "path": "git_branches",
            "detail": "Only 1 feat/ branch found; parallel dispatch not applicable or not used"
        })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": "git_branches",
            "detail": "No feat/ branches found; checking task-level indicators"
        })

    # Check 2: Look for parallel keywords in tasks
    parallel_indicators = check_tasks_for_parallel_keywords(changes_dir)
    if parallel_indicators:
        evidence.append({
            "type": "file_timestamp",
            "path": changes_dir,
            "detail": (
                "Found parallel dispatch keywords in {} feature(s): {}".format(
                    len(parallel_indicators),
                    "; ".join(
                        "{}: {}".format(i["feature"], ", ".join(i["keywords"]))
                        for i in parallel_indicators[:3]
                    )
                )
            )
        })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": changes_dir,
            "detail": "No parallel dispatch keywords found in tasks.md files"
        })

    # Check 3: Multiple role branches per feature (e.g., feat/auth/worker-1, feat/auth/sdet-unit)
    features_with_multiple_roles = {}
    for branch in branch_times:
        parts = branch.split("/")
        if len(parts) >= 3:
            feature = parts[1]
            role = parts[2]
            features_with_multiple_roles.setdefault(feature, []).append(role)

    multi_role_features = {
        f: roles for f, roles in features_with_multiple_roles.items()
        if len(roles) > 1
    }

    if multi_role_features:
        evidence.append({
            "type": "file_timestamp",
            "path": "git_branches",
            "detail": (
                f"Features with multiple role branches: "
                f"{'; '.join(f'{f}: {len(r)} roles ({', '.join(r)})' for f, r in multi_role_features.items())}"
            )
        })
    # If we found either overlapping branches or parallel keywords, consider it a pass
    if not branch_times and not parallel_indicators:
        all_pass = False

    result = {
        "question": "p3.2",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
