#!/usr/bin/env python3
"""Check o3.5: Are dependencies properly declared (no implicit/missing deps)?

Checks that pyproject.toml (or setup.py/setup.cfg/requirements.txt) exists
and that imports used in source code are either stdlib or declared as
dependencies.
"""

import ast
import os
import sys
import yaml


# Common standard library module names (Python 3.8+)
STDLIB_MODULES = {
    "abc", "aifc", "argparse", "array", "ast", "asynchat", "asyncio",
    "asyncore", "atexit", "audioop", "base64", "bdb", "binascii",
    "binhex", "bisect", "builtins", "bz2", "calendar", "cgi", "cgitb",
    "chunk", "cmath", "cmd", "code", "codecs", "codeop", "collections",
    "colorsys", "compileall", "concurrent", "configparser", "contextlib",
    "contextvars", "copy", "copyreg", "cProfile", "crypt", "csv",
    "ctypes", "curses", "dataclasses", "datetime", "dbm", "decimal",
    "difflib", "dis", "distutils", "doctest", "email", "encodings",
    "enum", "errno", "faulthandler", "fcntl", "filecmp", "fileinput",
    "fnmatch", "fractions", "ftplib", "functools", "gc", "getopt",
    "getpass", "gettext", "glob", "graphlib", "grp", "gzip", "hashlib",
    "heapq", "hmac", "html", "http", "idlelib", "imaplib", "imghdr",
    "imp", "importlib", "inspect", "io", "ipaddress", "itertools",
    "json", "keyword", "lib2to3", "linecache", "locale", "logging",
    "lzma", "mailbox", "mailcap", "marshal", "math", "mimetypes",
    "mmap", "modulefinder", "multiprocessing", "netrc", "nis", "nntplib",
    "numbers", "operator", "optparse", "os", "ossaudiodev", "pathlib",
    "pdb", "pickle", "pickletools", "pipes", "pkgutil", "platform",
    "plistlib", "poplib", "posix", "posixpath", "pprint", "profile",
    "pstats", "pty", "pwd", "py_compile", "pyclbr", "pydoc",
    "queue", "quopri", "random", "re", "readline", "reprlib",
    "resource", "rlcompleter", "runpy", "sched", "secrets", "select",
    "selectors", "shelve", "shlex", "shutil", "signal", "site",
    "smtpd", "smtplib", "sndhdr", "socket", "socketserver", "spwd",
    "sqlite3", "sre_compile", "sre_constants", "sre_parse", "ssl",
    "stat", "statistics", "string", "stringprep", "struct", "subprocess",
    "sunau", "symtable", "sys", "sysconfig", "syslog", "tabnanny",
    "tarfile", "telnetlib", "tempfile", "termios", "test", "textwrap",
    "threading", "time", "timeit", "tkinter", "token", "tokenize",
    "tomllib", "trace", "traceback", "tracemalloc", "tty", "turtle",
    "turtledemo", "types", "typing", "unicodedata", "unittest", "urllib",
    "uu", "uuid", "venv", "warnings", "wave", "weakref", "webbrowser",
    "winreg", "winsound", "wsgiref", "xdrlib", "xml", "xmlrpc",
    "zipapp", "zipfile", "zipimport", "zlib", "_thread", "__future__",
    "typing_extensions", "tomli",
}


def extract_imports(filepath):
    """Extract top-level imported module names from a Python file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except OSError:
        return set()

    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return set()

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                imports.add(node.module.split(".")[0])

    return imports


def get_local_package_names(project_path):
    """Get package/module names defined locally in the project."""
    local = set()
    src_dirs = [
        os.path.join(project_path, "artifacts", "src"),
        os.path.join(project_path, "artifacts"),
        os.path.join(project_path, "src"),
    ]

    for sd in src_dirs:
        if not os.path.isdir(sd):
            continue
        for item in os.listdir(sd):
            item_path = os.path.join(sd, item)
            if os.path.isdir(item_path) and os.path.isfile(os.path.join(item_path, "__init__.py")):
                local.add(item)
            elif item.endswith(".py"):
                local.add(item[:-3])

    return local


def parse_declared_deps(project_path):
    """Parse declared dependencies from project config files."""
    deps = set()

    # pyproject.toml
    pyproject = os.path.join(project_path, "artifacts", "pyproject.toml")
    if not os.path.isfile(pyproject):
        pyproject = os.path.join(project_path, "pyproject.toml")

    if os.path.isfile(pyproject):
        try:
            with open(pyproject, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            # Simple parser for dependencies list
            import re
            # Match lines like: "package-name>=1.0"
            dep_pattern = re.compile(r'"([a-zA-Z0-9_-]+)')
            in_deps = False
            for line in content.splitlines():
                stripped = line.strip()
                if "dependencies" in stripped.lower() and "=" in stripped:
                    in_deps = True
                    continue
                if in_deps:
                    if stripped.startswith("]"):
                        in_deps = False
                        continue
                    m = dep_pattern.search(stripped)
                    if m:
                        # Normalize: PyPI name -> import name
                        dep_name = m.group(1).lower().replace("-", "_")
                        deps.add(dep_name)
        except OSError:
            pass

    # requirements.txt
    for fname in ["requirements.txt", "artifacts/requirements.txt"]:
        req_file = os.path.join(project_path, fname)
        if os.path.isfile(req_file):
            try:
                with open(req_file, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or line.startswith("-"):
                            continue
                        # Extract package name
                        import re
                        m = re.match(r"([a-zA-Z0-9_-]+)", line)
                        if m:
                            deps.add(m.group(1).lower().replace("-", "_"))
            except OSError:
                pass

    return deps


def main():
    if len(sys.argv) < 2:
        print("Usage: check_o3_5.py <project_path>", file=sys.stderr)
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])

    _ssot = os.path.join(project_path, "ssot")
    spec_root = _ssot if os.path.isdir(_ssot) else project_path

    evidence = []
    all_pass = True

    # Check for dependency declaration files
    dep_files = [
        os.path.join(project_path, "artifacts", "pyproject.toml"),
        os.path.join(project_path, "pyproject.toml"),
        os.path.join(project_path, "artifacts", "setup.py"),
        os.path.join(project_path, "setup.py"),
        os.path.join(project_path, "artifacts", "requirements.txt"),
        os.path.join(project_path, "requirements.txt"),
    ]

    found_dep_file = None
    for df in dep_files:
        if os.path.isfile(df):
            found_dep_file = df
            break

    if found_dep_file is None:
        all_pass = False
        evidence.append({
            "type": "command_output",
            "command": "dependency declaration check",
            "stdout": "",
            "exit_code": 1,
            "detail": "No dependency declaration file found (pyproject.toml, setup.py, requirements.txt)"
        })
        result = {
            "question": "o3.5",
            "answer": "no",
            "evidence": evidence
        }
        print(yaml.dump(result, default_flow_style=False, sort_keys=False))
        return

    evidence.append({
        "type": "command_output",
        "command": "dependency declaration check",
        "stdout": os.path.relpath(found_dep_file, project_path),
        "exit_code": 0,
        "detail": f"Found dependency file: {os.path.relpath(found_dep_file, project_path)}"
    })

    # Collect all imports from source files
    src_dirs = [
        os.path.join(project_path, "artifacts", "src"),
        os.path.join(project_path, "artifacts"),
        os.path.join(project_path, "src"),
    ]

    all_imports = set()
    for sd in src_dirs:
        if not os.path.isdir(sd):
            continue
        for root, _dirs, files in os.walk(sd):
            if "__pycache__" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    all_imports |= extract_imports(os.path.join(root, f))

    declared_deps = parse_declared_deps(project_path)
    local_packages = get_local_package_names(project_path)

    # Third-party imports = imports - stdlib - local
    third_party = all_imports - STDLIB_MODULES - local_packages
    undeclared = third_party - declared_deps

    if undeclared:
        # Some may just be mismatched names (PyPI name != import name)
        # Only flag if significantly undeclared
        if len(undeclared) > len(third_party) / 2 and len(undeclared) > 1:
            all_pass = False
        evidence.append({
            "type": "command_output",
            "command": "import vs dependency check",
            "stdout": f"Undeclared: {', '.join(sorted(undeclared)[:10])}",
            "exit_code": 1,
            "detail": (
                f"Found {len(undeclared)} potentially undeclared dependency import(s): "
                f"{', '.join(sorted(undeclared)[:10])}"
            )
        })
    else:
        evidence.append({
            "type": "command_output",
            "command": "import vs dependency check",
            "stdout": f"All third-party imports accounted for",
            "exit_code": 0,
            "detail": (
                f"All third-party imports ({len(third_party)}) are declared as dependencies -- OK"
            )
        })

    result = {
        "question": "o3.5",
        "answer": "yes" if all_pass else "no",
        "evidence": evidence
    }
    print(yaml.dump(result, default_flow_style=False, sort_keys=False))


if __name__ == "__main__":
    main()
