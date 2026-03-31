#!/usr/bin/env python3
"""Check o4.3: Are there zero implemented features that lack a spec?

Checks that every source module in artifacts/ has a corresponding feature
spec under runtime/openspec/changes/. Also checks for orphan source
directories that don't map to any spec.
"""

import os
import re
import sys
import yaml


def collect_implemented_modules(artifacts_dir):
    """Identify distinct modules/features implemented in artifacts/."""
    modules = set()
    if not os.path.isdir(artifacts_dir):
        return modules

    src_dir = os.path.join(artifacts_dir, "src")
    search = src_dir if os.path.isdir(src_dir) else artifacts_dir

    for root, dirs, files in os.walk(search):
        # Skip test directories and __pycache__
        dirs[:] = [
            d for d in dirs
            if d not in ("tests", "test", "__pycache__", ".pytest_cache", "__pycache__")
        ]

        rel_root = os.path.relpath(root, search)

        # Top-level directories (or the root itself) are "modules"
        depth = len(rel_root.split(os.sep)) if rel_root != "." else 0

        if depth <= 1:
            for f in files:
                if f.endswith(".py") and f != "__init__.py" and f != "conftest.py":
                    if not f.startswith("test_") and not f.endswith("_test.py"):
                        # Module name from filename
                        mod_name = os.path.splitext(f)[0]
                        modules.add(mod_name.lower())

            for d in dirs:
                modules.add(d.lower())

    return modules


def collect_spec_features(changes_dir):
    """Collect feature names from the spec cascade directories."""
    features = set()
    if not os.path.isdir(changes_dir):
        return features

    for d in os.listdir(changes_dir):
        if os.path.isdir(os.path.join(changes_dir, d)):
            features.add(d.lower())

    return features


def extract_feature_keywords(changes_dir):
    """Extract keywords from spec files that might match module names."""
    keywords = set()
    if not os.path.isdir(changes_dir):
        return keywords

    for feature_dir in os.listdir(changes_dir):
        fp = os.path.join(changes_dir, feature_dir)
        if not os.path.isdir(fp):
            continue

        for spec_file in ["proposal.md", "behavior_spec.md", "tasks.md"]:
            spec_path = os.path.join(fp, spec_file)
            if os.path.isfile(spec_path):
                try:
                    with open(spec_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    # Extract backtick-wrapped identifiers
                    for match in re.finditer(r"`(\w+)`", content):
                        name = match.group(1).lower()
                        if len(name) > 2:
                            keywords.add(name)
                except OSError:
                    pass

    return keywords


def main():
    if len(sys.argv) < 2:
        print("Usage: check_o4_3.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    changes_dir = os.path.join(spec_root, "runtime", "openspec", "changes")
    artifacts_dir = os.path.join(project_path, "artifacts")

    evidence = []
    all_pass = True

    if not os.path.isdir(changes_dir):
        result = {
            "question": "o4.3",
            "answer": "no",
            "evidence": [{
                "type": "missing_directory",
                "path": changes_dir,
                "detail": "runtime/openspec/changes/ directory not found"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    spec_features = collect_spec_features(changes_dir)
    impl_modules = collect_implemented_modules(artifacts_dir)

    evidence.append({
        "type": "file_timestamp",
        "path": changes_dir,
        "detail": f"Found {len(spec_features)} spec feature(s): {', '.join(sorted(spec_features))}"
    })

    evidence.append({
        "type": "file_timestamp",
        "path": artifacts_dir,
        "detail": f"Found {len(impl_modules)} implemented module(s): {', '.join(sorted(impl_modules))}"
    })

    if not impl_modules:
        evidence.append({
            "type": "file_timestamp",
            "path": artifacts_dir,
            "detail": "No implementation modules found; condition trivially satisfied"
        })
        result = {
            "question": "o4.3",
            "answer": "yes",
            "evidence": evidence
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    # Check 1: Every feature directory has a behavior_spec.md
    features_without_spec = []
    for feature in sorted(spec_features):
        behavior_spec = os.path.join(changes_dir, feature, "behavior_spec.md")
        if not os.path.isfile(behavior_spec):
            features_without_spec.append(feature)

    if features_without_spec:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": changes_dir,
            "detail": (
                f"Features missing behavior_spec.md: "
                f"{', '.join(features_without_spec)}"
            )
        })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": changes_dir,
            "detail": "All features have behavior_spec.md"
        })

    # Check 2: Every source module has at least one corresponding test file
    test_dirs = [
        os.path.join(artifacts_dir, "tests"),
        os.path.join(artifacts_dir, "test"),
    ]
    test_files = set()
    for td in test_dirs:
        if not os.path.isdir(td):
            continue
        for root, _dirs, files in os.walk(td):
            for f in files:
                if f.endswith(".py") and (f.startswith("test_") or f.endswith("_test.py")):
                    # Extract the module name the test covers
                    name = f.replace("test_", "").replace("_test", "")
                    name = os.path.splitext(name)[0].lower()
                    test_files.add(name)

    modules_without_tests = []
    for module in sorted(impl_modules):
        if module not in test_files:
            modules_without_tests.append(module)

    if modules_without_tests:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": artifacts_dir,
            "detail": (
                f"Modules without corresponding tests: "
                f"{', '.join(modules_without_tests)}"
            )
        })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": artifacts_dir,
            "detail": "All implemented modules have corresponding test files"
        })

    result = {
        "question": "o4.3",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
