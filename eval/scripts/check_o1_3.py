#!/usr/bin/env python3
"""Check o1.3: Do all integration tests pass?

Looks for test files matching integration test patterns (test_*integration*,
test_cli*, test_e2e*) and runs them with pytest.
"""

import os
import subprocess
import sys
import yaml


def find_integration_tests(directory):
    """Recursively find integration/CLI/e2e test files."""
    integration_files = []
    if not os.path.isdir(directory):
        return integration_files

    integration_patterns = [
        "integration", "cli", "e2e", "end_to_end", "endtoend",
        "acceptance", "functional", "smoke"
    ]

    for root, _dirs, files in os.walk(directory):
        for f in files:
            if not f.endswith(".py"):
                continue
            if not (f.startswith("test_") or f.endswith("_test.py")):
                continue
            f_lower = f.lower()
            if any(pat in f_lower for pat in integration_patterns):
                integration_files.append(os.path.join(root, f))

    return integration_files


def main():
    if len(sys.argv) < 2:
        print("Usage: check_o1_3.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])
    artifacts_dir = os.path.join(project_path, "artifacts")

    evidence = []

    # Search for integration tests in multiple locations
    search_dirs = [
        os.path.join(project_path, "artifacts", "tests"),
        os.path.join(project_path, "artifacts", "test"),
        os.path.join(project_path, "artifacts"),
        os.path.join(project_path, "tests"),
        os.path.join(project_path, "test"),
    ]

    all_integration_files = []
    for sd in search_dirs:
        for f in find_integration_tests(sd):
            if f not in all_integration_files:
                all_integration_files.append(f)

    if not all_integration_files:
        # No integration tests found -- check if there are ANY test files
        # that test across module boundaries
        result = {
            "question": "o1.3",
            "answer": "no",
            "evidence": [{
                "type": "command_output",
                "command": "find integration tests",
                "stdout": "",
                "exit_code": -1,
                "detail": "No integration test files found (patterns: test_*integration*, test_cli*, test_e2e*)"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    # Run the integration tests
    cwd = artifacts_dir if os.path.isdir(artifacts_dir) else project_path

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "--tb=short", "-q"] + all_integration_files,
            capture_output=True, text=True,
            cwd=cwd,
            timeout=120
        )
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        exit_code = proc.returncode

        combined_output = stdout
        if stderr:
            combined_output += "\n" + stderr

        if exit_code == 0:
            detail = f"All integration tests passed ({len(all_integration_files)} file(s))"
        elif exit_code == 5:
            detail = "No integration tests were collected by pytest"
        else:
            detail = f"Integration tests failed (exit code {exit_code})"

        evidence.append({
            "type": "command_output",
            "command": f"python -m pytest --tb=short -q ({len(all_integration_files)} integration test file(s))",
            "stdout": combined_output[:2000],
            "exit_code": exit_code,
            "detail": detail
        })

        answer = "yes" if exit_code == 0 else "no"

    except subprocess.TimeoutExpired:
        evidence.append({
            "type": "command_output",
            "command": "python -m pytest (integration tests)",
            "stdout": "",
            "exit_code": -1,
            "detail": "Integration tests timed out after 120 seconds"
        })
        answer = "no"

    except FileNotFoundError:
        evidence.append({
            "type": "command_output",
            "command": "python -m pytest (integration tests)",
            "stdout": "",
            "exit_code": -1,
            "detail": "pytest not found; ensure it is installed"
        })
        answer = "no"

    # List the integration test files found
    rel_files = [os.path.relpath(f, project_path) for f in all_integration_files]
    evidence.append({
        "type": "file_timestamp",
        "path": "tests/",
        "detail": f"Integration test files: {', '.join(rel_files[:10])}"
    })

    result = {
        "question": "o1.3",
        "answer": answer,
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
