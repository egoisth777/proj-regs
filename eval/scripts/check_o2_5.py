#!/usr/bin/env python3
"""Check o2.5: Do test names clearly describe the behavior being tested?

Checks that test function names are longer than 10 characters and contain
descriptive words (not just 'test_1', 'test_a', etc.).
"""

import os
import re
import sys
import yaml


MIN_NAME_LENGTH = 10

# Short/non-descriptive patterns
NON_DESCRIPTIVE_PATTERNS = [
    re.compile(r"^test_?\d+$"),           # test_1, test2
    re.compile(r"^test_?[a-z]$"),         # test_a, testa
    re.compile(r"^test_?it$"),            # test_it
    re.compile(r"^test_?this$"),          # test_this
    re.compile(r"^test_?something$"),     # test_something
    re.compile(r"^test_?basic$"),         # test_basic
    re.compile(r"^test_?foo$"),           # test_foo
    re.compile(r"^test_?bar$"),           # test_bar
    re.compile(r"^test_?example$"),       # test_example
    re.compile(r"^test_?sample$"),        # test_sample
    re.compile(r"^test_?temp$"),          # test_temp
    re.compile(r"^test_?main$"),          # test_main
    re.compile(r"^test_?run$"),           # test_run
]


def extract_test_names(filepath):
    """Extract test function names from a Python test file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError:
        return []

    func_pattern = re.compile(
        r"^\s*(?:def|async\s+def)\s+(test_\w+)\s*\(",
        re.MULTILINE
    )
    return func_pattern.findall(content)


def is_descriptive(name):
    """Check if a test name is descriptive enough."""
    if len(name) < MIN_NAME_LENGTH:
        return False, f"too short ({len(name)} chars)"

    name_lower = name.lower()
    for pattern in NON_DESCRIPTIVE_PATTERNS:
        if pattern.match(name_lower):
            return False, "non-descriptive pattern"

    # Check it has at least 2 meaningful words (beyond 'test')
    parts = name.lower().split("_")
    meaningful_parts = [p for p in parts if p and p != "test" and len(p) > 1]
    if len(meaningful_parts) < 2:
        return False, f"only {len(meaningful_parts)} meaningful word(s)"

    return True, "OK"


def main():
    if len(sys.argv) < 2:
        print("Usage: check_o2_5.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    evidence = []
    all_pass = True

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
            "question": "o2.5",
            "answer": "no",
            "evidence": [{
                "type": "file_timestamp",
                "path": "tests/",
                "detail": "No test files found"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    total_tests = 0
    descriptive_count = 0
    poor_names = []

    for tf in test_files:
        rel_path = os.path.relpath(tf, project_path)
        names = extract_test_names(tf)
        total_tests += len(names)

        for name in names:
            ok, reason = is_descriptive(name)
            if ok:
                descriptive_count += 1
            else:
                poor_names.append(f"{rel_path}: {name} ({reason})")

    if total_tests == 0:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": "tests/",
            "detail": "No test functions found"
        })
    else:
        ratio = descriptive_count / total_tests
        evidence.append({
            "type": "file_timestamp",
            "path": "tests/",
            "detail": (
                f"{descriptive_count}/{total_tests} test name(s) are descriptive "
                f"({ratio:.0%})"
            )
        })

        if poor_names:
            if ratio < 0.8:
                all_pass = False
            shown = poor_names[:10]
            evidence.append({
                "type": "file_timestamp",
                "path": "tests/",
                "detail": (
                    f"Non-descriptive test names: {'; '.join(shown)}"
                    + (f" ... and {len(poor_names) - 10} more" if len(poor_names) > 10 else "")
                )
            })
        else:
            evidence.append({
                "type": "file_timestamp",
                "path": "tests/",
                "detail": "All test names are descriptive -- OK"
            })

    result = {
        "question": "o2.5",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
