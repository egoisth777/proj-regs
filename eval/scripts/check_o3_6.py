#!/usr/bin/env python3
"""Check o3.6: Does the project have a working entry point?

Checks for:
- A pyproject.toml [project.scripts] or [tool.poetry.scripts] entry
- A __main__.py file enabling `python -m <package>`
- An if __name__ == "__main__" block in a source file
"""

import os
import re
import sys
import yaml


def main():
    if len(sys.argv) < 2:
        print("Usage: check_o3_6.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    evidence = []
    all_pass = False  # Must find at least one entry point

    src_dirs = [
        os.path.join(project_path, "artifacts", "src"),
        os.path.join(project_path, "artifacts"),
        os.path.join(project_path, "src"),
    ]

    # Check 1: pyproject.toml scripts entry
    pyproject_paths = [
        os.path.join(project_path, "artifacts", "pyproject.toml"),
        os.path.join(project_path, "pyproject.toml"),
    ]
    for pp in pyproject_paths:
        if os.path.isfile(pp):
            try:
                with open(pp, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                if "[project.scripts]" in content or "[tool.poetry.scripts]" in content:
                    all_pass = True
                    evidence.append({
                        "type": "command_output",
                        "command": "entry point check",
                        "stdout": os.path.relpath(pp, project_path),
                        "exit_code": 0,
                        "detail": f"pyproject.toml has scripts entry point definition"
                    })
            except OSError:
                pass

    # Check 2: __main__.py
    for sd in src_dirs:
        if not os.path.isdir(sd):
            continue
        for root, _dirs, files in os.walk(sd):
            if "__main__.py" in files:
                all_pass = True
                rel_path = os.path.relpath(os.path.join(root, "__main__.py"), project_path)
                evidence.append({
                    "type": "command_output",
                    "command": "entry point check",
                    "stdout": rel_path,
                    "exit_code": 0,
                    "detail": f"Found __main__.py at {rel_path} (python -m support)"
                })

    # Check 3: if __name__ == "__main__" blocks
    main_block_pattern = re.compile(
        r'''if\s+__name__\s*==\s*['"]__main__['"]\s*:''',
        re.MULTILINE
    )
    main_files = []
    for sd in src_dirs:
        if not os.path.isdir(sd):
            continue
        for root, _dirs, files in os.walk(sd):
            if "__pycache__" in root:
                continue
            for f in files:
                if not f.endswith(".py") or f.startswith("test_"):
                    continue
                fpath = os.path.join(root, f)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
                        content = fh.read()
                    if main_block_pattern.search(content):
                        main_files.append(os.path.relpath(fpath, project_path))
                except OSError:
                    pass

    if main_files:
        all_pass = True
        evidence.append({
            "type": "command_output",
            "command": "entry point check",
            "stdout": "\n".join(main_files[:5]),
            "exit_code": 0,
            "detail": (
                f"Found if __name__ == '__main__' block in "
                f"{len(main_files)} file(s): {', '.join(main_files[:5])}"
            )
        })

    if not all_pass:
        evidence.append({
            "type": "command_output",
            "command": "entry point check",
            "stdout": "",
            "exit_code": 1,
            "detail": "No working entry point found (no scripts in pyproject.toml, no __main__.py, no __name__ == '__main__' block)"
        })

    result = {
        "question": "o3.6",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
