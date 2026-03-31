#!/usr/bin/env python3
"""Check p4.4: Were implementation records created for all completed features?

Checks for IR_INDEX.md entries or an implementation/ directory that
documents completed features.
"""

import os
import re
import sys
import yaml


def main():
    if len(sys.argv) < 2:
        print("Usage: check_p4_4.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    evidence = []
    all_pass = True

    # Identify completed features from openspec/changes/
    changes_dir = os.path.join(spec_root, "runtime", "openspec", "changes")
    completed_features = []

    if os.path.isdir(changes_dir):
        for feature in sorted(os.listdir(changes_dir)):
            feature_path = os.path.join(changes_dir, feature)
            if not os.path.isdir(feature_path):
                continue
            # A feature is considered completed if it has a status.md
            # with completion markers or has all spec cascade files
            status_file = os.path.join(feature_path, "status.md")
            if os.path.isfile(status_file):
                try:
                    with open(status_file, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read().lower()
                    if any(kw in content for kw in ["complete", "done", "merged", "delivered", "closed"]):
                        completed_features.append(feature)
                        continue
                except OSError:
                    pass
            # Fallback: if proposal + behavior_spec + test_spec all exist
            has_all = all(
                os.path.isfile(os.path.join(feature_path, s))
                for s in ["proposal.md", "behavior_spec.md", "test_spec.md"]
            )
            if has_all:
                completed_features.append(feature)

    if not completed_features:
        evidence.append({
            "type": "file_timestamp",
            "path": spec_root,
            "detail": "No completed features found to check for implementation records"
        })
        all_pass = False
        result = {
            "question": "p4.4",
            "answer": "no",
            "evidence": evidence
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    # Check for implementation records
    ir_index = os.path.join(spec_root, "IR_INDEX.md")
    impl_dir = os.path.join(spec_root, "implementation")
    records_dir = os.path.join(spec_root, "runtime", "implementation")

    ir_index_features = set()
    if os.path.isfile(ir_index):
        try:
            with open(ir_index, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            for feature in completed_features:
                if feature.lower() in content.lower():
                    ir_index_features.add(feature)
        except OSError:
            pass

    impl_dir_features = set()
    for d in [impl_dir, records_dir]:
        if os.path.isdir(d):
            for item in os.listdir(d):
                item_lower = item.lower().replace("-", "_").replace(" ", "_")
                for feature in completed_features:
                    feat_lower = feature.lower().replace("-", "_").replace(" ", "_")
                    if feat_lower in item_lower or item_lower in feat_lower:
                        impl_dir_features.add(feature)

    # Also check for implementation records inside each feature dir
    feature_level_records = set()
    for feature in completed_features:
        feature_path = os.path.join(changes_dir, feature)
        for fname in os.listdir(feature_path):
            if "implementation" in fname.lower() or "ir" in fname.lower().split("_"):
                feature_level_records.add(feature)
                break

    documented = ir_index_features | impl_dir_features | feature_level_records
    missing = [f for f in completed_features if f not in documented]

    evidence.append({
        "type": "file_timestamp",
        "path": spec_root,
        "detail": (
            f"{len(completed_features)} completed feature(s): "
            f"{', '.join(completed_features)}"
        )
    })

    if ir_index_features:
        evidence.append({
            "type": "file_timestamp",
            "path": os.path.relpath(ir_index, project_path) if os.path.isfile(ir_index) else "IR_INDEX.md",
            "detail": f"IR_INDEX.md references: {', '.join(sorted(ir_index_features))}"
        })

    if impl_dir_features:
        evidence.append({
            "type": "file_timestamp",
            "path": "implementation/",
            "detail": f"Implementation directory records: {', '.join(sorted(impl_dir_features))}"
        })

    if missing:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": spec_root,
            "detail": (
                f"{len(missing)} feature(s) missing implementation records: "
                f"{', '.join(missing)}"
            )
        })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": spec_root,
            "detail": "All completed features have implementation records -- OK"
        })

    result = {
        "question": "p4.4",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
