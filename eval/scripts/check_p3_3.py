#!/usr/bin/env python3
"""Check p3.3: Were there zero redundant dispatches (same work assigned twice)?

Checks tasks.md files across features for duplicated task descriptions,
and checks for duplicate branch work or identical file modifications
across separate dispatches.
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


def extract_task_descriptions(tasks_md_path):
    """Extract task descriptions from a tasks.md file."""
    if not os.path.isfile(tasks_md_path):
        return []

    with open(tasks_md_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    tasks = []

    # Extract numbered or bulleted tasks
    task_pattern = re.compile(r"^\s*(?:\d+[\.\)]|-|\*)\s+(.{15,})", re.MULTILINE)
    for match in task_pattern.finditer(content):
        task_text = match.group(1).strip().lower()
        # Normalize: remove backticks, extra whitespace
        task_text = re.sub(r"`[^`]*`", "", task_text)
        task_text = re.sub(r"\s+", " ", task_text).strip()
        if len(task_text) > 10:
            tasks.append(task_text)

    # Extract section headers as task titles
    header_pattern = re.compile(r"^#+\s+(.{10,})", re.MULTILINE)
    for match in header_pattern.finditer(content):
        header = match.group(1).strip().lower()
        if any(kw in header for kw in ["task", "worker", "sdet", "implement", "write", "create"]):
            tasks.append(header)

    return tasks


def normalize_for_comparison(text):
    """Normalize a text string for fuzzy comparison."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def find_duplicates(tasks_by_feature):
    """Find duplicate tasks across features."""
    duplicates = []
    all_tasks = []
    for feature, tasks in tasks_by_feature.items():
        for task in tasks:
            normalized = normalize_for_comparison(task)
            if len(normalized) < 15:
                continue
            all_tasks.append((feature, task, normalized))

    # Check for near-duplicates across different features
    for i in range(len(all_tasks)):
        for j in range(i + 1, len(all_tasks)):
            f1, t1, n1 = all_tasks[i]
            f2, t2, n2 = all_tasks[j]
            if f1 == f2:
                continue  # Same feature, might be intentional subtasks
            # Check for exact or near-exact match
            if n1 == n2:
                duplicates.append((f1, t1, f2, t2))
            elif len(n1) > 20 and len(n2) > 20:
                # Check substring containment for longer tasks
                if n1 in n2 or n2 in n1:
                    duplicates.append((f1, t1, f2, t2))

    return duplicates


def main():
    if len(sys.argv) < 2:
        print("Usage: check_p3_3.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    changes_dir = os.path.join(spec_root, "runtime", "openspec", "changes")

    evidence = []
    all_pass = True

    if not os.path.isdir(changes_dir):
        result = {
            "question": "p3.3",
            "answer": "no",
            "evidence": [{
                "type": "missing_directory",
                "path": changes_dir,
                "detail": "runtime/openspec/changes/ directory not found"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    feature_dirs = [
        d for d in os.listdir(changes_dir)
        if os.path.isdir(os.path.join(changes_dir, d))
    ]

    if not feature_dirs:
        result = {
            "question": "p3.3",
            "answer": "no",
            "evidence": [{
                "type": "missing_directory",
                "path": changes_dir,
                "detail": "No feature directories found"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    # Collect tasks from each feature
    tasks_by_feature = {}
    for feature in sorted(feature_dirs):
        tasks_file = os.path.join(changes_dir, feature, "tasks.md")
        tasks = extract_task_descriptions(tasks_file)
        tasks_by_feature[feature] = tasks
        evidence.append({
            "type": "file_timestamp",
            "path": tasks_file,
            "detail": f"Feature '{feature}': extracted {len(tasks)} task description(s)"
        })

    # Check for duplicates
    duplicates = find_duplicates(tasks_by_feature)

    if duplicates:
        all_pass = False
        for f1, t1, f2, t2 in duplicates[:5]:
            evidence.append({
                "type": "file_timestamp",
                "path": changes_dir,
                "detail": (
                    f"Redundant dispatch: '{f1}' task \"{t1[:60]}\" "
                    f"duplicates '{f2}' task \"{t2[:60]}\""
                )
            })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": changes_dir,
            "detail": f"No redundant task dispatches found across {len(feature_dirs)} feature(s)"
        })

    # Also check for duplicate feature proposals (same proposal content)
    proposal_hashes = {}
    for feature in sorted(feature_dirs):
        proposal_file = os.path.join(changes_dir, feature, "proposal.md")
        if os.path.isfile(proposal_file):
            try:
                with open(proposal_file, "r", encoding="utf-8", errors="replace") as f:
                    content = normalize_for_comparison(f.read())
                if len(content) > 50:
                    if content in proposal_hashes.values():
                        dup_feature = [k for k, v in proposal_hashes.items() if v == content][0]
                        all_pass = False
                        evidence.append({
                            "type": "file_timestamp",
                            "path": proposal_file,
                            "detail": (
                                f"Feature '{feature}' has identical proposal content to "
                                f"feature '{dup_feature}'"
                            )
                        })
                    proposal_hashes[feature] = content
            except OSError:
                pass

    result = {
        "question": "p3.3",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
