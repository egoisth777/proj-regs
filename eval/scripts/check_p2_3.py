#!/usr/bin/env python3
"""Check p2.3: Did workers only modify files listed in their tasks.md file scope?

Parses each feature's tasks.md for 'File Scope' sections, extracts allowed paths.
Checks that source files in artifacts/ are mentioned somewhere in a tasks.md file scope.
"""

import os
import re
import sys
import yaml


def parse_file_scope(tasks_md_path):
    """Parse a tasks.md file and extract file scope entries.

    Looks for sections titled 'File Scope' or similar, then extracts
    file paths listed beneath them. Also looks for paths in backticks
    or bullet points following scope headings.
    """
    if not os.path.isfile(tasks_md_path):
        return []

    with open(tasks_md_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    scoped_files = []

    # Strategy 1: Look for "File Scope" sections
    scope_pattern = re.compile(
        r"(?:#+\s*)?[Ff]ile\s+[Ss]cope[:\s]*\n(.*?)(?=\n#|\n\n\n|\Z)",
        re.DOTALL
    )
    for match in scope_pattern.finditer(content):
        block = match.group(1)
        # Extract paths from bullets or backtick-wrapped paths
        for line in block.splitlines():
            line = line.strip()
            # Match paths in backticks
            bt_matches = re.findall(r"`([^`]+)`", line)
            for p in bt_matches:
                if "/" in p or p.endswith((".py", ".js", ".ts", ".md")):
                    scoped_files.append(p)
            # Match paths after bullet markers
            bullet_match = re.match(r"^[-*]\s+(.+)", line)
            if bullet_match:
                path_candidate = bullet_match.group(1).strip().strip("`")
                if "/" in path_candidate or path_candidate.endswith((".py", ".js", ".ts")):
                    scoped_files.append(path_candidate)

    # Strategy 2: Look for "Scope:" or "Files:" inline patterns
    inline_pattern = re.compile(r"(?:scope|files)\s*:\s*`([^`]+)`", re.IGNORECASE)
    for match in inline_pattern.finditer(content):
        scoped_files.append(match.group(1))

    return list(set(scoped_files))


def collect_source_files(directory):
    """Collect source code files in a directory."""
    source_files = []
    if not os.path.isdir(directory):
        return source_files
    for root, _dirs, files in os.walk(directory):
        for f in files:
            if f.endswith((".py", ".js", ".ts", ".java", ".go", ".rs", ".c", ".cpp", ".h")):
                source_files.append(os.path.join(root, f))
    return source_files


def normalize_path(path):
    """Normalize a path for comparison by stripping leading ./ and trailing /."""
    path = path.strip().strip("/")
    if path.startswith("./"):
        path = path[2:]
    return path


def main():
    if len(sys.argv) < 2:
        print("Usage: check_p2_3.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    # Resolve spec root: reg_root/ssot/ if it exists, else reg_root
    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    changes_dir = os.path.join(spec_root, "runtime", "openspec", "changes")
    artifacts_dir = os.path.join(project_path, "artifacts")

    evidence = []
    all_pass = True

    # Gather all scoped files from all tasks.md files
    all_scoped_paths = []

    if os.path.isdir(changes_dir):
        feature_dirs = [
            d for d in os.listdir(changes_dir)
            if os.path.isdir(os.path.join(changes_dir, d))
        ]

        for feature in sorted(feature_dirs):
            tasks_file = os.path.join(changes_dir, feature, "tasks.md")
            scoped = parse_file_scope(tasks_file)
            if scoped:
                all_scoped_paths.extend(scoped)
                evidence.append({
                    "type": "file_timestamp",
                    "path": tasks_file,
                    "detail": f"Feature '{feature}': Found {len(scoped)} scoped path(s): {', '.join(scoped[:5])}"
                })
            elif os.path.isfile(tasks_file):
                evidence.append({
                    "type": "file_timestamp",
                    "path": tasks_file,
                    "detail": f"Feature '{feature}': tasks.md exists but no File Scope section parsed"
                })
            else:
                evidence.append({
                    "type": "file_timestamp",
                    "path": tasks_file,
                    "detail": f"Feature '{feature}': tasks.md not found"
                })
    else:
        result = {
            "question": "p2.3",
            "answer": "no",
            "evidence": [{
                "type": "missing_directory",
                "path": changes_dir,
                "detail": "runtime/openspec/changes/ directory not found"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    # Check that source files in artifacts/ are covered by scoped paths
    source_files = collect_source_files(artifacts_dir)
    normalized_scopes = [normalize_path(p) for p in all_scoped_paths]

    unscoped_files = []
    for sf in source_files:
        rel_sf = os.path.relpath(sf, project_path)
        norm_sf = normalize_path(rel_sf)

        # Check if this file matches any scoped path (exact match, prefix, or basename)
        covered = False
        for sp in normalized_scopes:
            norm_sp = normalize_path(sp)
            if norm_sf == norm_sp:
                covered = True
                break
            if norm_sf.startswith(norm_sp + "/") or norm_sf.startswith(norm_sp):
                covered = True
                break
            if norm_sp.endswith(os.path.basename(norm_sf)):
                covered = True
                break
            # Check if scope is a directory prefix
            if norm_sf.startswith(norm_sp):
                covered = True
                break
        if not covered:
            unscoped_files.append(rel_sf)

    if unscoped_files:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": "artifacts/",
            "detail": (
                f"Found {len(unscoped_files)} source file(s) not in any tasks.md file scope: "
                f"{', '.join(unscoped_files[:10])}"
            )
        })
    elif source_files:
        evidence.append({
            "type": "file_timestamp",
            "path": "artifacts/",
            "detail": f"All {len(source_files)} source file(s) are covered by tasks.md file scopes"
        })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": "artifacts/",
            "detail": "No source files found in artifacts/ to check"
        })

    result = {
        "question": "p2.3",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
