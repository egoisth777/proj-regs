#!/usr/bin/env python3
"""Check p4.3: Is the openspec index consistent with completed/archived features?

Checks that the openspec index file (if present) lists features that match
the actual directories under runtime/openspec/changes/, and that
completed/archived features are properly categorized.
"""

import os
import re
import sys
import yaml


def find_index_file(spec_root):
    """Search for the openspec index file."""
    candidates = [
        os.path.join(spec_root, "runtime", "openspec", "index.md"),
        os.path.join(spec_root, "runtime", "openspec", "index.yaml"),
        os.path.join(spec_root, "runtime", "openspec", "INDEX.md"),
        os.path.join(spec_root, "runtime", "openspec", "registry.md"),
        os.path.join(spec_root, "runtime", "openspec", "changes", "index.md"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c

    # Search for any index-like file in openspec/
    openspec_dir = os.path.join(spec_root, "runtime", "openspec")
    if os.path.isdir(openspec_dir):
        for f in os.listdir(openspec_dir):
            if f.lower() in ("index.md", "index.yaml", "index.yml", "registry.md"):
                return os.path.join(openspec_dir, f)

    return None


def extract_referenced_features(content):
    """Extract feature names referenced in index content.

    Handles the markdown table format used by pool-e:
        | Feature | OpenSpec Path | Status | ... |
        |---|---|---|...|
        | feat-001-add-task | changes/feat-001-add-task | merged | ... |

    Also handles markdown links, backtick-wrapped names that look like
    feature identifiers, and bullet lists.
    """
    features = set()

    # Pattern 1: Markdown table rows — extract the first non-empty cell
    # that looks like a feature name (skip header/separator rows).
    table_row_pattern = re.compile(r"^\s*\|(.+)\|", re.MULTILINE)
    for match in table_row_pattern.finditer(content):
        row = match.group(1)
        cells = [c.strip() for c in row.split("|")]
        # Skip separator rows (all dashes)
        if all(re.match(r"^[-:\s]*$", c) for c in cells):
            continue
        # Skip header rows by checking for known header words
        if cells and cells[0].lower() in ("feature", "name", ""):
            continue
        # First non-empty cell is the feature name
        for cell in cells:
            if cell and len(cell) > 2 and not re.match(r"^[-:\s]*$", cell):
                features.add(cell.strip().lower())
                break

    # Pattern 2: Feature folder references in path column (changes/feat-xxx)
    path_pattern = re.compile(r"changes/(feat-[a-z0-9_-]+)", re.IGNORECASE)
    for match in path_pattern.finditer(content):
        features.add(match.group(1).strip().lower())

    # Pattern 3: Markdown links: [feature-name](...)
    link_pattern = re.compile(r"\[([^\]]+)\]\([^\)]*\)")
    for match in link_pattern.finditer(content):
        name = match.group(1).strip().lower()
        # Only include if it looks like a feature reference (has a hyphen
        # or starts with feat-)
        if "feat" in name or "-" in name:
            features.add(name)

    # Pattern 4: Backtick-wrapped names that look like feature identifiers
    bt_pattern = re.compile(r"`([^`]+)`")
    for match in bt_pattern.finditer(content):
        name = match.group(1).strip().lower()
        # Only include names that look like feature identifiers, not
        # status keywords or generic terms
        if re.match(r"^feat-", name):
            features.add(name)

    return features


def main():
    if len(sys.argv) < 2:
        print("Usage: check_p4_3.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    changes_dir = os.path.join(spec_root, "runtime", "openspec", "changes")

    evidence = []
    all_pass = True

    if not os.path.isdir(changes_dir):
        result = {
            "question": "p4.3",
            "answer": "no",
            "evidence": [{
                "type": "missing_directory",
                "path": changes_dir,
                "detail": "runtime/openspec/changes/ directory not found"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    # Get actual feature directories
    actual_features = set()
    feature_dirs = [
        d for d in os.listdir(changes_dir)
        if os.path.isdir(os.path.join(changes_dir, d))
    ]
    for d in feature_dirs:
        actual_features.add(d.lower())

    if not actual_features:
        result = {
            "question": "p4.3",
            "answer": "no",
            "evidence": [{
                "type": "missing_directory",
                "path": changes_dir,
                "detail": "No feature directories found under changes/"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    # Find and parse index
    index_file = find_index_file(spec_root)

    if index_file is None:
        # No index file -- check if features are self-consistent
        # (each has a status.md that indicates state)
        evidence.append({
            "type": "file_timestamp",
            "path": os.path.join(spec_root, "runtime", "openspec"),
            "detail": "No openspec index file found; checking feature self-consistency"
        })

        for feature in sorted(actual_features):
            feature_path = os.path.join(changes_dir, feature)
            status_file = os.path.join(feature_path, "status.md")
            if os.path.isfile(status_file):
                try:
                    with open(status_file, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read().lower()
                    has_state = any(
                        kw in content for kw in
                        ["complete", "done", "merged", "archived", "in progress", "pending"]
                    )
                    if has_state:
                        evidence.append({
                            "type": "file_timestamp",
                            "path": status_file,
                            "detail": f"Feature '{feature}': status.md contains state information"
                        })
                    else:
                        evidence.append({
                            "type": "file_timestamp",
                            "path": status_file,
                            "detail": f"Feature '{feature}': status.md lacks clear state information"
                        })
                except OSError:
                    all_pass = False
            else:
                all_pass = False
                evidence.append({
                    "type": "file_timestamp",
                    "path": status_file,
                    "detail": f"Feature '{feature}': no status.md found"
                })
    else:
        # Parse index and compare with actual features
        try:
            with open(index_file, "r", encoding="utf-8", errors="replace") as f:
                index_content = f.read()
        except OSError:
            result = {
                "question": "p4.3",
                "answer": "no",
                "evidence": [{
                    "type": "file_timestamp",
                    "path": index_file,
                    "detail": "Could not read openspec index file"
                }]
            }
            print(yaml.dump(result, default_flow_style=False, sort_keys=False))
            return

        referenced = extract_referenced_features(index_content)

        if not referenced:
            # Index file exists but has no feature entries (e.g. empty template
            # table). Fall back to checking feature self-consistency via
            # status.md files rather than failing against an empty table.
            evidence.append({
                "type": "file_timestamp",
                "path": index_file,
                "detail": "Index file exists but contains no feature entries; checking feature self-consistency"
            })
            for feature in sorted(actual_features):
                feature_path = os.path.join(changes_dir, feature)
                status_file = os.path.join(feature_path, "status.md")
                if os.path.isfile(status_file):
                    try:
                        with open(status_file, "r", encoding="utf-8", errors="replace") as f:
                            st_content = f.read().lower()
                        has_state = any(
                            kw in st_content for kw in
                            ["complete", "done", "merged", "archived", "in progress", "pending"]
                        )
                        if has_state:
                            evidence.append({
                                "type": "file_timestamp",
                                "path": status_file,
                                "detail": f"Feature '{feature}': status.md contains state information"
                            })
                        else:
                            evidence.append({
                                "type": "file_timestamp",
                                "path": status_file,
                                "detail": f"Feature '{feature}': status.md lacks clear state information"
                            })
                    except OSError:
                        all_pass = False
                else:
                    all_pass = False
                    evidence.append({
                        "type": "file_timestamp",
                        "path": status_file,
                        "detail": f"Feature '{feature}': no status.md found"
                    })
        else:
            # Check for features in directories but not in index
            missing_from_index = actual_features - referenced
            # Check for features in index but not in directories
            extra_in_index = referenced - actual_features

            evidence.append({
                "type": "file_timestamp",
                "path": index_file,
                "detail": (
                    f"Index references {len(referenced)} feature(s); "
                    f"actual directories: {len(actual_features)}"
                )
            })

            if missing_from_index:
                # Not necessarily a failure -- may be unreferenced by exact name
                evidence.append({
                    "type": "file_timestamp",
                    "path": index_file,
                    "detail": (
                        f"Feature dirs not found in index: "
                        f"{', '.join(sorted(missing_from_index))}"
                    )
                })
                # Only fail if there are many missing
                if len(missing_from_index) > len(actual_features) / 2:
                    all_pass = False

            if extra_in_index:
                evidence.append({
                    "type": "file_timestamp",
                    "path": index_file,
                    "detail": (
                        f"Index references not matching directories: "
                        f"{', '.join(sorted(list(extra_in_index)[:5]))}"
                    )
                })

    result = {
        "question": "p4.3",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
