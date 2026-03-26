# context/inject.py
"""CLI tool: assembles minimum-context prompts for subagents.

Usage:
    python context/inject.py --role <role> [--feature <feature>] [--project <path>] [--format json|text]
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

from hooks.utils.config_loader import (
    find_project_root,
    load_harness_config,
    load_context_map,
    resolve_feature_folder,
)


def _has_feature_placeholder(required_docs: list[str]) -> bool:
    """Check if any doc path contains <feature> placeholder."""
    return any("<feature>" in doc for doc in required_docs)


def _resolve_doc_path(doc_path: str, feature: Optional[str], registry_path: str) -> str:
    """Resolve <feature> placeholder in a doc path to actual registry-relative path."""
    if "<feature>" not in doc_path:
        return doc_path

    resolved_folder = resolve_feature_folder(registry_path, feature)
    if not resolved_folder:
        return doc_path  # Can't resolve — return as-is, will fail at read time

    # Convert absolute to registry-relative
    rel_folder = os.path.relpath(resolved_folder, registry_path)
    return doc_path.replace("<feature>", rel_folder)


def _read_file(registry_path: str, relative_path: str) -> dict:
    """Read a file from the registry. Returns dict with path, content, and optional error."""
    full_path = Path(registry_path) / relative_path
    if not full_path.exists():
        return {"path": relative_path, "content": None, "error": "File not found"}
    try:
        content = full_path.read_text()
        return {"path": relative_path, "content": content}
    except Exception as e:
        return {"path": relative_path, "content": None, "error": str(e)}


def build_prompt_prefix(
    role: str,
    feature: Optional[str],
    role_definition: Optional[str],
    docs: list[dict],
) -> str:
    """Assemble the prompt prefix from role definition and docs."""
    parts = []

    # Header
    if feature:
        parts.append(f"You are a {role} agent dispatched for feature '{feature}'.")
    else:
        parts.append(f"You are a {role} agent.")

    # Role definition
    if role_definition:
        parts.append("\n## Your Role")
        parts.append(role_definition)

    # Context documents
    readable_docs = [d for d in docs if d.get("content") is not None]
    if readable_docs:
        parts.append("\n## Context Documents")
        for i, doc in enumerate(readable_docs):
            if i > 0:
                parts.append("\n---")
            parts.append(f"\n### {doc['path']}")
            parts.append(doc["content"])

    return "\n".join(parts)


def assemble_context(role: str, feature: Optional[str], registry_path: str) -> dict:
    """Assemble context for a subagent based on its role.

    Returns dict with role, feature, role_definition, docs, prompt_prefix.
    On error, returns {"error": "message"}.
    """
    # Load context map
    try:
        context_map = load_context_map(registry_path)
    except FileNotFoundError as e:
        return {"error": str(e)}

    role_context = context_map.get("agent_role_context", {})

    # Validate role
    if role not in role_context:
        return {"error": f"Role '{role}' not found in context_map.json"}

    required_docs = role_context[role].get("required_docs", [])

    # Check if feature is needed
    needs_feature = _has_feature_placeholder(required_docs)
    if needs_feature and not feature:
        return {"error": f"Role '{role}' requires --feature but none provided"}

    # Resolve feature folder if needed
    if needs_feature:
        resolved_folder = resolve_feature_folder(registry_path, feature)
        if not resolved_folder:
            return {"error": f"No OpenSpec folder found for feature '{feature}'"}

    # Resolve doc paths and read contents
    docs = []
    for doc_path in required_docs:
        resolved_path = _resolve_doc_path(doc_path, feature, registry_path)
        doc_data = _read_file(registry_path, resolved_path)
        docs.append(doc_data)

    # Read role definition
    role_def_path = Path(registry_path) / "blueprint" / "orchestrate-members" / f"{role}.md"
    role_definition = None
    if role_def_path.exists():
        role_definition = role_def_path.read_text()

    # Build prompt prefix
    prompt_prefix = build_prompt_prefix(role, feature, role_definition, docs)

    return {
        "role": role,
        "feature": feature,
        "role_definition": role_definition,
        "docs": docs,
        "prompt_prefix": prompt_prefix,
    }


def main():
    parser = argparse.ArgumentParser(description="Assemble minimum-context prompt for a subagent")
    parser.add_argument("--role", required=True, help="Agent role name")
    parser.add_argument("--feature", default=None, help="Feature name (for roles with <feature> placeholders)")
    parser.add_argument("--project", default=None, help="Path to the project (defaults to CWD)")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
    args = parser.parse_args()

    # Find project root
    project_path = args.project or os.getcwd()
    project_root = find_project_root(project_path)
    if not project_root:
        json.dump({"error": "No .harness.json found. Run init_project.py first."}, sys.stdout)
        sys.exit(1)

    # Load config
    config = load_harness_config(project_root)
    if not config:
        json.dump({"error": "Failed to load .harness.json"}, sys.stdout)
        sys.exit(1)

    registry_path = config.get("registry_path")
    if not registry_path:
        json.dump({"error": "registry_path not found in .harness.json"}, sys.stdout)
        sys.exit(1)

    # Assemble context
    result = assemble_context(args.role, args.feature, registry_path)

    if "error" in result:
        if args.format == "json":
            json.dump(result, sys.stdout)
        else:
            print(result["error"], file=sys.stderr)
        sys.exit(1)

    # Output
    if args.format == "text":
        print(result["prompt_prefix"])
    else:
        json.dump(result, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
