#!/usr/bin/env python3
"""Check p1.6: Did every feature complete the full cascade (no skipped stages)?

Verifies that each feature folder has all 5 files: proposal.md,
behavior_spec.md, test_spec.md, tasks.md, status.md — and all are non-empty.
"""

import os
import sys
import yaml


REQUIRED_FILES = [
    "proposal.md",
    "behavior_spec.md",
    "test_spec.md",
    "tasks.md",
    "status.md",
]


def main():
    if len(sys.argv) < 2:
        print("Usage: check_p1_6.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])
    changes_dir = os.path.join(project_path, "runtime", "openspec", "changes")

    evidence = []
    all_pass = True

    if not os.path.isdir(changes_dir):
        result = {
            "question": "p1.6",
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
            "question": "p1.6",
            "answer": "no",
            "evidence": [{
                "type": "missing_directory",
                "path": changes_dir,
                "detail": "No feature directories found under runtime/openspec/changes/"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    for feature in sorted(feature_dirs):
        feature_path = os.path.join(changes_dir, feature)
        missing = []
        empty = []

        for req_file in REQUIRED_FILES:
            fp = os.path.join(feature_path, req_file)
            if not os.path.isfile(fp):
                missing.append(req_file)
            elif os.path.getsize(fp) == 0:
                empty.append(req_file)

        if missing or empty:
            all_pass = False
            detail_parts = []
            if missing:
                detail_parts.append(f"missing: {', '.join(missing)}")
            if empty:
                detail_parts.append(f"empty: {', '.join(empty)}")
            evidence.append({
                "type": "file_timestamp",
                "path": feature_path,
                "detail": f"Feature '{feature}': {'; '.join(detail_parts)}"
            })
        else:
            evidence.append({
                "type": "file_timestamp",
                "path": feature_path,
                "detail": f"Feature '{feature}': All 5 cascade files present and non-empty"
            })

    result = {
        "question": "p1.6",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
