#!/usr/bin/env python3
"""Check p4.6: Was milestones.md updated upon sprint completion?

Checks that milestones.md exists, is non-empty, and contains completion markers.
"""

import os
import re
import sys
import yaml


def main():
    if len(sys.argv) < 2:
        print("Usage: check_p4_6.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    evidence = []
    all_pass = True

    # Locate milestones.md
    candidates = [
        os.path.join(spec_root, "milestones.md"),
        os.path.join(spec_root, "runtime", "milestones.md"),
        os.path.join(project_path, "milestones.md"),
    ]

    milestones_path = None
    for c in candidates:
        if os.path.isfile(c):
            milestones_path = c
            break

    if milestones_path is None:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": spec_root,
            "detail": "milestones.md not found in project"
        })
        result = {
            "question": "p4.6",
            "answer": "no",
            "evidence": evidence
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    rel_path = os.path.relpath(milestones_path, project_path)

    try:
        with open(milestones_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": rel_path,
            "detail": "Could not read milestones.md"
        })
        result = {
            "question": "p4.6",
            "answer": "no",
            "evidence": evidence
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    non_blank_lines = [l for l in content.splitlines() if l.strip()]

    if len(non_blank_lines) == 0:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": rel_path,
            "detail": "milestones.md is empty"
        })
        result = {
            "question": "p4.6",
            "answer": "no",
            "evidence": evidence
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    evidence.append({
        "type": "file_timestamp",
        "path": rel_path,
        "detail": f"milestones.md has {len(non_blank_lines)} non-blank line(s)"
    })

    # Check for completion markers
    completion_keywords = [
        "complete", "done", "delivered", "merged", "closed",
        "finished", "achieved", "[x]"
    ]
    content_lower = content.lower()
    found_markers = [kw for kw in completion_keywords if kw in content_lower]

    if found_markers:
        evidence.append({
            "type": "file_timestamp",
            "path": rel_path,
            "detail": f"Completion markers found: {', '.join(found_markers)} -- OK"
        })
    else:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": rel_path,
            "detail": "No completion markers found in milestones.md (expected: complete, done, delivered, [x], etc.)"
        })

    result = {
        "question": "p4.6",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
