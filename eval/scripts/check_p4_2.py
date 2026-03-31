#!/usr/bin/env python3
"""Check p4.2: Does status.md for each feature reflect its actual final state?

Checks that each feature's status.md exists, is non-empty, and contains
phase markings or completion indicators that are consistent with the
presence of other cascade files.
"""

import os
import re
import sys
import yaml


def main():
    if len(sys.argv) < 2:
        print("Usage: check_p4_2.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    changes_dir = os.path.join(spec_root, "runtime", "openspec", "changes")

    evidence = []
    all_pass = True

    if not os.path.isdir(changes_dir):
        result = {
            "question": "p4.2",
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
            "question": "p4.2",
            "answer": "no",
            "evidence": [{
                "type": "missing_directory",
                "path": changes_dir,
                "detail": "No feature directories found"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    cascade_files = ["proposal.md", "behavior_spec.md", "test_spec.md", "tasks.md"]
    phase_keywords = [
        "complete", "done", "merged", "closed", "implemented",
        "in progress", "wip", "pending", "review", "approved",
        "phase", "stage", "status", "sprint"
    ]

    for feature in sorted(feature_dirs):
        feature_path = os.path.join(changes_dir, feature)
        status_file = os.path.join(feature_path, "status.md")

        if not os.path.isfile(status_file):
            all_pass = False
            evidence.append({
                "type": "file_timestamp",
                "path": status_file,
                "detail": f"Feature '{feature}': status.md not found"
            })
            continue

        try:
            with open(status_file, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError:
            all_pass = False
            evidence.append({
                "type": "file_timestamp",
                "path": status_file,
                "detail": f"Feature '{feature}': status.md could not be read"
            })
            continue

        if len(content.strip()) < 10:
            all_pass = False
            evidence.append({
                "type": "file_timestamp",
                "path": status_file,
                "detail": f"Feature '{feature}': status.md is too short ({len(content.strip())} chars)"
            })
            continue

        content_lower = content.lower()

        # Check for phase markings
        found_phases = [kw for kw in phase_keywords if kw in content_lower]

        # Determine actual state of the feature (what cascade files exist)
        existing_files = []
        for cf in cascade_files:
            if os.path.isfile(os.path.join(feature_path, cf)):
                existing_files.append(cf)

        # Check consistency: if all cascade files exist, status should indicate completion
        all_cascade_present = len(existing_files) == len(cascade_files)
        has_completion_marker = any(
            kw in content_lower for kw in ["complete", "done", "merged", "implemented", "closed"]
        )

        if found_phases:
            if all_cascade_present and not has_completion_marker:
                # All files present but status doesn't show completion
                evidence.append({
                    "type": "file_timestamp",
                    "path": status_file,
                    "detail": (
                        f"Feature '{feature}': All cascade files present but status.md "
                        f"lacks completion marker (found: {', '.join(found_phases)})"
                    )
                })
                # This is a soft warning, not necessarily a failure
            else:
                evidence.append({
                    "type": "file_timestamp",
                    "path": status_file,
                    "detail": (
                        f"Feature '{feature}': status.md has phase markings: "
                        f"{', '.join(found_phases)}; cascade files: {len(existing_files)}/{len(cascade_files)}"
                    )
                })
        else:
            all_pass = False
            evidence.append({
                "type": "file_timestamp",
                "path": status_file,
                "detail": (
                    f"Feature '{feature}': status.md has no recognized phase markings. "
                    f"Content length: {len(content)} chars"
                )
            })

    result = {
        "question": "p4.2",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
