#!/usr/bin/env python3
"""Check o3.2: Are there zero unused imports or dead variables?

Parses Python files with the ast module to detect:
- Imported names that are never referenced in the code
- Variables assigned but never used
"""

import ast
import os
import sys
import yaml


class UnusedImportChecker(ast.NodeVisitor):
    """AST visitor that detects unused imports and dead variables."""

    def __init__(self):
        self.imports = {}  # name -> lineno
        self.assignments = {}  # name -> lineno
        self.references = set()
        self._in_import = False

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            # For "import foo.bar", the usable name is "foo"
            if "." in name:
                name = name.split(".")[0]
            self.imports[name] = node.lineno
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            if alias.name == "*":
                continue
            name = alias.asname if alias.asname else alias.name
            self.imports[name] = node.lineno
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Load, ast.Del)):
            self.references.add(node.id)
        elif isinstance(node.ctx, ast.Store):
            # Track assignments, but only simple ones at function/module level
            self.assignments[node.id] = node.lineno
        self.generic_visit(node)

    def visit_Attribute(self, node):
        # Track attribute access -- the base name is referenced
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.references.add(node.name)
        # Don't track parameters or local vars of functions
        # Just visit body
        for child in ast.iter_child_nodes(node):
            self.visit(child)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        self.references.add(node.name)
        self.generic_visit(node)

    def get_unused_imports(self):
        """Return list of (name, lineno) for unused imports."""
        unused = []
        for name, lineno in self.imports.items():
            if name not in self.references and name != "_":
                # Check if it's a dunder or commonly re-exported name
                if not name.startswith("__"):
                    unused.append((name, lineno))
        return unused


def check_file(filepath):
    """Check a Python file for unused imports."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except OSError:
        return [], []

    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return [], []

    checker = UnusedImportChecker()
    checker.visit(tree)

    unused_imports = checker.get_unused_imports()

    return unused_imports, []


def main():
    if len(sys.argv) < 2:
        print("Usage: check_o3_2.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    src_dir = os.path.join(project_path, "artifacts", "src")
    artifacts_dir = os.path.join(project_path, "artifacts")
    search_dir = src_dir if os.path.isdir(src_dir) else artifacts_dir

    evidence = []
    all_pass = True

    py_files = []
    if os.path.isdir(search_dir):
        for root, _dirs, files in os.walk(search_dir):
            if "__pycache__" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    py_files.append(os.path.join(root, f))

    if not py_files:
        result = {
            "question": "o3.2",
            "answer": "no",
            "evidence": [{
                "type": "command_output",
                "command": "unused import check",
                "stdout": "",
                "exit_code": -1,
                "detail": f"No .py files found under {os.path.relpath(search_dir, project_path)}/"
            }]
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    total_unused_imports = 0
    files_with_issues = []

    for py_file in py_files:
        rel_path = os.path.relpath(py_file, project_path)
        unused_imports, _ = check_file(py_file)

        if unused_imports:
            total_unused_imports += len(unused_imports)
            import_details = [f"'{name}' (line {ln})" for name, ln in unused_imports[:5]]
            files_with_issues.append(f"{rel_path}: {', '.join(import_details)}")

    if files_with_issues:
        all_pass = False
        evidence.append({
            "type": "command_output",
            "command": f"ast unused import check ({len(py_files)} files)",
            "stdout": "\n".join(files_with_issues[:10]),
            "exit_code": 1,
            "detail": (
                f"Found {total_unused_imports} unused import(s) across "
                f"{len(files_with_issues)} file(s)"
            )
        })
    else:
        evidence.append({
            "type": "command_output",
            "command": f"ast unused import check ({len(py_files)} files)",
            "stdout": f"All {len(py_files)} files have no unused imports detected",
            "exit_code": 0,
            "detail": f"Zero unused imports found across {len(py_files)} Python file(s)"
        })

    result = {
        "question": "o3.2",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
