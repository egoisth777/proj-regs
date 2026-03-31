#!/usr/bin/env python3
"""Check p3.4: Did the orchestrator detect and resolve blockers without human intervention?

Checks for blocker resolution evidence in status.md and active_sprint.md files.
Looks for keywords such as 'blocker', 'blocked', 'resolved', 'unblocked',
'retry', 'workaround', 'escalat'.
"""

import os
import re
import sys
import yaml


BLOCKER_KEYWORDS = [
    "blocker", "blocked", "unblocked", "resolved blocker",
    "workaround", "retry", "retried", "escalat", "obstacle",
    "impediment", "dependency issue", "conflict resolved"
]

RESOLUTION_KEYWORDS = [
    "resolved", "unblocked", "fixed", "workaround",
    "retried", "recovered", "completed after", "moved past"
]


def search_file_for_blockers(filepath):
    """Search a file for blocker mentions and resolution evidence."""
    if not os.path.isfile(filepath):
        return [], []

    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError:
        return [], []

    content_lower = content.lower()
    blocker_mentions = []
    resolution_mentions = []

    # Patterns that indicate NO blockers (should not count as blocker mentions)
    no_blocker_patterns = re.compile(
        r"(no\s+blockers?|zero\s+blockers?|blockers?:\s*none|no\s+blockers?\s+encountered)",
        re.IGNORECASE
    )

    for kw in BLOCKER_KEYWORDS:
        for m in re.finditer(re.escape(kw), content_lower):
            start = max(0, m.start() - 40)
            end = min(len(content), m.end() + 40)
            context = content[start:end].replace("\n", " ").strip()
            # Skip if the context indicates no blockers exist
            if no_blocker_patterns.search(context):
                continue
            blocker_mentions.append(context)

    for kw in RESOLUTION_KEYWORDS:
        for m in re.finditer(re.escape(kw), content_lower):
            start = max(0, m.start() - 40)
            end = min(len(content), m.end() + 40)
            context = content[start:end].replace("\n", " ").strip()
            resolution_mentions.append(context)

    return blocker_mentions, resolution_mentions


def main():
    if len(sys.argv) < 2:
        print("Usage: check_p3_4.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    evidence = []
    all_pass = True

    # Files to inspect for blocker evidence
    candidate_files = [
        os.path.join(spec_root, "runtime", "active_sprint.md"),
        os.path.join(spec_root, "runtime", "status.md"),
    ]

    # Also check feature-level status files
    changes_dir = os.path.join(spec_root, "runtime", "openspec", "changes")
    if os.path.isdir(changes_dir):
        for feature in sorted(os.listdir(changes_dir)):
            feature_path = os.path.join(changes_dir, feature)
            if os.path.isdir(feature_path):
                candidate_files.append(os.path.join(feature_path, "status.md"))

    total_blocker_mentions = 0
    total_resolution_mentions = 0
    checked_files = 0

    for fpath in candidate_files:
        if not os.path.isfile(fpath):
            continue
        checked_files += 1
        blockers, resolutions = search_file_for_blockers(fpath)
        rel_path = os.path.relpath(fpath, project_path)

        total_blocker_mentions += len(blockers)
        total_resolution_mentions += len(resolutions)

        if blockers:
            evidence.append({
                "type": "file_timestamp",
                "path": rel_path,
                "detail": (
                    f"Found {len(blockers)} blocker mention(s) and "
                    f"{len(resolutions)} resolution mention(s)"
                )
            })

    if checked_files == 0:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": spec_root,
            "detail": "No status or sprint files found to check for blocker resolution"
        })
    elif total_blocker_mentions == 0:
        # No blockers found -- could mean none occurred (acceptable)
        # or could mean orchestrator did not document them
        evidence.append({
            "type": "file_timestamp",
            "path": spec_root,
            "detail": (
                f"Checked {checked_files} file(s); no blocker mentions found. "
                "Either no blockers occurred or they were not documented."
            )
        })
        # If no blockers occurred, the check passes vacuously
    elif total_resolution_mentions == 0:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": spec_root,
            "detail": (
                f"Found {total_blocker_mentions} blocker mention(s) but "
                f"zero resolution evidence -- blockers may be unresolved"
            )
        })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": spec_root,
            "detail": (
                f"Found {total_blocker_mentions} blocker mention(s) with "
                f"{total_resolution_mentions} resolution mention(s) -- OK"
            )
        })

    result = {
        "question": "p3.4",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
