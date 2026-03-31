#!/usr/bin/env python3
"""Check o1.6: Do API contracts match what the spec defined?

Extracts function/method signatures from behavior_spec.md and checks that
matching signatures exist in the source code.
"""

import ast
import os
import re
import sys
import yaml


def extract_spec_signatures(behavior_spec_path):
    """Extract function/method names and signatures mentioned in behavior_spec."""
    if not os.path.isfile(behavior_spec_path):
        return []

    try:
        with open(behavior_spec_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError:
        return []

    signatures = []

    # Match function signatures in code blocks: def func_name(...)
    code_block_pattern = re.compile(
        r"(?:def|async\s+def)\s+(\w+)\s*\(([^)]*)\)",
        re.MULTILINE
    )
    for m in code_block_pattern.finditer(content):
        name = m.group(1)
        params = m.group(2).strip()
        signatures.append({"name": name, "params": params})

    # Match function references in text: `func_name()` or func_name()
    func_ref_pattern = re.compile(r"`(\w+)\s*\([^)]*\)`")
    for m in func_ref_pattern.finditer(content):
        name = m.group(1)
        if name not in [s["name"] for s in signatures]:
            signatures.append({"name": name, "params": ""})

    return signatures


def extract_source_signatures(project_path):
    """Extract function/method signatures from Python source files."""
    src_dirs = [
        os.path.join(project_path, "artifacts", "src"),
        os.path.join(project_path, "artifacts"),
        os.path.join(project_path, "src"),
    ]

    signatures = {}
    for sd in src_dirs:
        if not os.path.isdir(sd):
            continue
        for root, _dirs, files in os.walk(sd):
            if "__pycache__" in root or "test" in os.path.basename(root).lower():
                continue
            for f in files:
                if not f.endswith(".py") or f.startswith("test_"):
                    continue
                fpath = os.path.join(root, f)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
                        source = fh.read()
                    tree = ast.parse(source, filename=fpath)
                except (SyntaxError, OSError):
                    continue

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        params = []
                        for arg in node.args.args:
                            params.append(arg.arg)
                        signatures[node.name] = {
                            "params": params,
                            "file": os.path.relpath(fpath, project_path)
                        }

    return signatures


def main():
    if len(sys.argv) < 2:
        print("Usage: check_o1_6.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    evidence = []
    all_pass = True

    changes_dir = os.path.join(spec_root, "runtime", "openspec", "changes")

    # Collect all spec signatures
    spec_sigs = []
    if os.path.isdir(changes_dir):
        for feature in sorted(os.listdir(changes_dir)):
            feature_path = os.path.join(changes_dir, feature)
            if not os.path.isdir(feature_path):
                continue
            bspec = os.path.join(feature_path, "behavior_spec.md")
            sigs = extract_spec_signatures(bspec)
            for s in sigs:
                s["feature"] = feature
            spec_sigs.extend(sigs)

    source_sigs = extract_source_signatures(project_path)

    if not spec_sigs:
        evidence.append({
            "type": "file_timestamp",
            "path": "behavior_spec",
            "detail": "No API signatures found in behavior specs (cannot verify contracts)"
        })
        # Vacuously true if no contracts are specified
        result = {
            "question": "o1.6",
            "answer": "yes",
            "evidence": evidence
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    if not source_sigs:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": "src/",
            "detail": "No source functions found to match against spec signatures"
        })
        result = {
            "question": "o1.6",
            "answer": "no",
            "evidence": evidence
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    matched = 0
    missing = []

    for sig in spec_sigs:
        name = sig["name"]
        if name in source_sigs:
            matched += 1
        else:
            missing.append(f"{sig.get('feature', '?')}: {name}()")

    evidence.append({
        "type": "file_timestamp",
        "path": "behavior_spec",
        "detail": (
            f"Spec defines {len(spec_sigs)} API signature(s); "
            f"{matched} found in source, {len(missing)} missing"
        )
    })

    if missing:
        coverage_ratio = matched / len(spec_sigs) if spec_sigs else 0
        if coverage_ratio < 0.7:
            all_pass = False
        shown = missing[:10]
        evidence.append({
            "type": "file_timestamp",
            "path": "src/",
            "detail": (
                f"Missing implementations: {'; '.join(shown)}"
                + (f" ... and {len(missing) - 10} more" if len(missing) > 10 else "")
            )
        })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": "src/",
            "detail": "All spec API signatures found in source -- OK"
        })

    result = {
        "question": "o1.6",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
