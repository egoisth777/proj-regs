#!/usr/bin/env python3
"""Cookiecutter post-generation hook.

Runs after the project tree is populated. Regenerates INDEX.yaml from
frontmatter and marks shell scripts executable on POSIX systems.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    project_root = Path.cwd().resolve()
    omne_dir = project_root / ".omne"
    if not omne_dir.is_dir():
        print(f"post_gen_project.py: .omne/ not found at {omne_dir}", file=sys.stderr)
        return 1

    # Regenerate INDEX.yaml from frontmatter.
    build_index = omne_dir / "scripts" / "build_index.py"
    if build_index.is_file():
        result = subprocess.run(
            [sys.executable, str(build_index)],
            cwd=str(omne_dir),
            check=False,
        )
        if result.returncode != 0:
            print("post_gen_project.py: build_index.py failed", file=sys.stderr)
            return result.returncode

    # Make shell scripts executable on POSIX.
    if os.name == "posix":
        scripts_dir = omne_dir / "scripts"
        for sh in scripts_dir.glob("*.sh"):
            sh.chmod(0o755)

    print(f"omne SSOT skeleton ready at {project_root.name}/.omne/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
