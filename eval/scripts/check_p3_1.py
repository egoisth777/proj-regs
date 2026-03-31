#!/usr/bin/env python3
"""Check p3.1: Was every agent dispatched with an explicit task description?

Checks that tasks.md files exist in each feature folder and contain
explicit task descriptions (not just headers or empty sections).
"""

import os
import re
import sys
import yaml


def main():
    if len(sys.argv) < 2:
        print("Usage: check_p3_1.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    changes_dir = os.path.join(spec_root, "runtime", "openspec", "changes")

    evidence = []
    all_pass = True

    if not os.path.isdir(changes_dir):
        result = {
            "question": "p3.1",
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
            "question": "p3.1",
            "answer": "no",
            "evidence": [{
                "type": "missing_directory",
                "path": changes_dir,
                "detail": "No feature directories found"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    for feature in sorted(feature_dirs):
        feature_path = os.path.join(changes_dir, feature)
        tasks_file = os.path.join(feature_path, "tasks.md")

        if not os.path.isfile(tasks_file):
            all_pass = False
            evidence.append({
                "type": "file_timestamp",
                "path": tasks_file,
                "detail": f"Feature '{feature}': tasks.md not found"
            })
            continue

        with open(tasks_file, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        if len(content.strip()) < 20:
            all_pass = False
            evidence.append({
                "type": "file_timestamp",
                "path": tasks_file,
                "detail": f"Feature '{feature}': tasks.md is too short ({len(content.strip())} chars) to contain task descriptions"
            })
            continue

        # Check for task description patterns
        # Look for role/agent assignments with descriptions
        task_patterns = [
            # "## Worker" or "## SDET" or "### Task:" style headers
            re.compile(r"^#+\s+(?:worker|sdet|spec-writer|team-lead|task)", re.IGNORECASE | re.MULTILINE),
            # "Role:" or "Agent:" or "Assigned:" labels
            re.compile(r"(?:role|agent|assigned|dispatch|task)\s*:", re.IGNORECASE),
            # Bullet-point task descriptions (at least 30 chars after bullet)
            re.compile(r"^\s*[-*]\s+.{30,}", re.MULTILINE),
            # Numbered task list items
            re.compile(r"^\s*\d+[\.\)]\s+.{20,}", re.MULTILINE),
        ]

        found_patterns = 0
        pattern_details = []
        for pattern in task_patterns:
            matches = pattern.findall(content)
            if matches:
                found_patterns += 1
                pattern_details.append(f"{len(matches)} match(es)")

        # Count non-header, non-empty lines as "description lines"
        desc_lines = 0
        for line in content.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and len(stripped) > 10:
                desc_lines += 1

        has_descriptions = found_patterns >= 1 and desc_lines >= 3

        if has_descriptions:
            evidence.append({
                "type": "file_timestamp",
                "path": tasks_file,
                "detail": (
                    f"Feature '{feature}': tasks.md has {desc_lines} description line(s), "
                    f"{found_patterns} task pattern(s) found"
                )
            })
        else:
            all_pass = False
            evidence.append({
                "type": "file_timestamp",
                "path": tasks_file,
                "detail": (
                    f"Feature '{feature}': tasks.md lacks explicit task descriptions "
                    f"({desc_lines} desc lines, {found_patterns} patterns)"
                )
            })

    result = {
        "question": "p3.1",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
