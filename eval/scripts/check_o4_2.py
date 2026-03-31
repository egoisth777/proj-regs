#!/usr/bin/env python3
"""Check o4.2: Does every test in test_spec have a corresponding test file?

Parses test_spec.md for test descriptions/names and compares them against
actual test functions found in test files.
"""

import os
import re
import sys
import yaml


def extract_spec_tests(test_spec_path):
    """Extract test names/descriptions from a test_spec.md file."""
    if not os.path.isfile(test_spec_path):
        return []

    with open(test_spec_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    spec_tests = []

    # Pattern 1: test function names in backticks: `test_something`
    backtick_pattern = re.compile(r"`(test_\w+)`")
    for match in backtick_pattern.finditer(content):
        spec_tests.append(match.group(1))

    # Pattern 2: test descriptions like "TC-001:" or "Test Case 1:"
    tc_pattern = re.compile(r"(?:TC|Test\s*Case)[-\s]*\d+[:\s]+(.+)", re.IGNORECASE)
    for match in tc_pattern.finditer(content):
        spec_tests.append(match.group(1).strip())

    # Pattern 3: Numbered or bulleted items that describe tests
    if not spec_tests:
        item_pattern = re.compile(r"^\s*(?:\d+[\.\)]|-|\*)\s+(.{15,})", re.MULTILINE)
        for match in item_pattern.finditer(content):
            text = match.group(1).strip()
            # Filter to items that look like test descriptions
            if any(kw in text.lower() for kw in [
                "test", "verify", "check", "assert", "ensure", "validate",
                "should", "must", "expect"
            ]):
                spec_tests.append(text)

    # Pattern 4: Markdown headers that describe test scenarios
    if not spec_tests:
        header_pattern = re.compile(r"^#+\s+(.+test.+|.+scenario.+|.+case.+)", re.IGNORECASE | re.MULTILINE)
        for match in header_pattern.finditer(content):
            spec_tests.append(match.group(1).strip())

    return spec_tests


def collect_actual_tests(project_path):
    """Collect all actual test function names from test files."""
    test_names = set()
    test_dirs = [
        os.path.join(project_path, "artifacts", "tests"),
        os.path.join(project_path, "artifacts", "test"),
        os.path.join(project_path, "artifacts"),
        os.path.join(project_path, "tests"),
    ]

    for td in test_dirs:
        if not os.path.isdir(td):
            continue
        for root, _dirs, files in os.walk(td):
            for f in files:
                if not f.endswith(".py"):
                    continue
                if not (f.startswith("test_") or f.endswith("_test.py")):
                    continue
                fp = os.path.join(root, f)
                try:
                    with open(fp, "r", encoding="utf-8", errors="replace") as fh:
                        content = fh.read()
                    func_pattern = re.compile(
                        r"^\s*(?:def|async\s+def)\s+(test_\w+)\s*\(", re.MULTILINE
                    )
                    for match in func_pattern.finditer(content):
                        test_names.add(match.group(1))
                except OSError:
                    pass

    return test_names


def normalize_test_name(text):
    """Normalize a test description for fuzzy matching."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s_]", "", text)
    text = re.sub(r"\s+", "_", text).strip("_")
    return text


def main():
    if len(sys.argv) < 2:
        print("Usage: check_o4_2.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    changes_dir = os.path.join(spec_root, "runtime", "openspec", "changes")

    evidence = []
    all_pass = True

    if not os.path.isdir(changes_dir):
        result = {
            "question": "o4.2",
            "answer": "no",
            "evidence": [{
                "type": "missing_directory",
                "path": changes_dir,
                "detail": "runtime/openspec/changes/ directory not found"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    # Collect all actual tests
    actual_tests = collect_actual_tests(project_path)
    actual_normalized = {normalize_test_name(t): t for t in actual_tests}

    # Check each feature's test_spec
    feature_dirs = [
        d for d in os.listdir(changes_dir)
        if os.path.isdir(os.path.join(changes_dir, d))
    ]

    total_spec_tests = 0
    total_matched = 0
    total_unmatched = 0

    for feature in sorted(feature_dirs):
        test_spec_path = os.path.join(changes_dir, feature, "test_spec.md")
        spec_tests = extract_spec_tests(test_spec_path)

        if not os.path.isfile(test_spec_path):
            evidence.append({
                "type": "file_timestamp",
                "path": test_spec_path,
                "detail": f"Feature '{feature}': test_spec.md not found"
            })
            continue

        if not spec_tests:
            evidence.append({
                "type": "file_timestamp",
                "path": test_spec_path,
                "detail": f"Feature '{feature}': No test entries parsed from test_spec.md"
            })
            continue

        total_spec_tests += len(spec_tests)
        matched = 0
        unmatched = []

        for spec_test in spec_tests:
            normalized = normalize_test_name(spec_test)

            # Try exact match
            if spec_test in actual_tests:
                matched += 1
                continue

            # Try normalized match
            if normalized in actual_normalized:
                matched += 1
                continue

            # Try substring match: any actual test name contains key words
            spec_words = set(normalized.split("_")) - {"test", "the", "a", "an", "is", "should", "when", "then"}
            found = False
            for actual_norm in actual_normalized:
                actual_words = set(actual_norm.split("_"))
                # If most spec words appear in an actual test name
                if spec_words and len(spec_words & actual_words) >= len(spec_words) * 0.5:
                    found = True
                    break

            if found:
                matched += 1
            else:
                unmatched.append(spec_test[:80])

        total_matched += matched
        total_unmatched += len(unmatched)

        if unmatched:
            evidence.append({
                "type": "file_timestamp",
                "path": test_spec_path,
                "detail": (
                    f"Feature '{feature}': {matched}/{len(spec_tests)} spec tests matched; "
                    f"unmatched: {'; '.join(unmatched[:3])}"
                )
            })
        else:
            evidence.append({
                "type": "file_timestamp",
                "path": test_spec_path,
                "detail": f"Feature '{feature}': All {len(spec_tests)} spec test(s) have matching implementations"
            })

    if total_spec_tests == 0:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": changes_dir,
            "detail": "No test entries found in any test_spec.md"
        })
    elif total_unmatched > 0:
        # Fail if more than 30% unmatched
        if total_unmatched / total_spec_tests > 0.3:
            all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": "tests/",
            "detail": (
                f"Overall: {total_matched}/{total_spec_tests} spec tests matched to implementations "
                f"({total_unmatched} unmatched)"
            )
        })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": "tests/",
            "detail": f"All {total_spec_tests} spec test(s) have corresponding test implementations"
        })

    evidence.append({
        "type": "file_timestamp",
        "path": "tests/",
        "detail": f"Found {len(actual_tests)} actual test function(s) in project"
    })

    result = {
        "question": "o4.2",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
