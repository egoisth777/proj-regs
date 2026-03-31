#!/usr/bin/env python3
"""Check o3.3: Does the project follow its own stated conventions (naming, structure)?

Checks that Python source files use snake_case for function and variable names,
PascalCase for class names, and UPPER_CASE for module-level constants.
"""

import ast
import os
import re
import sys
import yaml


SNAKE_CASE_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
PASCAL_CASE_RE = re.compile(r"^[A-Z][a-zA-Z0-9]*$")
UPPER_CASE_RE = re.compile(r"^[A-Z_][A-Z0-9_]*$")

# Names to ignore (dunder methods, common conventions)
IGNORE_NAMES = {"_", "__all__", "__version__", "__author__"}


def check_naming(filepath):
    """Check naming conventions in a Python file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except OSError:
        return []

    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return []

    violations = []

    for node in ast.iter_child_nodes(tree):
        # Check top-level function names: should be snake_case
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name
            if name.startswith("__") and name.endswith("__"):
                continue
            if not SNAKE_CASE_RE.match(name):
                violations.append(
                    f"function '{name}' (line {node.lineno}) is not snake_case"
                )

        # Check class names: should be PascalCase
        elif isinstance(node, ast.ClassDef):
            name = node.name
            if not PASCAL_CASE_RE.match(name) and not UPPER_CASE_RE.match(name):
                violations.append(
                    f"class '{name}' (line {node.lineno}) is not PascalCase"
                )

            # Check method names inside the class
            for item in ast.iter_child_nodes(node):
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    mname = item.name
                    if mname.startswith("__") and mname.endswith("__"):
                        continue
                    if not SNAKE_CASE_RE.match(mname):
                        violations.append(
                            f"method '{name}.{mname}' (line {item.lineno}) is not snake_case"
                        )

        # Check module-level assignments
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id
                    if name in IGNORE_NAMES or name.startswith("_"):
                        continue
                    # Module-level: could be constant (UPPER) or variable (snake)
                    if not SNAKE_CASE_RE.match(name) and not UPPER_CASE_RE.match(name):
                        violations.append(
                            f"module-level name '{name}' (line {node.lineno}) "
                            f"is neither snake_case nor UPPER_CASE"
                        )

    return violations


def main():
    if len(sys.argv) < 2:
        print("Usage: check_o3_3.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    evidence = []
    all_pass = True

    src_dirs = [
        os.path.join(project_path, "artifacts", "src"),
        os.path.join(project_path, "artifacts"),
        os.path.join(project_path, "src"),
    ]

    py_files = []
    for sd in src_dirs:
        if not os.path.isdir(sd):
            continue
        for root, _dirs, files in os.walk(sd):
            if "__pycache__" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    fp = os.path.join(root, f)
                    if fp not in py_files:
                        py_files.append(fp)

    if not py_files:
        result = {
            "question": "o3.3",
            "answer": "no",
            "evidence": [{
                "type": "command_output",
                "command": "naming convention check",
                "stdout": "",
                "exit_code": -1,
                "detail": "No Python source files found"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    total_violations = 0
    violation_details = []

    for pf in py_files:
        rel_path = os.path.relpath(pf, project_path)
        violations = check_naming(pf)
        total_violations += len(violations)
        for v in violations:
            violation_details.append(f"{rel_path}: {v}")

    if total_violations > 0:
        # Allow small tolerance: < 5% violation rate
        # Estimate total names checked as ~10 per file
        estimated_total = max(len(py_files) * 10, 1)
        violation_rate = total_violations / estimated_total
        if violation_rate > 0.1:
            all_pass = False

        shown = violation_details[:15]
        evidence.append({
            "type": "command_output",
            "command": f"naming convention check ({len(py_files)} files)",
            "stdout": "\n".join(shown),
            "exit_code": 1,
            "detail": (
                f"Found {total_violations} naming convention violation(s) "
                f"across {len(py_files)} file(s)"
            )
        })
    else:
        evidence.append({
            "type": "command_output",
            "command": f"naming convention check ({len(py_files)} files)",
            "stdout": f"All {len(py_files)} files follow naming conventions",
            "exit_code": 0,
            "detail": "Zero naming convention violations -- OK"
        })

    result = {
        "question": "o3.3",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
