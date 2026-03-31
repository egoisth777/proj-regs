#!/usr/bin/env python3
"""Check p4.5: Does context_map.json accurately reflect the final project structure?

Reads context_map.json and verifies that file references within it
correspond to actual files in the project.
"""

import json
import os
import sys
import yaml


def collect_paths_from_obj(obj, paths=None):
    """Recursively collect string values that look like file paths from a JSON object."""
    if paths is None:
        paths = set()

    if isinstance(obj, str):
        # Heuristic: strings containing '/' or ending with known extensions are paths
        if "/" in obj or obj.endswith((".py", ".md", ".json", ".yaml", ".yml", ".toml", ".txt")):
            paths.add(obj)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            # Keys might also be paths
            if isinstance(k, str) and ("/" in k or k.endswith((".py", ".md", ".json", ".yaml"))):
                paths.add(k)
            collect_paths_from_obj(v, paths)
    elif isinstance(obj, list):
        for item in obj:
            collect_paths_from_obj(item, paths)

    return paths


def main():
    if len(sys.argv) < 2:
        print("Usage: check_p4_5.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    evidence = []
    all_pass = True

    # Locate context_map.json
    candidates = [
        os.path.join(spec_root, "context_map.json"),
        os.path.join(spec_root, "runtime", "context_map.json"),
        os.path.join(project_path, "context_map.json"),
    ]

    context_map_path = None
    for c in candidates:
        if os.path.isfile(c):
            context_map_path = c
            break

    if context_map_path is None:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": spec_root,
            "detail": "context_map.json not found in project"
        })
        result = {
            "question": "p4.5",
            "answer": "no",
            "evidence": evidence
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    # Parse the context map
    try:
        with open(context_map_path, "r", encoding="utf-8", errors="replace") as f:
            context_map = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": os.path.relpath(context_map_path, project_path),
            "detail": f"Failed to parse context_map.json: {e}"
        })
        result = {
            "question": "p4.5",
            "answer": "no",
            "evidence": evidence
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    # Extract file paths referenced in the map
    referenced_paths = collect_paths_from_obj(context_map)

    if not referenced_paths:
        evidence.append({
            "type": "file_timestamp",
            "path": os.path.relpath(context_map_path, project_path),
            "detail": "No file path references found in context_map.json"
        })
        # An empty context map with no references is not necessarily wrong
        # but is suspicious
        all_pass = False
        result = {
            "question": "p4.5",
            "answer": "no",
            "evidence": evidence
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    # Check each referenced path exists
    found = 0
    missing = []
    for ref in sorted(referenced_paths):
        # Try resolving relative to project_path and spec_root
        candidates_check = [
            os.path.join(project_path, ref),
            os.path.join(spec_root, ref),
        ]
        exists = any(os.path.exists(c) for c in candidates_check)
        if exists:
            found += 1
        else:
            missing.append(ref)

    total = len(referenced_paths)
    evidence.append({
        "type": "file_timestamp",
        "path": os.path.relpath(context_map_path, project_path),
        "detail": f"context_map.json references {total} path(s); {found} exist, {len(missing)} missing"
    })

    if missing:
        # Allow a small tolerance (<=20% missing)
        miss_ratio = len(missing) / total if total else 1
        if miss_ratio > 0.2:
            all_pass = False
        shown = missing[:10]
        evidence.append({
            "type": "file_timestamp",
            "path": os.path.relpath(context_map_path, project_path),
            "detail": (
                f"Missing path(s): {', '.join(shown)}"
                + (f" ... and {len(missing) - 10} more" if len(missing) > 10 else "")
            )
        })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": os.path.relpath(context_map_path, project_path),
            "detail": "All referenced paths exist in the project -- OK"
        })

    result = {
        "question": "p4.5",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
