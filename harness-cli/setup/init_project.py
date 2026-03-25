"""Setup script: installs MAS Harness hooks and config into a target project."""

import argparse
import json
import os
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).parent
TEMPLATES_DIR = SCRIPT_DIR / "templates"
HARNESS_CLI_DIR = SCRIPT_DIR.parent

GITIGNORE_ENTRIES = [
    "CLAUDE.md",
    "AGENTS.md",
    ".claude/",
    ".harness.json",
]


def validate_inputs(project: Path, registry: Path):
    if not project.exists():
        sys.exit(f"Error: Project directory does not exist: {project}")
    if not (project / ".git").exists():
        sys.exit(f"Error: Project is not a git repository: {project}")
    if not registry.exists():
        sys.exit(f"Error: Registry directory does not exist: {registry}")
    if not (registry / "context_map.json").exists():
        sys.exit(f"Error: Registry missing context_map.json: {registry}")


def create_harness_json(project: Path, registry: Path):
    config = {
        "registry_path": str(registry.resolve()),
        "harness_cli_path": str(HARNESS_CLI_DIR.resolve()),
        "version": "1.0.0",
    }
    (project / ".harness.json").write_text(json.dumps(config, indent=2) + "\n")
    print(f"  .harness.json: created")


def copy_templates(project: Path, registry: Path):
    registry_path = str(registry.resolve())
    project_name = project.name

    for tpl_name, out_name in [("CLAUDE.md.tpl", "CLAUDE.md"), ("AGENTS.md.tpl", "AGENTS.md")]:
        tpl_path = TEMPLATES_DIR / tpl_name
        if not tpl_path.exists():
            print(f"  Warning: Template not found: {tpl_path}")
            continue
        content = tpl_path.read_text()
        content = content.replace("{{REGISTRY_PATH}}", registry_path)
        content = content.replace("{{PROJECT_NAME}}", project_name)
        (project / out_name).write_text(content)
        print(f"  {out_name}: created")


def create_agents_symlink(project: Path, registry: Path):
    agents_path = project / ".agents"
    target = registry / "blueprint" / "orchestrate-members"

    if agents_path.exists() or agents_path.is_symlink():
        print(f"  .agents/: already exists, skipping")
        return

    os.symlink(str(target.resolve()), str(agents_path))
    print(f"  .agents/: symlinked -> {target}")


def configure_hooks(project: Path):
    claude_dir = project / ".claude"
    claude_dir.mkdir(exist_ok=True)
    settings_path = claude_dir / "settings.local.json"

    cli_path = str(HARNESS_CLI_DIR.resolve())

    hooks_config = {
        "hooks": {
            "PreToolUse": [
                {"matcher": "Write|Edit", "command": f"python {cli_path}/hooks/path_validator.py"},
                {"matcher": "Write|Edit", "command": f"python {cli_path}/hooks/spec_cascade_gate.py"},
            ],
            "PostToolUse": [
                {"matcher": "Bash", "command": f"node {cli_path}/dist/hooks/post_pr_wait.js"},
            ],
        }
    }

    if settings_path.exists():
        existing = json.loads(settings_path.read_text())
        existing["hooks"] = hooks_config["hooks"]
        settings_path.write_text(json.dumps(existing, indent=2) + "\n")
    else:
        settings_path.write_text(json.dumps(hooks_config, indent=2) + "\n")

    print(f"  Hooks: path_validator, spec_cascade_gate, post_pr_wait")


def update_gitignore(project: Path):
    gitignore_path = project / ".gitignore"

    existing_content = ""
    existing_lines = set()
    if gitignore_path.exists():
        existing_content = gitignore_path.read_text()
        existing_lines = set(existing_content.splitlines())

    new_entries = [e for e in GITIGNORE_ENTRIES if e not in existing_lines]
    if new_entries:
        with open(gitignore_path, "a") as f:
            if existing_content and not existing_content.endswith("\n"):
                f.write("\n")
            f.write("\n".join(new_entries) + "\n")
        print(f"  .gitignore: updated")
    else:
        print(f"  .gitignore: already up to date")


def main():
    parser = argparse.ArgumentParser(description="Initialize MAS Harness in a project")
    parser.add_argument("--project", required=True, help="Path to the target project")
    parser.add_argument("--registry", required=True, help="Path to the MAS registry vault")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    registry = Path(args.registry).resolve()

    validate_inputs(project, registry)

    print(f"MAS Harness initializing for: {project}")
    print(f"  Registry: {registry}")

    create_harness_json(project, registry)
    copy_templates(project, registry)
    create_agents_symlink(project, registry)
    configure_hooks(project)
    update_gitignore(project)

    print(f"\nDone! MAS Harness installed.")


if __name__ == "__main__":
    main()
