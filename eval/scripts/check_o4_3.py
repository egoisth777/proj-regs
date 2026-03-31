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
    spec_keywords = extract_feature_keywords(changes_dir)

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

    # Check for modules that don't match any spec feature
    unspecced = []
    all_known = spec_features | spec_keywords

    for module in sorted(impl_modules):
        # Check various matching strategies
        matched = False

        # Direct match
        if module in spec_features:
            matched = True

        # Substring match: spec feature name contains module name or vice versa
        if not matched:
            for sf in spec_features:
                if module in sf or sf in module:
                    matched = True
                    break

        # Keyword match: module name appears in spec keywords
        if not matched:
            if module in spec_keywords:
                matched = True

        # Hyphen/underscore normalization
        if not matched:
            norm_module = module.replace("-", "_").replace("_", "")
            for sf in spec_features:
                norm_sf = sf.replace("-", "_").replace("_", "")
                if norm_module == norm_sf or norm_module in norm_sf or norm_sf in norm_module:
                    matched = True
                    break

        if not matched:
            unspecced.append(module)

    if unspecced:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": artifacts_dir,
            "detail": (
                f"Implemented modules without matching specs: "
                f"{', '.join(unspecced)}"
            )
        })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": artifacts_dir,
            "detail": "All implemented modules have corresponding spec features"
        })

    result = {
        "question": "o4.3",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
