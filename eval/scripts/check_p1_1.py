#!/usr/bin/env python3
"""Check p1.1: Did every feature have a proposal created before any other spec?

Verifies that proposal.md exists in each feature folder under
runtime/openspec/changes/ and has an earlier git commit or mtime than
behavior_spec.md and test_spec.md.
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
            # Last line is the earliest commit (git log is newest-first)
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


def main():
    if len(sys.argv) < 2:
        print("Usage: check_p1_1.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])
    repo_root = find_repo_root(project_path)

    # Resolve spec root: reg_root/ssot/ if it exists, else reg_root
    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    changes_dir = os.path.join(spec_root, "runtime", "openspec", "changes")
    evidence = []
    all_pass = True

    if not os.path.isdir(changes_dir):
        result = {
            "question": "p1.1",
            "answer": "no",
            "evidence": [{
                "type": "missing_directory",
                "path": changes_dir,
                "detail": "runtime/openspec/changes/ directory not found"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    feature_dirs = [
        d for d in os.listdir(changes_dir)
        if os.path.isdir(os.path.join(changes_dir, d))
    ]

    if not feature_dirs:
        result = {
            "question": "p1.1",
            "answer": "no",
            "evidence": [{
                "type": "missing_directory",
                "path": changes_dir,
                "detail": "No feature directories found under runtime/openspec/changes/"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    for feature in sorted(feature_dirs):
        feature_path = os.path.join(changes_dir, feature)
        proposal_file = os.path.join(feature_path, "proposal.md")
        rel_proposal = os.path.relpath(proposal_file, repo_root)

        if not os.path.isfile(proposal_file):
            evidence.append({
                "type": "file_timestamp",
                "path": rel_proposal,
                "detail": f"Feature '{feature}': proposal.md does not exist"
            })
            all_pass = False
            continue

        proposal_time, proposal_src = get_file_time(repo_root, rel_proposal)

        if proposal_time is None:
            evidence.append({
                "type": "file_timestamp",
                "path": rel_proposal,
                "detail": f"Feature '{feature}': Could not determine proposal.md timestamp"
            })
            all_pass = False
            continue

        for spec_name in ["behavior_spec.md", "test_spec.md"]:
            spec_file = os.path.join(feature_path, spec_name)
            rel_spec = os.path.relpath(spec_file, repo_root)

            if not os.path.isfile(spec_file):
                # Spec doesn't exist, so proposal was before it trivially
                evidence.append({
                    "type": "file_timestamp",
                    "path": rel_spec,
                    "detail": f"Feature '{feature}': {spec_name} does not exist (proposal precedes by default)"
                })
                continue

            spec_time, spec_src = get_file_time(repo_root, rel_spec)

            if spec_time is None:
                evidence.append({
                    "type": "file_timestamp",
                    "path": rel_spec,
                    "detail": f"Feature '{feature}': Could not determine {spec_name} timestamp"
                })
                all_pass = False
                continue

            if proposal_time <= spec_time:
                evidence.append({
                    "type": "file_timestamp",
                    "path": rel_proposal,
                    "detail": (
                        f"Feature '{feature}': proposal.md ({proposal_src}={proposal_time}) "
                        f"<= {spec_name} ({spec_src}={spec_time}) -- OK"
                    )
                })
            else:
                evidence.append({
                    "type": "file_timestamp",
                    "path": rel_proposal,
                    "detail": (
                        f"Feature '{feature}': proposal.md ({proposal_src}={proposal_time}) "
                        f"> {spec_name} ({spec_src}={spec_time}) -- VIOLATION"
                    )
                })
                all_pass = False

    result = {
        "question": "p1.1",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence if evidence else [{
            "type": "file_timestamp",
            "path": changes_dir,
            "detail": "No features or specs found to evaluate"
        }]
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
