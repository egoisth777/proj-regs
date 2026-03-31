#!/usr/bin/env python3
"""Check o3.4: Is there no duplicated logic beyond a trivial threshold?

Simple heuristic: checks that no two functions in the project share more
than 5 consecutive identical non-blank lines of code.
"""

import os
import re
import sys
import yaml


MIN_DUPLICATE_LINES = 5

# Lines that are trivial / boilerplate and should not count toward duplication
_TRIVIAL_LINE_RE = re.compile(
    r"^("
    r"[\[\]\{\}\(\),.:;]+"          # pure punctuation (braces, brackets, etc.)
    r"|pass"
    r"|return"
    r"|return\s+None"
    r"|else:"
    r"|try:"
    r"|except.*:"
    r"|finally:"
    r"|\"\"\".*\"\"\""              # single-line docstrings
    r"|\'\'\'.*\'\'\'"
    r"|#.*"                         # comment-only lines
    r"|(from|import)\s+.*"          # import lines
    r")$"
)


def _is_trivial(line: str) -> bool:
    """Return True if a stripped source line is trivial boilerplate."""
    return bool(_TRIVIAL_LINE_RE.match(line))


def extract_function_blocks(filepath):
    """Extract function bodies as lists of stripped non-trivial lines, keyed by name."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except OSError:
        return {}

    functions = {}
    current_func = None
    current_lines = []
    current_indent = 0

    for i, line in enumerate(lines):
        stripped = line.rstrip()

        # Detect function definition
        lstripped = line.lstrip()
        if lstripped.startswith("def ") or lstripped.startswith("async def "):
            # Save previous function
            if current_func and current_lines:
                functions[current_func] = current_lines

            # Extract function name
            parts = lstripped.split("(")[0]
            name = parts.replace("async ", "").replace("def ", "").strip()
            current_func = f"{os.path.basename(filepath)}:{name}"
            current_lines = []
            current_indent = len(line) - len(lstripped)
        elif current_func:
            # Check if we're still inside the function
            if stripped and (len(line) - len(lstripped) <= current_indent) and not lstripped.startswith("#"):
                # Dedented to same or less level, function ended
                if current_lines:
                    functions[current_func] = current_lines
                current_func = None
                current_lines = []
            else:
                # Still in function body -- keep only non-blank, non-trivial lines
                if stripped and not _is_trivial(lstripped):
                    current_lines.append(lstripped)

    # Save last function
    if current_func and current_lines:
        functions[current_func] = current_lines

    return functions


def find_consecutive_duplicates(blocks, threshold):
    """Find pairs of functions that share >=threshold consecutive identical lines."""
    duplicates = []
    func_names = list(blocks.keys())

    for i in range(len(func_names)):
        for j in range(i + 1, len(func_names)):
            lines_a = blocks[func_names[i]]
            lines_b = blocks[func_names[j]]

            # Simple O(n*m) check for consecutive matches
            max_consecutive = 0
            for ai in range(len(lines_a)):
                for bi in range(len(lines_b)):
                    count = 0
                    while (ai + count < len(lines_a) and
                           bi + count < len(lines_b) and
                           lines_a[ai + count] == lines_b[bi + count]):
                        count += 1
                    if count > max_consecutive:
                        max_consecutive = count

            if max_consecutive >= threshold:
                duplicates.append((
                    func_names[i], func_names[j], max_consecutive
                ))

    return duplicates


def main():
    if len(sys.argv) < 2:
        print("Usage: check_o3_4.py <project_path>", file=sys.stderr)
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

    all_blocks = {}
    py_count = 0
    for sd in src_dirs:
        if not os.path.isdir(sd):
            continue
        for root, _dirs, files in os.walk(sd):
            if "__pycache__" in root:
                continue
            basename = os.path.basename(root)
            if basename in ("tests", "test"):
                continue
            for f in files:
                if f.endswith(".py") and not f.startswith("test_") and f != "conftest.py":
                    fp = os.path.join(root, f)
                    blocks = extract_function_blocks(fp)
                    all_blocks.update(blocks)
                    py_count += 1

    if py_count == 0:
        result = {
            "question": "o3.4",
            "answer": "no",
            "evidence": [{
                "type": "command_output",
                "command": "duplication check",
                "stdout": "",
                "exit_code": -1,
                "detail": "No Python source files found"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    if len(all_blocks) < 2:
        evidence.append({
            "type": "command_output",
            "command": f"duplication check ({py_count} files, {len(all_blocks)} functions)",
            "stdout": "Fewer than 2 functions -- no duplication possible",
            "exit_code": 0,
            "detail": "Too few functions to check for duplication"
        })
        result = {
            "question": "o3.4",
            "answer": "yes",
            "evidence": evidence
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    duplicates = find_consecutive_duplicates(all_blocks, MIN_DUPLICATE_LINES)

    if duplicates:
        all_pass = False
        dup_details = []
        for a, b, count in duplicates[:10]:
            dup_details.append(f"{a} <-> {b}: {count} consecutive identical lines")

        evidence.append({
            "type": "command_output",
            "command": f"duplication check ({py_count} files, {len(all_blocks)} functions)",
            "stdout": "\n".join(dup_details),
            "exit_code": 1,
            "detail": (
                f"Found {len(duplicates)} pair(s) of functions with "
                f">= {MIN_DUPLICATE_LINES} consecutive identical lines"
            )
        })
    else:
        evidence.append({
            "type": "command_output",
            "command": f"duplication check ({py_count} files, {len(all_blocks)} functions)",
            "stdout": "No significant duplication found",
            "exit_code": 0,
            "detail": (
                f"Checked {len(all_blocks)} function(s) across {py_count} file(s); "
                f"no pair shares >= {MIN_DUPLICATE_LINES} consecutive identical lines -- OK"
            )
        })

    result = {
        "question": "o3.4",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
