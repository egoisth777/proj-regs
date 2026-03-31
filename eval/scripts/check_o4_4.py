#!/usr/bin/env python3
"""Check o4.4: Do function/class names align with terminology used in the spec?

Extracts key terms from behavior_spec.md files and checks that they appear
in function/class names in the source code.
"""

import ast
import os
import re
import sys
import yaml


def extract_spec_terms(behavior_spec_path):
    """Extract significant terms from a behavior_spec.md file."""
    if not os.path.isfile(behavior_spec_path):
        return set()

    try:
        with open(behavior_spec_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError:
        return set()

    # Extract words that appear in headers, code blocks, and emphasized text
    terms = set()

    # Words from headers
    header_pattern = re.compile(r"^#+\s+(.+)", re.MULTILINE)
    for m in header_pattern.finditer(content):
        words = re.findall(r"[a-z]{3,}", m.group(1).lower())
        terms.update(words)

    # Words from code blocks (backtick-quoted)
    code_pattern = re.compile(r"`([^`]+)`")
    for m in code_pattern.finditer(content):
        words = re.findall(r"[a-z]{3,}", m.group(1).lower())
        terms.update(words)

    # Words from bold/italic text
    emphasis_pattern = re.compile(r"\*\*([^*]+)\*\*|\*([^*]+)\*")
    for m in emphasis_pattern.finditer(content):
        text = m.group(1) or m.group(2)
        words = re.findall(r"[a-z]{3,}", text.lower())
        terms.update(words)

    # Filter out very common/stop words
    stop_words = {
        "the", "and", "for", "are", "but", "not", "you", "all",
        "can", "has", "her", "was", "one", "our", "out", "day",
        "had", "hot", "oil", "sit", "now", "old", "off", "any",
        "its", "let", "say", "she", "too", "use", "way", "who",
        "boy", "did", "get", "him", "his", "how", "man", "new",
        "that", "this", "with", "have", "from", "they", "been",
        "call", "each", "make", "like", "long", "look", "many",
        "some", "them", "then", "when", "will", "more", "also",
        "back", "must", "name", "very", "here", "just", "over",
        "such", "take", "than", "into", "most", "only", "come",
        "should", "would", "could", "shall", "system", "user",
        "given", "when", "then", "spec", "test", "file", "data",
        "following", "example", "description", "behavior", "feature",
        "input", "output", "expected", "result", "return", "value",
        "error", "none", "true", "false", "string", "number",
    }
    terms -= stop_words

    return terms


def extract_source_names(project_path):
    """Extract function and class names from source files."""
    src_dirs = [
        os.path.join(project_path, "artifacts", "src"),
        os.path.join(project_path, "artifacts"),
        os.path.join(project_path, "src"),
    ]

    names = set()
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
                        names.add(node.name.lower())
                        # Also add individual words from snake_case names
                        for part in node.name.lower().split("_"):
                            if len(part) >= 3:
                                names.add(part)
                    elif isinstance(node, ast.ClassDef):
                        names.add(node.name.lower())
                        # Split PascalCase into words
                        parts = re.findall(r"[A-Z][a-z]+|[a-z]+", node.name)
                        for part in parts:
                            if len(part) >= 3:
                                names.add(part.lower())

    return names


def main():
    if len(sys.argv) < 2:
        print("Usage: check_o4_4.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    evidence = []
    all_pass = True

    changes_dir = os.path.join(spec_root, "runtime", "openspec", "changes")

    # Collect spec terms
    all_spec_terms = set()
    if os.path.isdir(changes_dir):
        for feature in sorted(os.listdir(changes_dir)):
            feature_path = os.path.join(changes_dir, feature)
            if not os.path.isdir(feature_path):
                continue
            bspec = os.path.join(feature_path, "behavior_spec.md")
            terms = extract_spec_terms(bspec)
            all_spec_terms |= terms

    source_names = extract_source_names(project_path)

    if not all_spec_terms:
        evidence.append({
            "type": "file_timestamp",
            "path": "behavior_spec",
            "detail": "No significant terms extracted from behavior specs"
        })
        # Vacuously true
        result = {
            "question": "o4.4",
            "answer": "yes",
            "evidence": evidence
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    if not source_names:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": "src/",
            "detail": "No function/class names found in source code"
        })
        result = {
            "question": "o4.4",
            "answer": "no",
            "evidence": evidence
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    matched_terms = all_spec_terms & source_names
    unmatched_terms = all_spec_terms - source_names

    coverage = len(matched_terms) / len(all_spec_terms) if all_spec_terms else 0

    evidence.append({
        "type": "file_timestamp",
        "path": "behavior_spec",
        "detail": (
            f"Extracted {len(all_spec_terms)} spec term(s); "
            f"{len(matched_terms)} found in source ({coverage:.0%})"
        )
    })

    if coverage < 0.3:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": "src/",
            "detail": (
                f"Low terminology alignment ({coverage:.0%}); "
                f"unmatched spec terms: {', '.join(sorted(unmatched_terms)[:15])}"
            )
        })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": "src/",
            "detail": (
                f"Good terminology alignment ({coverage:.0%}); "
                f"matched: {', '.join(sorted(matched_terms)[:10])}"
            )
        })

    result = {
        "question": "o4.4",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
