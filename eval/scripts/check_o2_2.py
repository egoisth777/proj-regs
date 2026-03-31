#!/usr/bin/env python3
"""Check o2.2: Do tests cover both happy-path and error cases for each feature?

Checks test files for test function names that indicate both success/happy-path
testing and error/invalid/exception testing patterns.
"""

import os
import re
import sys
import yaml


def analyze_test_file(filepath):
    """Analyze a test file for happy-path and error-case test functions."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError:
        return [], []

    func_pattern = re.compile(
        r"^\s*(?:def|async\s+def)\s+(test_\w+)\s*\(", re.MULTILINE
    )
    all_tests = func_pattern.findall(content)

    happy_tests = []
    error_tests = []

    error_keywords = [
        "error", "invalid", "exception", "fail", "raise", "reject",
        "bad", "wrong", "missing", "empty", "null", "none", "negative",
        "unauthorized", "forbidden", "not_found", "conflict", "timeout",
        "malformed", "corrupt", "broken", "edge", "boundary"
    ]

    happy_keywords = [
        "success", "valid", "create", "get", "list", "update", "delete",
        "add", "save", "load", "parse", "format", "render", "process",
        "happy", "basic", "simple", "default", "normal", "standard"
    ]

    for test_name in all_tests:
        name_lower = test_name.lower()
        is_error = any(kw in name_lower for kw in error_keywords)
        is_happy = any(kw in name_lower for kw in happy_keywords)

        if is_error:
            error_tests.append(test_name)
        elif is_happy:
            happy_tests.append(test_name)
        else:
            # Default: tests not matching either keyword are likely happy-path
            happy_tests.append(test_name)

    return happy_tests, error_tests


def main():
    if len(sys.argv) < 2:
        print("Usage: check_o2_2.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    evidence = []
    all_pass = True

    # Find all test files
    test_dirs = [
        os.path.join(project_path, "artifacts", "tests"),
        os.path.join(project_path, "artifacts", "test"),
        os.path.join(project_path, "artifacts"),
        os.path.join(project_path, "tests"),
        os.path.join(project_path, "test"),
    ]

    test_files = []
    for td in test_dirs:
        if not os.path.isdir(td):
            continue
        for root, _dirs, files in os.walk(td):
            for f in files:
                if f.endswith(".py") and (f.startswith("test_") or f.endswith("_test.py")):
                    fp = os.path.join(root, f)
                    if fp not in test_files:
                        test_files.append(fp)

    if not test_files:
        result = {
            "question": "o2.2",
            "answer": "no",
            "evidence": [{
                "type": "file_timestamp",
                "path": "tests/",
                "detail": "No test files found"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    total_happy = 0
    total_error = 0
    files_with_both = 0
    files_missing_error = []

    for tf in test_files:
        happy, error = analyze_test_file(tf)
        total_happy += len(happy)
        total_error += len(error)
        rel_tf = os.path.relpath(tf, project_path)

        if happy and error:
            files_with_both += 1
        elif happy and not error:
            files_missing_error.append(rel_tf)

    evidence.append({
        "type": "file_timestamp",
        "path": "tests/",
        "detail": (
            f"Analyzed {len(test_files)} test file(s): "
            f"{total_happy} happy-path test(s), {total_error} error-case test(s)"
        )
    })

    if total_error == 0:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": "tests/",
            "detail": "No error-case tests found across any test file"
        })
    elif files_missing_error:
        # Some files lack error tests, but overall there are some
        if len(files_missing_error) > len(test_files) / 2:
            all_pass = False
            evidence.append({
                "type": "file_timestamp",
                "path": "tests/",
                "detail": (
                    f"{len(files_missing_error)} of {len(test_files)} test file(s) "
                    f"have no error-case tests: {', '.join(files_missing_error[:5])}"
                )
            })
        else:
            evidence.append({
                "type": "file_timestamp",
                "path": "tests/",
                "detail": (
                    f"{files_with_both} of {len(test_files)} test file(s) cover both happy and error paths"
                )
            })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": "tests/",
            "detail": f"All {len(test_files)} test file(s) cover both happy-path and error cases"
        })

    result = {
        "question": "o2.2",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
