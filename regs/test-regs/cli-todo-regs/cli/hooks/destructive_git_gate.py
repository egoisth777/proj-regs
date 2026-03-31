"""PreToolUse hook: blocks destructive git and filesystem operations."""

import json
import re
import sys

DESTRUCTIVE_PATTERNS = [
    (r"\bgit\s+rm\b", "git rm"),
    (r"\bgit\s+reset\s+--hard\b", "git reset --hard"),
    (r"\bgit\s+push\s+--force\b", "git push --force"),
    (r"\bgit\s+push\s+--force-with-lease\b", "git push --force-with-lease"),
    (r"\bgit\s+branch\s+-D\b", "git branch -D"),
    (r"\bgit\s+clean\s+-f", "git clean -f"),
    (r"\bgit\s+checkout\s+--\s+\.", "git checkout -- ."),
    (r"\bgit\s+restore\s+\.\s*$", "git restore ."),
    (r"\brm\s+-[a-z]*r[a-z]*f[a-z]*\b", "rm -rf"),
    (r"\brm\s+-[a-z]*f[a-z]*r[a-z]*\b", "rm -fr"),
]


def check_destructive_git(command: str) -> dict:
    """Check if a bash command contains destructive patterns.

    Returns {"decision": "allow"} or {"decision": "block", "reason": "..."}.
    """
    for pattern, label in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command):
            return {
                "decision": "block",
                "reason": f"Destructive operation blocked: {label}",
            }
    return {"decision": "allow"}


def main():
    """Claude Code hook entry point. Reads JSON from stdin."""
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        json.dump({"decision": "allow"}, sys.stdout)
        return

    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        json.dump({"decision": "allow"}, sys.stdout)
        return

    command = input_data.get("tool_input", {}).get("command", "")
    result = check_destructive_git(command)
    json.dump(result, sys.stdout)


if __name__ == "__main__":
    main()
