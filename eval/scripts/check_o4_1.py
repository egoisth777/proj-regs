#!/usr/bin/env python3
"""Check o4.1: Does every behavior in behavior_spec have at least one test?

Parses behavior_spec.md for behaviors (Given/When/Then patterns or numbered
behaviors). Parses test files for test functions. Checks that the count of
test functions >= count of behaviors.
"""

import os
import re
import sys
import yaml


def count_behaviors(behavior_spec_path):
    """Count behaviors defined in a behavior_spec.md file.

    Looks for:
    - Given/When/Then blocks (each Given...When...Then is one behavior)
    - Numbered behavior items (e.g., "1.", "2.", etc. under Behavior headers)
    - Scenario: or Behavior: labels
    """
    if not os.path.isfile(behavior_spec_path):
        return 0, []

    with open(behavior_spec_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    behaviors = []

    # Count Given/When/Then blocks
    gwt_pattern = re.compile(
        r"(?:^|\n)\s*\*?\*?\s*(?:Given|Scenario)[:\s]",
        re.IGNORECASE
    )
    gwt_matches = gwt_pattern.findall(content)
    for m in gwt_matches:
        behaviors.append(m.strip())

    # Count numbered behaviors under behavior-like headings if GWT didn't find any
    if not behaviors:
        # Look for numbered list items that describe behaviors
        numbered_pattern = re.compile(r"^\s*\d+[\.\)]\s+.+", re.MULTILINE)
        numbered_matches = numbered_pattern.findall(content)
        for m in numbered_matches:
            behaviors.append(m.strip())

    # Also look for "## Behavior" or "### Behavior" section headers as behavior markers
    if not behaviors:
        header_pattern = re.compile(r"^#+\s+.+", re.MULTILINE)
        headers = header_pattern.findall(content)
        # Filter to only behavior-describing headers (not metadata headers)
        for h in headers:
            h_lower = h.lower()
            if any(kw in h_lower for kw in ["behavior", "feature", "scenario", "requirement", "shall", "must"]):
                behaviors.append(h.strip())

    # Fallback: count bullet points as potential behaviors
    if not behaviors:
        bullet_pattern = re.compile(r"^\s*[-*]\s+.{10,}", re.MULTILINE)
        bullet_matches = bullet_pattern.findall(content)
        behaviors = [m.strip() for m in bullet_matches]

    return len(behaviors), behaviors


def count_test_functions(test_dir):
    """Count test functions across all test files in a directory."""
    test_count = 0
    test_names = []

    if not os.path.isdir(test_dir):
        return 0, []

    for root, _dirs, files in os.walk(test_dir):
        for f in files:
            if not f.endswith(".py"):
                continue
            if not (f.startswith("test_") or f.endswith("_test.py")):
                continue

            filepath = os.path.join(root, f)
            with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read()

            # Count def test_*( patterns
            func_pattern = re.compile(r"^\s*(?:def|async\s+def)\s+(test_\w+)\s*\(", re.MULTILINE)
            matches = func_pattern.findall(content)
            test_count += len(matches)
            test_names.extend(matches)

            # Count test methods in classes (class Test*: ... def test_*)
            method_pattern = re.compile(r"^\s+(?:def|async\s+def)\s+(test_\w+)\s*\(", re.MULTILINE)
            # Already covered by the above pattern since we allow leading whitespace

    return test_count, test_names


def main():
    if len(sys.argv) < 2:
        print("Usage: check_o4_1.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    # Resolve spec root: reg_root/ssot/ if it exists, else reg_root
    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    changes_dir = os.path.join(spec_root, "runtime", "openspec", "changes")

    evidence = []
    all_pass = True

    # Count behaviors from all behavior_spec.md files
    total_behaviors = 0
    behavior_details = []

    if os.path.isdir(changes_dir):
        feature_dirs = [
            d for d in os.listdir(changes_dir)
            if os.path.isdir(os.path.join(changes_dir, d))
        ]

        for feature in sorted(feature_dirs):
            spec_path = os.path.join(changes_dir, feature, "behavior_spec.md")
            count, items = count_behaviors(spec_path)
            total_behaviors += count
            if os.path.isfile(spec_path):
                behavior_details.append(f"'{feature}': {count} behavior(s)")
    else:
        result = {
            "question": "o4.1",
            "answer": "no",
            "evidence": [{
                "type": "missing_directory",
                "path": changes_dir,
                "detail": "runtime/openspec/changes/ directory not found"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    # Count test functions
    test_dirs = [
        os.path.join(project_path, "artifacts", "tests"),
        os.path.join(project_path, "artifacts", "test"),
        os.path.join(project_path, "artifacts"),
        os.path.join(project_path, "tests"),
    ]

    total_tests = 0
    all_test_names = []
    for td in test_dirs:
        count, names = count_test_functions(td)
        total_tests += count
        all_test_names.extend(names)
    # Deduplicate in case of overlapping directories
    all_test_names = list(set(all_test_names))
    total_tests = len(all_test_names)

    evidence.append({
        "type": "file_timestamp",
        "path": changes_dir,
        "detail": f"Found {total_behaviors} behavior(s) across specs: {'; '.join(behavior_details)}"
    })

    evidence.append({
        "type": "file_timestamp",
        "path": "artifacts/",
        "detail": f"Found {total_tests} unique test function(s)"
    })

    if total_behaviors == 0:
        evidence.append({
            "type": "file_timestamp",
            "path": changes_dir,
            "detail": "No behaviors found in behavior_spec files; cannot verify coverage"
        })
        all_pass = False
    elif total_tests >= total_behaviors:
        evidence.append({
            "type": "file_timestamp",
            "path": "artifacts/",
            "detail": f"Test count ({total_tests}) >= behavior count ({total_behaviors}) -- OK"
        })
    else:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": "artifacts/",
            "detail": f"Test count ({total_tests}) < behavior count ({total_behaviors}) -- INSUFFICIENT COVERAGE"
        })

    result = {
        "question": "o4.1",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
