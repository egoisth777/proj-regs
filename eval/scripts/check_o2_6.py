#!/usr/bin/env python3
"""Check o2.6: Are there no test files with zero assertions?

Parses test files with ast and counts assert statements (both bare assert
and unittest-style self.assert* calls) per file.  Any test file containing
test functions but zero assertions is flagged.
"""

import ast
import os
import re
import sys
import yaml


class AssertCounter(ast.NodeVisitor):
    """AST visitor that counts assertions in a file."""

    def __init__(self):
        self.assert_count = 0
        self.test_func_count = 0

    def visit_Assert(self, node):
        self.assert_count += 1
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        if node.name.startswith("test_"):
            self.test_func_count += 1
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Expr(self, node):
        """Count unittest-style assertions: self.assert*, self.fail, etc."""
        if isinstance(node.value, ast.Call):
            func = node.value.func
            if isinstance(func, ast.Attribute):
                name = func.attr
                if name.startswith("assert") or name in ("fail", "failIf", "failUnless"):
                    self.assert_count += 1
            elif isinstance(func, ast.Name):
                # pytest-style assert helpers or standalone assert functions
                if func.id.startswith("assert"):
                    self.assert_count += 1
        self.generic_visit(node)

    def visit_With(self, node):
        """Count pytest.raises and self.assertRaises used as context managers."""
        for item in node.items:
            if isinstance(item.context_expr, ast.Call):
                func = item.context_expr.func
                func_name = ""
                if isinstance(func, ast.Attribute):
                    func_name = func.attr
                elif isinstance(func, ast.Name):
                    func_name = func.id
                if func_name in ("raises", "assertRaises", "assertWarns"):
                    self.assert_count += 1
        self.generic_visit(node)


def check_test_file(filepath):
    """Check a test file for assertion count."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except OSError:
        return 0, 0

    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return 0, 0

    counter = AssertCounter()
    counter.visit(tree)
    return counter.test_func_count, counter.assert_count


def main():
    if len(sys.argv) < 2:
        print("Usage: check_o2_6.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    evidence = []
    all_pass = True

    test_dirs = [
        os.path.join(project_path, "artifacts", "tests"),
        os.path.join(project_path, "artifacts", "test"),
        os.path.join(project_path, "artifacts"),
        os.path.join(project_path, "tests"),
        os.path.join(project_path, "test"),
    ]

    test_files = []
    for td in test_dirs:
        if not os.path.isdir(td):
            continue
        for root, _dirs, files in os.walk(td):
            for f in files:
                if f.endswith(".py") and (f.startswith("test_") or f.endswith("_test.py")):
                    fp = os.path.join(root, f)
                    if fp not in test_files:
                        test_files.append(fp)

    if not test_files:
        result = {
            "question": "o2.6",
            "answer": "no",
            "evidence": [{
                "type": "file_timestamp",
                "path": "tests/",
                "detail": "No test files found"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    zero_assertion_files = []
    total_assertions = 0

    for tf in test_files:
        rel_path = os.path.relpath(tf, project_path)
        test_count, assert_count = check_test_file(tf)
        total_assertions += assert_count

        if test_count > 0 and assert_count == 0:
            zero_assertion_files.append(f"{rel_path} ({test_count} test(s), 0 assertions)")

    if zero_assertion_files:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": "tests/",
            "detail": (
                f"Found {len(zero_assertion_files)} test file(s) with test functions "
                f"but zero assertions"
            )
        })
        shown = zero_assertion_files[:10]
        evidence.append({
            "type": "file_timestamp",
            "path": "tests/",
            "detail": "Zero-assertion files: " + "; ".join(shown)
        })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": "tests/",
            "detail": (
                f"All {len(test_files)} test file(s) have assertions "
                f"({total_assertions} total) -- OK"
            )
        })

    result = {
        "question": "o2.6",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
