#!/usr/bin/env python3
"""Check p1.4: Did test files exist before implementation code was written?

Verifies that the earliest test file (test_*.py) was committed/created
before or at the same time as the earliest implementation source file
in artifacts/src/.
"""

import os
import subprocess
import sys
import yaml


def git_first_commit_time(repo_root, filepath):
    """Get the timestamp of the first git commit that introduced a file."""
    try:
        result = subprocess.run(
            ["git", "log", "--diff-filter=A", "--follow", "--format=%ct", "--", filepath],
            capture_output=True, text=True, cwd=repo_root, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().splitlines()
            return int(lines[-1])
    except (subprocess.TimeoutExpired, ValueError):
        pass
    return None


def file_mtime(filepath):
    """Get file modification time as a fallback."""
    try:
        return int(os.path.getmtime(filepath))
    except OSError:
        return None


def get_file_time(repo_root, filepath):
    """Get the earliest known time for a file: git commit time or mtime."""
    git_time = git_first_commit_time(repo_root, filepath)
    if git_time is not None:
        return git_time, "git_commit"
    mt = file_mtime(os.path.join(repo_root, filepath))
    if mt is not None:
        return mt, "mtime"
    return None, None


def find_repo_root(project_path):
    """Find the git repo root from a project path."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, cwd=project_path, timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return project_path


def is_test_file(filename):
    """Check if a filename matches test file naming conventions."""
    return filename.endswith(".py") and (
        filename.startswith("test_") or filename.endswith("_test.py")
    )


def is_impl_file(filename):
    """Check if a filename is a non-test implementation source file."""
    if not filename.endswith((".py", ".js", ".ts", ".java", ".go", ".rs", ".c", ".cpp", ".h")):
        return False
    if is_test_file(filename):
        return False
    if filename.startswith("conftest") or filename == "__init__.py":
        return False
    return True


def collect_files(directory, predicate):
    """Recursively collect files matching a predicate."""
    results = []
    if not os.path.isdir(directory):
        return results
    for root, _dirs, files in os.walk(directory):
        for f in files:
            if predicate(f):
                results.append(os.path.join(root, f))
    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: check_p1_4.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])
    repo_root = find_repo_root(project_path)

    artifacts_dir = os.path.join(project_path, "artifacts")

    evidence = []
    all_pass = True

    # Collect test files
    test_dirs = [
        os.path.join(project_path, "artifacts", "tests"),
        os.path.join(project_path, "artifacts", "test"),
        os.path.join(project_path, "tests"),
        os.path.join(project_path, "test"),
    ]
    all_test_files = []
    for td in test_dirs:
        all_test_files.extend(collect_files(td, is_test_file))
    # Also search entire artifacts tree
    if os.path.isdir(artifacts_dir):
        for tf in collect_files(artifacts_dir, is_test_file):
            if tf not in all_test_files:
                all_test_files.append(tf)

    # Collect implementation files
    src_dirs = [
        os.path.join(project_path, "artifacts", "src"),
        os.path.join(project_path, "artifacts"),
    ]
    all_impl_files = []
    for sd in src_dirs:
        for f in collect_files(sd, is_impl_file):
            if f not in all_impl_files:
                # Skip files that live inside test directories
                rel = os.path.relpath(f, project_path)
                if "/test/" in rel or "/tests/" in rel:
                    continue
                all_impl_files.append(f)

    if not all_test_files:
        result = {
            "question": "p1.4",
            "answer": "no",
            "evidence": [{
                "type": "file_timestamp",
                "path": "tests/",
                "detail": "No test files found; cannot verify test-before-implementation ordering"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    if not all_impl_files:
        result = {
            "question": "p1.4",
            "answer": "yes",
            "evidence": [{
                "type": "file_timestamp",
                "path": "artifacts/",
                "detail": "No implementation files found; condition trivially satisfied"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    # Find earliest test file timestamp
    earliest_test_time = None
    earliest_test_file = None
    for tf in all_test_files:
        rel_tf = os.path.relpath(tf, repo_root)
        t, src = get_file_time(repo_root, rel_tf)
        if t is not None and (earliest_test_time is None or t < earliest_test_time):
            earliest_test_time = t
            earliest_test_file = rel_tf

    # Find earliest implementation file timestamp
    earliest_impl_time = None
    earliest_impl_file = None
    for imf in all_impl_files:
        rel_imf = os.path.relpath(imf, repo_root)
        t, src = get_file_time(repo_root, rel_imf)
        if t is not None and (earliest_impl_time is None or t < earliest_impl_time):
            earliest_impl_time = t
            earliest_impl_file = rel_imf

    if earliest_test_time is None:
        evidence.append({
            "type": "file_timestamp",
            "path": "tests/",
            "detail": "Could not determine timestamps for any test files"
        })
        all_pass = False
    elif earliest_impl_time is None:
        evidence.append({
            "type": "file_timestamp",
            "path": "artifacts/",
            "detail": "Could not determine timestamps for any implementation files"
        })
        all_pass = False
    elif earliest_test_time <= earliest_impl_time:
        evidence.append({
            "type": "file_timestamp",
            "path": earliest_test_file,
            "detail": (
                f"Earliest test '{earliest_test_file}' (t={earliest_test_time}) "
                f"<= earliest impl '{earliest_impl_file}' (t={earliest_impl_time}) -- OK"
            )
        })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": earliest_impl_file,
            "detail": (
                f"Earliest test '{earliest_test_file}' (t={earliest_test_time}) "
                f"> earliest impl '{earliest_impl_file}' (t={earliest_impl_time}) -- VIOLATION"
            )
        })
        all_pass = False

    evidence.append({
        "type": "file_timestamp",
        "path": "artifacts/",
        "detail": f"Found {len(all_test_files)} test file(s) and {len(all_impl_files)} implementation file(s)"
    })

    result = {
        "question": "p1.4",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
