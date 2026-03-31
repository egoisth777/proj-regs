#!/usr/bin/env python3
"""Check o2.4: Do tests fail when the corresponding implementation is removed?

Heuristic check: verifies that test files import from source modules
(i.e., they are not self-contained) and that at least some tests exist.
If tests are self-contained with no imports from source, they would pass
even if implementation were removed.
"""

import ast
import os
import sys
import yaml


def get_source_module_names(project_path):
    """Get names of Python modules in the source directories."""
    src_dirs = [
        os.path.join(project_path, "artifacts", "src"),
        os.path.join(project_path, "artifacts"),
        os.path.join(project_path, "src"),
    ]

    modules = set()
    for sd in src_dirs:
        if not os.path.isdir(sd):
            continue
        for root, _dirs, files in os.walk(sd):
            if "__pycache__" in root:
                continue
            # Skip test directories
            basename = os.path.basename(root)
            if basename in ("tests", "test"):
                continue

            for f in files:
                if f.endswith(".py") and not f.startswith("test_"):
                    mod_name = f[:-3]  # strip .py
                    modules.add(mod_name)

            # Also add package names (directories with __init__.py)
            if "__init__.py" in files:
                modules.add(basename)

    return modules


def check_test_imports(filepath, source_modules):
    """Check if a test file imports from any source module."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except OSError:
        return False, []

    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return False, []

    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top_module = alias.name.split(".")[0]
                imported_modules.add(top_module)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top_module = node.module.split(".")[0]
                imported_modules.add(top_module)

    matching = imported_modules & source_modules
    return bool(matching), list(matching)


def count_test_functions(filepath):
    """Count test functions in a file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except OSError:
        return 0

    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return 0

    count = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_"):
                count += 1
    return count


def main():
    if len(sys.argv) < 2:
        print("Usage: check_o2_4.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    evidence = []
    all_pass = True

    source_modules = get_source_module_names(project_path)

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
        all_pass = False
        result = {
            "question": "o2.4",
            "answer": "no",
            "evidence": [{
                "type": "file_timestamp",
                "path": "tests/",
                "detail": "No test files found"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    if not source_modules:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": "src/",
            "detail": "No source modules found to check imports against"
        })
        result = {
            "question": "o2.4",
            "answer": "no",
            "evidence": evidence
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    total_tests = 0
    files_importing_source = 0
    files_self_contained = []

    for tf in test_files:
        rel_path = os.path.relpath(tf, project_path)
        test_count = count_test_functions(tf)
        total_tests += test_count

        imports_source, matched = check_test_imports(tf, source_modules)
        if imports_source:
            files_importing_source += 1
        elif test_count > 0:
            files_self_contained.append(rel_path)

    evidence.append({
        "type": "file_timestamp",
        "path": "tests/",
        "detail": (
            f"Analyzed {len(test_files)} test file(s) with {total_tests} test function(s); "
            f"source modules: {', '.join(sorted(source_modules)[:10])}"
        )
    })

    evidence.append({
        "type": "file_timestamp",
        "path": "tests/",
        "detail": (
            f"{files_importing_source}/{len(test_files)} test file(s) import from source modules"
        )
    })

    if files_self_contained:
        # If more than half of test files are self-contained, fail
        if len(files_self_contained) > len(test_files) / 2:
            all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": "tests/",
            "detail": (
                f"{len(files_self_contained)} test file(s) appear self-contained "
                f"(no source imports): {', '.join(files_self_contained[:5])}"
            )
        })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": "tests/",
            "detail": "All test files import from source modules -- tests depend on implementation"
        })

    result = {
        "question": "o2.4",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
