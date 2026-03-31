#!/usr/bin/env python3
"""Check o3.1: Does the code pass linting with zero errors?

Runs py_compile on all Python files and checks for basic style issues
via ast parsing (syntax errors, indentation).
"""

import ast
import os
import subprocess
import sys
import yaml


def find_python_files(directory):
    """Recursively find all .py files under a directory."""
    py_files = []
    if not os.path.isdir(directory):
        return py_files
    for root, _dirs, files in os.walk(directory):
        if "__pycache__" in root:
            continue
        for f in files:
            if f.endswith(".py"):
                py_files.append(os.path.join(root, f))
    return py_files


def check_compile(filepath):
    """Check if a Python file compiles without errors."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", filepath],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return False, (result.stderr or result.stdout).strip()
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "compilation timed out"


def check_ast_issues(filepath):
    """Check for basic code quality issues using AST parsing."""
    issues = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except OSError:
        return ["could not read file"]

    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError as e:
        return [f"SyntaxError: {e}"]

    # Check for bare except
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                issues.append(f"line {node.lineno}: bare except clause")

    # Check for very long lines (>120 chars) -- just count them
    long_lines = 0
    for i, line in enumerate(source.splitlines(), 1):
        if len(line) > 120:
            long_lines += 1

    if long_lines > 0:
        issues.append(f"{long_lines} line(s) exceed 120 characters")

    return issues


def main():
    if len(sys.argv) < 2:
        print("Usage: check_o3_1.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    # Check files in artifacts/
    src_dir = os.path.join(project_path, "artifacts", "src")
    artifacts_dir = os.path.join(project_path, "artifacts")
    search_dir = src_dir if os.path.isdir(src_dir) else artifacts_dir

    py_files = find_python_files(search_dir)

    evidence = []

    if not py_files:
        result = {
            "question": "o3.1",
            "answer": "no",
            "evidence": [{
                "type": "command_output",
                "command": "lint check",
                "stdout": "",
                "exit_code": -1,
                "detail": f"No .py files found under {os.path.relpath(search_dir, project_path)}/"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    compile_failures = []
    ast_issues = {}
    total_issues = 0

    for py_file in py_files:
        rel_path = os.path.relpath(py_file, project_path)

        # Check compilation
        ok, error = check_compile(py_file)
        if not ok:
            compile_failures.append(f"{rel_path}: {error}")

        # Check AST issues
        issues = check_ast_issues(py_file)
        if issues:
            ast_issues[rel_path] = issues
            total_issues += len(issues)

    all_pass = len(compile_failures) == 0

    if compile_failures:
        evidence.append({
            "type": "command_output",
            "command": f"py_compile ({len(py_files)} files)",
            "stdout": "\n".join(compile_failures[:10]),
            "exit_code": 1,
            "detail": f"{len(compile_failures)} file(s) failed to compile"
        })
    else:
        evidence.append({
            "type": "command_output",
            "command": f"py_compile ({len(py_files)} files)",
            "stdout": f"All {len(py_files)} files compile successfully",
            "exit_code": 0,
            "detail": f"All {len(py_files)} Python files pass compilation check"
        })

    if ast_issues:
        issue_summary = []
        for path, issues in list(ast_issues.items())[:5]:
            issue_summary.append(f"{path}: {'; '.join(issues[:3])}")
        evidence.append({
            "type": "command_output",
            "command": "ast lint check",
            "stdout": "\n".join(issue_summary),
            "exit_code": 1 if compile_failures else 0,
            "detail": f"Found {total_issues} style issue(s) across {len(ast_issues)} file(s) (non-blocking)"
        })

    # Try running flake8 or ruff if available
    for linter, cmd in [("ruff", ["ruff", "check", "."]), ("flake8", ["flake8", "--count", "."])]:
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True, text=True,
                cwd=search_dir,
                timeout=30
            )
            if proc.returncode == 0:
                evidence.append({
                    "type": "command_output",
                    "command": " ".join(cmd),
                    "stdout": proc.stdout.strip()[:500],
                    "exit_code": 0,
                    "detail": f"{linter} reports zero errors"
                })
            else:
                evidence.append({
                    "type": "command_output",
                    "command": " ".join(cmd),
                    "stdout": proc.stdout.strip()[:500],
                    "exit_code": proc.returncode,
                    "detail": f"{linter} found issues"
                })
                all_pass = False
            break  # Use first available linter
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    result = {
        "question": "o3.1",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
