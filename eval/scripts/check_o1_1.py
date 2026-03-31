#!/usr/bin/env python3
"""Check o1.1: Does the application build without errors?

Runs python -m py_compile on all .py files in artifacts/src/.
Reports pass/fail.
"""

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
        for f in files:
            if f.endswith(".py"):
                py_files.append(os.path.join(root, f))
    return py_files


def main():
    if len(sys.argv) < 2:
        print("Usage: check_o1_1.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    # Look for Python files in artifacts/src/ first, then artifacts/
    src_dir = os.path.join(project_path, "artifacts", "src")
    artifacts_dir = os.path.join(project_path, "artifacts")

    search_dir = src_dir if os.path.isdir(src_dir) else artifacts_dir

    py_files = find_python_files(search_dir)

    evidence = []

    if not py_files:
        result = {
            "question": "o1.1",
            "answer": "no",
            "evidence": [{
                "type": "command_output",
                "command": "python -m py_compile <files>",
                "stdout": "",
                "exit_code": -1,
                "detail": f"No .py files found under {os.path.relpath(search_dir, project_path)}/"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    all_pass = True
    failures = []
    successes = 0

    for py_file in py_files:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", py_file],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                all_pass = False
                rel_path = os.path.relpath(py_file, project_path)
                error_msg = (result.stderr or result.stdout).strip()
                failures.append(f"{rel_path}: {error_msg}")
            else:
                successes += 1
        except subprocess.TimeoutExpired:
            all_pass = False
            rel_path = os.path.relpath(py_file, project_path)
            failures.append(f"{rel_path}: compilation timed out")

    stdout_summary = f"Compiled {len(py_files)} file(s): {successes} passed, {len(failures)} failed"
    if failures:
        stdout_summary += "\nFailures:\n" + "\n".join(failures[:20])

    evidence.append({
        "type": "command_output",
        "command": f"python -m py_compile (on {len(py_files)} files)",
        "stdout": stdout_summary,
        "exit_code": 0 if all_pass else 1,
        "detail": (
            f"All {len(py_files)} Python files compile successfully"
            if all_pass
            else f"{len(failures)} of {len(py_files)} files failed to compile"
        )
    })

    result = {
        "question": "o1.1",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
