#!/usr/bin/env python3
"""Check o1.2: Do all unit tests pass?

Runs python -m pytest in the artifacts directory. Reports pass/fail with test count.
"""

import os
import subprocess
import sys
import yaml


def main():
    if len(sys.argv) < 2:
        print("Usage: check_o1_2.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])
    artifacts_dir = os.path.join(project_path, "artifacts")

    evidence = []

    if not os.path.isdir(artifacts_dir):
        result = {
            "question": "o1.2",
            "answer": "no",
            "evidence": [{
                "type": "command_output",
                "command": "python -m pytest",
                "stdout": "",
                "exit_code": -1,
                "detail": "artifacts/ directory not found"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "--tb=short", "-q"],
            capture_output=True, text=True,
            cwd=artifacts_dir,
            timeout=120
        )
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        exit_code = proc.returncode

        # Parse test counts from pytest output
        # Typical output: "5 passed" or "3 passed, 2 failed"
        combined_output = stdout
        if stderr:
            combined_output += "\n" + stderr

        if exit_code == 0:
            detail = "All tests passed"
        elif exit_code == 5:
            # pytest exit code 5 = no tests collected
            detail = "No tests were collected by pytest"
        else:
            detail = f"Tests failed (exit code {exit_code})"

        evidence.append({
            "type": "command_output",
            "command": f"python -m pytest --tb=short -q (cwd={artifacts_dir})",
            "stdout": combined_output[:2000],  # Truncate if very long
            "exit_code": exit_code,
            "detail": detail
        })

        # exit_code 0 = all pass, 5 = no tests (treat as fail since question asks "do tests pass")
        answer = "yes" if exit_code == 0 else "no"

    except subprocess.TimeoutExpired:
        evidence.append({
            "type": "command_output",
            "command": "python -m pytest --tb=short -q",
            "stdout": "",
            "exit_code": -1,
            "detail": "pytest timed out after 120 seconds"
        })
        answer = "no"

    except FileNotFoundError:
        evidence.append({
            "type": "command_output",
            "command": "python -m pytest --tb=short -q",
            "stdout": "",
            "exit_code": -1,
            "detail": "pytest not found; ensure it is installed"
        })
        answer = "no"

    result = {
        "question": "o1.2",
        "answer": answer,
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
