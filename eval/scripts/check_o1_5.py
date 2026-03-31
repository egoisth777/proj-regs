#!/usr/bin/env python3
"""Check o1.5: Does each behavior in the spec have a corresponding working feature?

Compares behaviors listed in behavior_spec.md against test function names
in test files.  Each behavior should have at least one test whose name
contains key terms from the behavior description.
"""

import os
import re
import sys
import yaml


def extract_behaviors(behavior_spec_path):
    """Extract behavior descriptions from behavior_spec.md."""
    if not os.path.isfile(behavior_spec_path):
        return []

    try:
        with open(behavior_spec_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError:
        return []

    behaviors = []

    # Given/When/Then or Scenario patterns
    gwt_pattern = re.compile(
        r"(?:Given|When|Then|Scenario)[:\s]+(.+)",
        re.IGNORECASE | re.MULTILINE
    )
    for m in gwt_pattern.finditer(content):
        behaviors.append(m.group(1).strip())

    # Numbered list items
    if not behaviors:
        numbered = re.compile(r"^\s*\d+[\.\)]\s+(.+)", re.MULTILINE)
        for m in numbered.finditer(content):
            behaviors.append(m.group(1).strip())

    # Bullet items as fallback
    if not behaviors:
        bullet = re.compile(r"^\s*[-*]\s+(.{10,})", re.MULTILINE)
        for m in bullet.finditer(content):
            behaviors.append(m.group(1).strip())

    return behaviors


def extract_keywords(text):
    """Extract meaningful keywords from a behavior description."""
    # Remove common stop words, keep significant terms
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "shall", "should", "may", "might", "must", "can", "could",
        "would", "to", "of", "in", "for", "on", "with", "at", "by",
        "from", "as", "into", "through", "during", "before", "after",
        "and", "but", "or", "nor", "not", "so", "yet", "if", "then",
        "that", "this", "it", "its", "when", "given", "they", "them",
        "their", "user", "system"
    }
    words = re.findall(r"[a-z]{3,}", text.lower())
    return [w for w in words if w not in stop_words]


def find_test_functions(project_path):
    """Find all test function names across test files."""
    test_dirs = [
        os.path.join(project_path, "artifacts", "tests"),
        os.path.join(project_path, "artifacts", "test"),
        os.path.join(project_path, "artifacts"),
        os.path.join(project_path, "tests"),
        os.path.join(project_path, "test"),
    ]

    test_names = []
    func_pattern = re.compile(r"^\s*(?:def|async\s+def)\s+(test_\w+)\s*\(", re.MULTILINE)

    for td in test_dirs:
        if not os.path.isdir(td):
            continue
        for root, _dirs, files in os.walk(td):
            for f in files:
                if f.endswith(".py") and (f.startswith("test_") or f.endswith("_test.py")):
                    fpath = os.path.join(root, f)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
                            content = fh.read()
                        test_names.extend(func_pattern.findall(content))
                    except OSError:
                        pass

    return list(set(test_names))


def main():
    if len(sys.argv) < 2:
        print("Usage: check_o1_5.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    evidence = []
    all_pass = True

    changes_dir = os.path.join(spec_root, "runtime", "openspec", "changes")

    if not os.path.isdir(changes_dir):
        result = {
            "question": "o1.5",
            "answer": "no",
            "evidence": [{
                "type": "missing_directory",
                "path": changes_dir,
                "detail": "runtime/openspec/changes/ directory not found"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    test_names = find_test_functions(project_path)
    test_names_lower = [t.lower() for t in test_names]

    all_behaviors = []
    feature_dirs = sorted(
        d for d in os.listdir(changes_dir)
        if os.path.isdir(os.path.join(changes_dir, d))
    )

    for feature in feature_dirs:
        spec_path = os.path.join(changes_dir, feature, "behavior_spec.md")
        behaviors = extract_behaviors(spec_path)
        for b in behaviors:
            all_behaviors.append((feature, b))

    if not all_behaviors:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": changes_dir,
            "detail": "No behaviors found in behavior_spec files"
        })
    elif not test_names:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": "tests/",
            "detail": "No test functions found"
        })
    else:
        covered = 0
        uncovered = []

        for feature, behavior in all_behaviors:
            keywords = extract_keywords(behavior)
            if not keywords:
                covered += 1
                continue

            # Check if any test name contains at least 1 keyword
            matched = False
            for test_lower in test_names_lower:
                if any(kw in test_lower for kw in keywords):
                    matched = True
                    break

            if matched:
                covered += 1
            else:
                uncovered.append(f"{feature}: {behavior[:60]}")

        evidence.append({
            "type": "file_timestamp",
            "path": "behavior_spec",
            "detail": (
                f"{covered}/{len(all_behaviors)} behavior(s) have matching test(s); "
                f"{len(test_names)} total test function(s)"
            )
        })

        if uncovered:
            coverage_ratio = covered / len(all_behaviors) if all_behaviors else 0
            if coverage_ratio < 0.7:
                all_pass = False
            shown = uncovered[:5]
            evidence.append({
                "type": "file_timestamp",
                "path": "behavior_spec",
                "detail": (
                    f"Behaviors without matching tests: {'; '.join(shown)}"
                    + (f" ... and {len(uncovered) - 5} more" if len(uncovered) > 5 else "")
                )
            })
        else:
            evidence.append({
                "type": "file_timestamp",
                "path": "behavior_spec",
                "detail": "All behaviors have at least one matching test -- OK"
            })

    result = {
        "question": "o1.5",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
