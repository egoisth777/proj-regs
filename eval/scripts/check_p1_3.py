#!/usr/bin/env python3
"""Check p1.3: Did test_spec exist before any test files were written?

Verifies that test_spec.md in each feature folder was committed/created
before test files in tests/.
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


def find_test_files(directory):
    """Recursively find test files (test_*.py or *_test.py) under a directory."""
    test_files = []
    if not os.path.isdir(directory):
        return test_files
    for root, _dirs, files in os.walk(directory):
        for f in files:
            if (f.startswith("test_") or f.endswith("_test.py")) and f.endswith(".py"):
                test_files.append(os.path.join(root, f))
    return test_files


def main():
    if len(sys.argv) < 2:
        print("Usage: check_p1_3.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])
    repo_root = find_repo_root(project_path)

    changes_dir = os.path.join(project_path, "runtime", "openspec", "changes")
    # Test files can be in artifacts/tests/ or tests/ relative to project
    tests_candidates = [
        os.path.join(project_path, "artifacts", "tests"),
        os.path.join(project_path, "artifacts", "test"),
        os.path.join(project_path, "tests"),
        os.path.join(project_path, "test"),
    ]

    evidence = []
    all_pass = True

    if not os.path.isdir(changes_dir):
        result = {
            "question": "p1.3",
            "answer": "no",
            "evidence": [{
                "type": "missing_directory",
                "path": changes_dir,
                "detail": "runtime/openspec/changes/ directory not found"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    # Collect all test files across candidate directories
    all_test_files = []
    for td in tests_candidates:
        all_test_files.extend(find_test_files(td))

    # Also search recursively for any test files under artifacts/
    artifacts_dir = os.path.join(project_path, "artifacts")
    if os.path.isdir(artifacts_dir):
        for root, _dirs, files in os.walk(artifacts_dir):
            for f in files:
                fp = os.path.join(root, f)
                if fp not in all_test_files and f.endswith(".py") and (f.startswith("test_") or f.endswith("_test.py")):
                    all_test_files.append(fp)

    if not all_test_files:
        result = {
            "question": "p1.3",
            "answer": "yes",
            "evidence": [{
                "type": "file_timestamp",
                "path": "tests/",
                "detail": "No test files found; condition trivially satisfied"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    # Find the earliest test file timestamp
    earliest_test_time = None
    earliest_test_file = None
    for tf in all_test_files:
        rel_tf = os.path.relpath(tf, repo_root)
        t, src = get_file_time(repo_root, rel_tf)
        if t is not None and (earliest_test_time is None or t < earliest_test_time):
            earliest_test_time = t
            earliest_test_file = rel_tf

    feature_dirs = [
        d for d in os.listdir(changes_dir)
        if os.path.isdir(os.path.join(changes_dir, d))
    ]

    if not feature_dirs:
        result = {
            "question": "p1.3",
            "answer": "no",
            "evidence": [{
                "type": "missing_directory",
                "path": changes_dir,
                "detail": "No feature directories found"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    for feature in sorted(feature_dirs):
        feature_path = os.path.join(changes_dir, feature)
        test_spec_file = os.path.join(feature_path, "test_spec.md")
        rel_test_spec = os.path.relpath(test_spec_file, repo_root)

        if not os.path.isfile(test_spec_file):
            evidence.append({
                "type": "file_timestamp",
                "path": rel_test_spec,
                "detail": f"Feature '{feature}': test_spec.md does not exist"
            })
            all_pass = False
            continue

        spec_time, spec_src = get_file_time(repo_root, rel_test_spec)

        if spec_time is None:
            evidence.append({
                "type": "file_timestamp",
                "path": rel_test_spec,
                "detail": f"Feature '{feature}': Could not determine test_spec.md timestamp"
            })
            all_pass = False
            continue

        if earliest_test_time is not None and spec_time <= earliest_test_time:
            evidence.append({
                "type": "file_timestamp",
                "path": rel_test_spec,
                "detail": (
                    f"Feature '{feature}': test_spec.md ({spec_src}={spec_time}) "
                    f"<= earliest test file '{earliest_test_file}' ({earliest_test_time}) -- OK"
                )
            })
        elif earliest_test_time is not None:
            evidence.append({
                "type": "file_timestamp",
                "path": rel_test_spec,
                "detail": (
                    f"Feature '{feature}': test_spec.md ({spec_src}={spec_time}) "
                    f"> earliest test file '{earliest_test_file}' ({earliest_test_time}) -- VIOLATION"
                )
            })
            all_pass = False
        else:
            evidence.append({
                "type": "file_timestamp",
                "path": rel_test_spec,
                "detail": f"Feature '{feature}': test_spec.md exists but no test file timestamps available"
            })

    result = {
        "question": "p1.3",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
