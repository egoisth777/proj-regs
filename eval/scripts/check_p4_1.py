#!/usr/bin/env python3
"""Check p4.1: Was active_sprint.md updated at each phase transition?

Checks that active_sprint.md is non-empty and contains feature names or
phase information.
"""

import os
import re
import sys
import yaml


def find_active_sprint(project_path):
    """Search for active_sprint.md in common locations."""
    candidates = [
        os.path.join(project_path, "runtime", "active_sprint.md"),
        os.path.join(project_path, "runtime", "openspec", "active_sprint.md"),
        os.path.join(project_path, "active_sprint.md"),
        os.path.join(project_path, "ssot", "active_sprint.md"),
    ]

    # Also do a recursive search if none of the candidates exist
    for c in candidates:
        if os.path.isfile(c):
            return c

    # Recursive fallback
    for root, _dirs, files in os.walk(project_path):
        for f in files:
            if f == "active_sprint.md":
                return os.path.join(root, f)

    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: check_p4_1.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])
    evidence = []
    all_pass = True

    sprint_file = find_active_sprint(project_path)

    if sprint_file is None:
        result = {
            "question": "p4.1",
            "answer": "no",
            "evidence": [{
                "type": "file_timestamp",
                "path": os.path.join(project_path, "runtime", "active_sprint.md"),
                "detail": "active_sprint.md not found anywhere in the project"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    rel_path = os.path.relpath(sprint_file, project_path)

    # Check non-empty
    try:
        size = os.path.getsize(sprint_file)
    except OSError:
        size = 0

    if size == 0:
        result = {
            "question": "p4.1",
            "answer": "no",
            "evidence": [{
                "type": "file_timestamp",
                "path": rel_path,
                "detail": "active_sprint.md exists but is empty"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    with open(sprint_file, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Check for phase-related keywords
    phase_keywords = [
        "proposal", "behavior", "test_spec", "tasks", "status",
        "phase", "stage", "sprint", "feature", "cascade",
        "in progress", "complete", "pending", "done", "wip",
        "implement", "review", "merge"
    ]

    found_keywords = []
    content_lower = content.lower()
    for kw in phase_keywords:
        if kw in content_lower:
            found_keywords.append(kw)

    # Check for feature names (look for things that look like feature identifiers)
    feature_pattern = re.compile(r"(?:feature|sprint|task)[:\s]+\S+", re.IGNORECASE)
    feature_matches = feature_pattern.findall(content)

    # Check for phase transition markers (dates, status changes, etc.)
    date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}")
    dates_found = date_pattern.findall(content)

    has_phase_info = len(found_keywords) >= 2
    has_features = len(feature_matches) > 0 or any(
        kw in content_lower for kw in ["feature", "sprint"]
    )

    evidence.append({
        "type": "file_timestamp",
        "path": rel_path,
        "detail": f"File size: {size} bytes, {len(content.splitlines())} lines"
    })

    if found_keywords:
        evidence.append({
            "type": "file_timestamp",
            "path": rel_path,
            "detail": f"Phase-related keywords found: {', '.join(found_keywords)}"
        })

    if dates_found:
        evidence.append({
            "type": "file_timestamp",
            "path": rel_path,
            "detail": f"Date stamps found: {', '.join(dates_found[:5])}"
        })

    if feature_matches:
        evidence.append({
            "type": "file_timestamp",
            "path": rel_path,
            "detail": f"Feature references found: {'; '.join(feature_matches[:5])}"
        })

    if has_phase_info or has_features:
        evidence.append({
            "type": "file_timestamp",
            "path": rel_path,
            "detail": "active_sprint.md contains meaningful phase/feature content"
        })
    else:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": rel_path,
            "detail": "active_sprint.md exists but lacks phase transition or feature content"
        })

    result = {
        "question": "p4.1",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
