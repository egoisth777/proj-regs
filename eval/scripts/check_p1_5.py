#!/usr/bin/env python3
"""Check p1.5: Are all spec documents non-trivial (>50 lines or substantive content)?

Counts lines in proposal.md, behavior_spec.md, and test_spec.md for each
feature under runtime/openspec/changes/.  All spec files must exceed 50 lines.
"""

import os
import sys
import yaml


SPEC_FILES = ["proposal.md", "behavior_spec.md", "test_spec.md"]
MIN_LINES = 50


def count_lines(filepath):
    """Return the number of non-blank lines in a file, or -1 if missing."""
    if not os.path.isfile(filepath):
        return -1
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return sum(1 for line in f if line.strip())
    except OSError:
        return -1


def main():
    if len(sys.argv) < 2:
        print("Usage: check_p1_5.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    changes_dir = os.path.join(spec_root, "runtime", "openspec", "changes")
    evidence = []
    all_pass = True

    if not os.path.isdir(changes_dir):
        result = {
            "question": "p1.5",
            "answer": "no",
            "evidence": [{
                "type": "missing_directory",
                "path": changes_dir,
                "detail": "runtime/openspec/changes/ directory not found"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    feature_dirs = sorted(
        d for d in os.listdir(changes_dir)
        if os.path.isdir(os.path.join(changes_dir, d))
    )

    if not feature_dirs:
        result = {
            "question": "p1.5",
            "answer": "no",
            "evidence": [{
                "type": "missing_directory",
                "path": changes_dir,
                "detail": "No feature directories found under runtime/openspec/changes/"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    for feature in feature_dirs:
        feature_path = os.path.join(changes_dir, feature)
        for spec_name in SPEC_FILES:
            spec_path = os.path.join(feature_path, spec_name)
            line_count = count_lines(spec_path)
            rel_path = os.path.relpath(spec_path, project_path)

            if line_count < 0:
                evidence.append({
                    "type": "file_timestamp",
                    "path": rel_path,
                    "detail": f"Feature '{feature}': {spec_name} does not exist"
                })
                all_pass = False
            elif line_count < MIN_LINES:
                evidence.append({
                    "type": "file_timestamp",
                    "path": rel_path,
                    "detail": (
                        f"Feature '{feature}': {spec_name} has {line_count} "
                        f"non-blank lines (< {MIN_LINES}) -- TRIVIAL"
                    )
                })
                all_pass = False
            else:
                evidence.append({
                    "type": "file_timestamp",
                    "path": rel_path,
                    "detail": (
                        f"Feature '{feature}': {spec_name} has {line_count} "
                        f"non-blank lines (>= {MIN_LINES}) -- OK"
                    )
                })

    result = {
        "question": "p1.5",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
