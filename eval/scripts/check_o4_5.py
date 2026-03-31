#!/usr/bin/env python3
"""Check o4.5: Does the file structure match what was laid out in tasks.md?

Compares files listed in tasks.md File Scope sections against actual files
that exist in the project.
"""

import os
import re
import sys
import yaml


def extract_file_scope(tasks_path):
    """Extract file paths from File Scope sections in tasks.md."""
    if not os.path.isfile(tasks_path):
        return []

    try:
        with open(tasks_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError:
        return []

    files = []

    # Look for "File Scope" or "Files" section
    in_file_scope = False
    for line in content.splitlines():
        stripped = line.strip()

        # Detect file scope section header
        if re.match(r"^#+\s*(?:File\s*Scope|Files|File\s*List|Scope)", stripped, re.IGNORECASE):
            in_file_scope = True
            continue

        # Detect next section header (end of file scope)
        if in_file_scope and re.match(r"^#+\s", stripped):
            in_file_scope = False
            continue

        if in_file_scope:
            # Extract file paths from bullet points or plain lines
            # Pattern: - `path/to/file.py` or - path/to/file.py
            m = re.match(r"^\s*[-*]\s+`?([^`\s]+\.\w+)`?", stripped)
            if m:
                files.append(m.group(1))
                continue

            # Pattern: plain path with extension
            m = re.match(r"^\s*`?([a-zA-Z0-9_/.-]+\.\w{1,10})`?", stripped)
            if m and "/" in m.group(1):
                files.append(m.group(1))

    # Also look for inline file references in the whole document
    if not files:
        # Pattern: `path/to/file.ext` anywhere in the doc
        code_pattern = re.compile(r"`([a-zA-Z0-9_/.-]+\.\w{1,10})`")
        for m in code_pattern.finditer(content):
            path = m.group(1)
            if "/" in path and not path.startswith("http"):
                files.append(path)

    return list(set(files))


def main():
    if len(sys.argv) < 2:
        print("Usage: check_o4_5.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    evidence = []
    all_pass = True

    # Find all tasks.md files
    tasks_files = []
    for root, _dirs, files in os.walk(spec_root):
        for fname in files:
            if fname == "tasks.md":
                tasks_files.append(os.path.join(root, fname))

    if not tasks_files:
        evidence.append({
            "type": "file_timestamp",
            "path": spec_root,
            "detail": "No tasks.md files found"
        })
        all_pass = False
        result = {
            "question": "o4.5",
            "answer": "no",
            "evidence": evidence
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    all_expected_files = []
    for tf in tasks_files:
        scope_files = extract_file_scope(tf)
        rel_tf = os.path.relpath(tf, project_path)
        if scope_files:
            evidence.append({
                "type": "file_timestamp",
                "path": rel_tf,
                "detail": f"File Scope lists {len(scope_files)} file(s)"
            })
            all_expected_files.extend(scope_files)
        else:
            evidence.append({
                "type": "file_timestamp",
                "path": rel_tf,
                "detail": "No File Scope section or file references found"
            })

    if not all_expected_files:
        evidence.append({
            "type": "file_timestamp",
            "path": spec_root,
            "detail": "No file paths extracted from any tasks.md -- cannot verify structure"
        })
        all_pass = False
        result = {
            "question": "o4.5",
            "answer": "no",
            "evidence": evidence
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    # Deduplicate
    all_expected_files = list(set(all_expected_files))

    # Check which expected files actually exist
    found = []
    missing = []

    for ef in sorted(all_expected_files):
        candidates = [
            os.path.join(project_path, ef),
            os.path.join(project_path, "artifacts", ef),
            os.path.join(project_path, "artifacts", "src", ef),
        ]
        exists = any(os.path.exists(c) for c in candidates)
        if exists:
            found.append(ef)
        else:
            missing.append(ef)

    total = len(all_expected_files)
    evidence.append({
        "type": "file_timestamp",
        "path": "tasks.md",
        "detail": f"{len(found)}/{total} expected file(s) exist"
    })

    if missing:
        coverage = len(found) / total if total else 0
        if coverage < 0.7:
            all_pass = False
        shown = missing[:10]
        evidence.append({
            "type": "file_timestamp",
            "path": "tasks.md",
            "detail": (
                f"Missing files: {', '.join(shown)}"
                + (f" ... and {len(missing) - 10} more" if len(missing) > 10 else "")
            )
        })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": "tasks.md",
            "detail": "All files listed in tasks.md File Scope exist -- OK"
        })

    result = {
        "question": "o4.5",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
