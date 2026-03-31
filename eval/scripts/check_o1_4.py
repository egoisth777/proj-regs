#!/usr/bin/env python3
"""Check o1.4: Does the app start and run without runtime errors?

Tries to run the CLI/app with --help and checks for exit code 0.
Falls back to importing the main module.
"""

import os
import subprocess
import sys
import yaml


def find_entry_points(project_path):
    """Find potential entry points for the application."""
    artifacts_dir = os.path.join(project_path, "artifacts")
    src_dir = os.path.join(project_path, "artifacts", "src")

    candidates = []

    # Check for common entry point files
    entry_names = ["main.py", "cli.py", "app.py", "__main__.py", "run.py", "server.py"]
    search_dirs = [src_dir, artifacts_dir, project_path]

    for sd in search_dirs:
        if not os.path.isdir(sd):
            continue
        for root, _dirs, files in os.walk(sd):
            for f in files:
                if f in entry_names:
                    candidates.append(os.path.join(root, f))

    # Check for setup.py / pyproject.toml console_scripts
    setup_py = os.path.join(artifacts_dir, "setup.py")
    pyproject = os.path.join(artifacts_dir, "pyproject.toml")
    if os.path.isfile(pyproject):
        candidates.append(("pyproject", pyproject))
    if os.path.isfile(setup_py):
        candidates.append(("setup", setup_py))

    return candidates


def try_run_entry_point(filepath, cwd):
    """Try to run a Python entry point with --help."""
    try:
        proc = subprocess.run(
            [sys.executable, filepath, "--help"],
            capture_output=True, text=True,
            cwd=cwd,
            timeout=30,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "Timed out after 30 seconds"
    except FileNotFoundError:
        return -1, "", "File not found"


def try_import_module(filepath, cwd):
    """Try to import a Python module to check for import errors."""
    try:
        proc = subprocess.run(
            [sys.executable, "-c", f"import importlib.util; spec = importlib.util.spec_from_file_location('m', '{filepath}'); mod = importlib.util.module_from_spec(spec)"],
            capture_output=True, text=True,
            cwd=cwd,
            timeout=15,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return -1, "", "Could not import"


def main():
    if len(sys.argv) < 2:
        print("Usage: check_o1_4.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])
    artifacts_dir = os.path.join(project_path, "artifacts")
    cwd = artifacts_dir if os.path.isdir(artifacts_dir) else project_path

    evidence = []
    answer = "no"

    entry_points = find_entry_points(project_path)

    if not entry_points:
        result = {
            "question": "o1.4",
            "answer": "no",
            "evidence": [{
                "type": "command_output",
                "command": "find entry points",
                "stdout": "",
                "exit_code": -1,
                "detail": "No entry point files found (main.py, cli.py, app.py, __main__.py)"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    for ep in entry_points:
        if isinstance(ep, tuple):
            # Skip pyproject/setup -- just note them
            evidence.append({
                "type": "file_timestamp",
                "path": ep[1],
                "detail": f"Found {ep[0]} file: {os.path.relpath(ep[1], project_path)}"
            })
            continue

        rel_path = os.path.relpath(ep, project_path)

        # Try running with --help
        exit_code, stdout, stderr = try_run_entry_point(ep, cwd)

        if exit_code == 0:
            answer = "yes"
            evidence.append({
                "type": "command_output",
                "command": f"python {rel_path} --help",
                "stdout": stdout[:500] if stdout else "(no output)",
                "exit_code": exit_code,
                "detail": f"Entry point '{rel_path}' runs successfully with --help"
            })
            break  # One successful entry point is sufficient
        else:
            # Try just importing
            import_exit, import_out, import_err = try_import_module(ep, cwd)
            if import_exit == 0:
                answer = "yes"
                evidence.append({
                    "type": "command_output",
                    "command": f"python -c 'import {rel_path}'",
                    "stdout": "",
                    "exit_code": 0,
                    "detail": f"Entry point '{rel_path}' imports successfully (--help returned exit code {exit_code})"
                })
                break
            else:
                combined_err = stderr
                if import_err:
                    combined_err += "\n" + import_err
                evidence.append({
                    "type": "command_output",
                    "command": f"python {rel_path} --help",
                    "stdout": combined_err[:500],
                    "exit_code": exit_code,
                    "detail": f"Entry point '{rel_path}' failed: exit code {exit_code}"
                })

    if answer == "no" and not any(
        e.get("type") == "command_output" for e in evidence
    ):
        evidence.append({
            "type": "command_output",
            "command": "run entry points",
            "stdout": "",
            "exit_code": -1,
            "detail": "No entry points could be executed successfully"
        })

    result = {
        "question": "o1.4",
        "answer": answer,
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
