#!/usr/bin/env python3
"""Check o4.6: Are there zero todo/fixme markers left in delivered code?

Greps for TODO, FIXME, HACK, and XXX markers in Python source files.
"""

import os
import re
import sys
import yaml


MARKER_PATTERN = re.compile(
    r"\b(TODO|FIXME|HACK|XXX)\b",
    re.IGNORECASE
)


def main():
    if len(sys.argv) < 2:
        print("Usage: check_o4_6.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    evidence = []
    all_pass = True

    src_dirs = [
        os.path.join(project_path, "artifacts", "src"),
        os.path.join(project_path, "artifacts"),
        os.path.join(project_path, "src"),
    ]

    py_files = []
    for sd in src_dirs:
        if not os.path.isdir(sd):
            continue
        for root, _dirs, files in os.walk(sd):
            if "__pycache__" in root:
                continue
            # Skip test directories for this check (checking delivered source)
            basename = os.path.basename(root)
            if basename in ("tests", "test"):
                continue
            for f in files:
                if f.endswith(".py"):
                    fp = os.path.join(root, f)
                    if fp not in py_files:
                        py_files.append(fp)

    if not py_files:
        result = {
            "question": "o4.6",
            "answer": "no",
            "evidence": [{
                "type": "command_output",
                "command": "todo/fixme grep",
                "stdout": "",
                "exit_code": -1,
                "detail": "No Python source files found to check"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    total_markers = 0
    marker_details = []

    for pf in py_files:
        rel_path = os.path.relpath(pf, project_path)
        try:
            with open(pf, "r", encoding="utf-8", errors="replace") as f:
                for lineno, line in enumerate(f, 1):
                    for m in MARKER_PATTERN.finditer(line):
                        total_markers += 1
                        context = line.strip()[:80]
                        marker_details.append(f"{rel_path}:{lineno} -- {context}")
        except OSError:
            pass

    if total_markers > 0:
        all_pass = False
        evidence.append({
            "type": "command_output",
            "command": f"todo/fixme grep ({len(py_files)} files)",
            "stdout": "\n".join(marker_details[:15]),
            "exit_code": 1,
            "detail": f"Found {total_markers} TODO/FIXME/HACK/XXX marker(s)"
        })
    else:
        evidence.append({
            "type": "command_output",
            "command": f"todo/fixme grep ({len(py_files)} files)",
            "stdout": f"Checked {len(py_files)} file(s); zero markers found",
            "exit_code": 0,
            "detail": "Zero TODO/FIXME/HACK/XXX markers in delivered source -- OK"
        })

    result = {
        "question": "o4.6",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
