#!/usr/bin/env python3
"""Check o2.3: Are there zero trivially passing tests (e.g., assert True)?

Parses test files with the ast module and checks that assert statements
are not trivially true (assert True, assert 1, assert "string", etc.).
"""

import ast
import os
import sys
import yaml


class TrivialAssertChecker(ast.NodeVisitor):
    """AST visitor that detects trivially passing assertions."""

    def __init__(self):
        self.trivial = []
        self.total_asserts = 0

    def visit_Assert(self, node):
        self.total_asserts += 1
        test = node.test

        # assert True
        if isinstance(test, ast.Constant) and test.value in (True, 1):
            self.trivial.append(("assert True/1", node.lineno))

        # assert "string" (any non-empty string is truthy)
        elif isinstance(test, ast.Constant) and isinstance(test.value, str) and test.value:
            self.trivial.append((f'assert "{test.value[:20]}"', node.lineno))

        # assert not False, assert not None
        elif isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
            if isinstance(test.operand, ast.Constant) and test.operand.value in (False, None, 0):
                self.trivial.append(("assert not False/None/0", node.lineno))

        self.generic_visit(node)

    def visit_Expr(self, node):
        """Check for method-style trivial assertions like self.assertTrue(True)."""
        if isinstance(node.value, ast.Call):
            func = node.value
            func_name = ""
            if isinstance(func.func, ast.Attribute):
                func_name = func.func.attr
            elif isinstance(func.func, ast.Name):
                func_name = func.func.id

            if func_name == "assertTrue" and func.args:
                arg = func.args[0]
                if isinstance(arg, ast.Constant) and arg.value in (True, 1):
                    self.trivial.append(("assertTrue(True)", node.lineno))
                    self.total_asserts += 1

            elif func_name == "assertFalse" and func.args:
                arg = func.args[0]
                if isinstance(arg, ast.Constant) and arg.value in (False, 0, None):
                    self.trivial.append(("assertFalse(False)", node.lineno))
                    self.total_asserts += 1

            elif func_name == "assertEqual" and len(func.args) >= 2:
                # assertEqual(x, x) where both are the same constant
                a, b = func.args[0], func.args[1]
                if (isinstance(a, ast.Constant) and isinstance(b, ast.Constant)
                        and a.value == b.value):
                    self.trivial.append((f"assertEqual({a.value!r}, {b.value!r})", node.lineno))
                    self.total_asserts += 1

            elif func_name in ("assertTrue", "assertFalse", "assertEqual",
                               "assertNotEqual", "assertIn", "assertNotIn",
                               "assertIs", "assertIsNot", "assertIsNone",
                               "assertIsNotNone", "assertRaises", "assertGreater",
                               "assertLess"):
                self.total_asserts += 1

        self.generic_visit(node)


def check_test_file(filepath):
    """Check a test file for trivially passing assertions."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except OSError:
        return [], 0

    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return [], 0

    checker = TrivialAssertChecker()
    checker.visit(tree)
    return checker.trivial, checker.total_asserts


def main():
    if len(sys.argv) < 2:
        print("Usage: check_o2_3.py <project_path>", file=sys.stderr)
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
            "question": "o2.3",
            "answer": "no",
            "evidence": [{
                "type": "file_timestamp",
                "path": "tests/",
                "detail": "No test files found"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    total_trivial = 0
    trivial_details = []
    total_asserts = 0

    for tf in test_files:
        rel_path = os.path.relpath(tf, project_path)
        trivials, asserts = check_test_file(tf)
        total_asserts += asserts
        total_trivial += len(trivials)
        for desc, lineno in trivials:
            trivial_details.append(f"{rel_path}:{lineno} -- {desc}")

    if total_trivial > 0:
        all_pass = False
        evidence.append({
            "type": "file_timestamp",
            "path": "tests/",
            "detail": (
                f"Found {total_trivial} trivially passing assertion(s) "
                f"across {len(test_files)} test file(s)"
            )
        })
        shown = trivial_details[:10]
        evidence.append({
            "type": "file_timestamp",
            "path": "tests/",
            "detail": "Trivial assertions: " + "; ".join(shown)
        })
    else:
        evidence.append({
            "type": "file_timestamp",
            "path": "tests/",
            "detail": (
                f"Checked {len(test_files)} test file(s) with {total_asserts} assertion(s); "
                f"zero trivially passing assertions found -- OK"
            )
        })

    result = {
        "question": "o2.3",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
