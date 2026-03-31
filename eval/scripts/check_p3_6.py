#!/usr/bin/env python3
"""Check p3.6: Did no agent idle (dispatched but produce no output)?

Checks all tasks in tasks.md for completion markers.  Any task that
appears dispatched but has no completion indicator is flagged as idle.
"""

import os
import re
import sys
import yaml


def parse_tasks(filepath):
    """Parse a tasks.md file for dispatched tasks and their completion status.

    Returns (total_tasks, completed_tasks, idle_tasks_detail).
    """
    if not os.path.isfile(filepath):
        return 0, 0, []

    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError:
        return 0, 0, []

    total = 0
    completed = 0
    idle = []

    # Pattern: checkbox items like - [x] or - [ ] with task description
    checkbox_pattern = re.compile(r"^\s*[-*]\s+\[([ xX])\]\s+(.+)", re.MULTILINE)
    for m in checkbox_pattern.finditer(content):
        total += 1
        status = m.group(1).strip().lower()
        desc = m.group(2).strip()
        if status == "x":
            completed += 1
        else:
            idle.append(desc[:80])

    # If no checkbox pattern found, look for status-based task lists
    if total == 0:
        # Look for table rows or lines with status indicators
        status_pattern = re.compile(
            r"(?:complete|done|finished|merged|delivered|closed)",
            re.IGNORECASE
        )
        pending_pattern = re.compile(
            r"(?:pending|in[_\s-]?progress|dispatched|assigned|started|blocked|waiting)",
            re.IGNORECASE
        )

        # Lines that are clearly status field declarations (e.g. **Status:** complete)
        status_field_pattern = re.compile(
            r"^\*{0,2}Status:?\*{0,2}\s+",
            re.IGNORECASE
        )

        lines = content.splitlines()
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith("#"):
                continue
            # Skip HTML comments and template placeholder lines
            if "<!--" in line_stripped:
                continue
            # Skip lines showing status options as template placeholders
            if re.search(r"pending\s*\|\s*in-progress\s*\|\s*complete", line_stripped):
                continue

            # Only count lines that look like actual status fields, not descriptions
            is_status_field = bool(status_field_pattern.match(line_stripped))

            has_done = bool(status_pattern.search(line_stripped))
            has_pending = bool(pending_pattern.search(line_stripped))

            if is_status_field:
                if has_done:
                    total += 1
                    completed += 1
                elif has_pending:
                    total += 1
                    idle.append(line_stripped[:80])
            elif has_done and not has_pending:
                total += 1
                completed += 1

    return total, completed, idle


def main():
    if len(sys.argv) < 2:
        print("Usage: check_p3_6.py <project_path>", file=sys.stderr)
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
            "question": "p3.6",
            "answer": "no",
            "evidence": evidence
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    grand_total = 0
    grand_completed = 0
    grand_idle = []

    for tf in tasks_files:
        rel_path = os.path.relpath(tf, project_path)
        total, completed, idle = parse_tasks(tf)
        grand_total += total
        grand_completed += completed
        grand_idle.extend(idle)

        evidence.append({
            "type": "file_timestamp",
            "path": rel_path,
            "detail": (
                f"{completed}/{total} task(s) completed"
                + (f"; {len(idle)} idle/pending" if idle else "")
            )
        })

    if grand_total == 0:
        evidence.append({
            "type": "file_timestamp",
            "path": spec_root,
            "detail": "No parseable tasks found in tasks.md files"
        })
        all_pass = False
    elif grand_idle:
        all_pass = False
        shown = grand_idle[:5]
        evidence.append({
            "type": "file_timestamp",
            "path": spec_root,
            "detail": (
                f"{len(grand_idle)} task(s) dispatched but not completed: "
                f"{'; '.join(shown)}"
                + (f" ... and {len(grand_idle) - 5} more" if len(grand_idle) > 5 else "")
            )
        })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": spec_root,
            "detail": f"All {grand_total} task(s) completed -- no idle agents"
        })

    result = {
        "question": "p3.6",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
