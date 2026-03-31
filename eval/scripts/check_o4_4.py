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

    # Filter out common English stop words, spec-template boilerplate,
    # and generic programming terms that don't convey domain meaning.
    stop_words = {
        # Determiners, pronouns, prepositions, conjunctions
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
        "should", "would", "could", "shall", "may", "might",
        "does", "done", "been", "being", "were", "what", "which",
        "there", "their", "about", "after", "before", "between",
        "during", "through", "until", "upon", "onto", "above",
        "below", "under", "other", "another", "every", "either",
        "neither", "both", "same", "still", "already", "again",
        "once", "twice", "never", "always", "often", "sometimes",
        "where", "while", "because", "since", "although", "though",
        "however", "therefore", "instead", "whether", "without",
        # Common verbs / verb forms
        "added", "adds", "runs", "run", "running", "used", "using",
        "sets", "set", "gets", "got", "got", "gives", "gave",
        "goes", "went", "gone", "sees", "saw", "seen",
        "knows", "knew", "known", "takes", "took", "taken",
        "makes", "made", "finds", "found", "comes", "came",
        "keeps", "kept", "shows", "shown", "tells", "told",
        "says", "said", "puts", "reads", "read", "writes",
        "written", "needs", "want", "wants", "works", "worked",
        "tries", "tried", "starts", "started", "becomes",
        "leaves", "left", "holds", "held", "brings", "brought",
        "begins", "began", "appears", "changes", "changed",
        "follows", "means", "meant", "turns", "turned",
        "creates", "created", "provides", "provided",
        "includes", "included", "contains", "contained",
        "requires", "required", "allows", "allowed",
        "exists", "existed", "remains", "remained",
        "produces", "produced", "received", "receives",
        "indicates", "indicating", "performs", "performed",
        "represents", "represented", "ensures", "ensure",
        "matches", "matching", "matching", "accepting",
        # Adjectives / adverbs
        "first", "last", "next", "previous", "current",
        "valid", "invalid", "correct", "incorrect",
        "empty", "full", "close", "open", "real",
        "same", "different", "specific", "general",
        "exactly", "properly", "correctly", "successfully",
        # Spec-template boilerplate
        "given", "spec", "test", "file", "data",
        "following", "example", "description", "behavior", "feature",
        "input", "output", "expected", "result", "return", "value",
        "error", "none", "true", "false", "string", "number",
        "system", "user", "note", "see", "below",
        "section", "case", "cases", "scenario", "scenarios",
        "step", "steps", "action", "actions", "rule", "rules",
        "approved", "proposal", "produced", "writer",
        "observable", "testable", "format", "uses",
        # Generic programming terms
        "code", "function", "class", "method", "variable",
        "type", "types", "object", "objects", "array", "arrays",
        "list", "dict", "int", "str", "bool", "float",
        "arg", "args", "argument", "arguments", "param", "params",
        "key", "keys", "val", "vals", "config", "configuration",
        "default", "defaults", "option", "options",
        "message", "messages", "path", "paths",
        "print", "prints", "printed", "line", "lines",
        "text", "content", "contents", "body",
        "state", "status", "update", "updates", "updated",
        "check", "checks", "checked",
        "handle", "handles", "handler",
        "write", "writer", "reader",
        "parse", "parser", "parsed",
        "load", "loader", "loaded", "save", "saved",
        "send", "sent", "response", "request",
        "field", "fields", "record", "records",
        # Short / ambiguous words that slip through 3-char minimum
        "abc", "etc", "via", "per", "yet", "ago",
        "end", "top", "low", "high", "mid", "max", "min",
        "add", "del", "put", "pop", "run", "try", "fix",
        "log", "map", "set", "get", "new", "raw",
        "buy", "cut", "bit", "big", "bad", "own",
        "cli", "api", "url", "sql",
        # Misc common words
        "well", "even", "much", "part", "point", "place",
        "time", "year", "week", "month", "hour", "minute",
        "second", "date", "today", "right", "left",
        "good", "best", "better", "great", "large", "small",
        "three", "four", "five", "zero", "single", "double",
        "word", "words", "look", "form", "water", "hand",
        "need", "move", "live", "help", "turn", "play",
        "keep", "think", "thought", "head", "page",
        "letter", "mother", "answer", "food", "world",
        "school", "still", "learn", "plant", "cover",
        "story", "young", "along", "close",
        "enough", "plain", "girl", "usual", "ready",
        "completions", "completing", "completed",
        "archived", "auto", "behaviors", "bug",
        "custom", "directory", "environment", "variable",
        "storage", "persist", "persisted", "persistence",
        "reject", "rejection", "rejected",
        "exist", "existing", "missing", "deleted",
        "parent", "child", "root", "base",
        "actual", "practical", "entire",
        "back", "safe", "atomic", "corrupt", "corrupted",
        "pretty", "human", "readability", "readable",
        "pattern", "choice", "choices", "listing",
        "confirm", "confirmation", "correct", "exit",
        "exits", "instead",
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

    # Use an absolute count threshold: 5+ domain terms found in source = pass.
    # Percentage-based thresholds are unreliable because spec prose contains
    # many terms that won't (and shouldn't) appear as identifiers.
    MIN_MATCHED_TERMS = 5

    evidence.append({
        "type": "file_timestamp",
        "path": "behavior_spec",
        "detail": (
            f"Extracted {len(all_spec_terms)} domain term(s); "
            f"{len(matched_terms)} found in source ({coverage:.0%})"
        )
    })

    if len(matched_terms) < MIN_MATCHED_TERMS:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": "src/",
            "detail": (
                f"Low terminology alignment: only {len(matched_terms)} domain "
                f"term(s) found in source (need >= {MIN_MATCHED_TERMS}); "
                f"unmatched spec terms: {', '.join(sorted(unmatched_terms)[:15])}"
            )
        })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": "src/",
            "detail": (
                f"Good terminology alignment: {len(matched_terms)} domain "
                f"term(s) found in source (>= {MIN_MATCHED_TERMS}); "
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
