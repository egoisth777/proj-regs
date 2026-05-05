#!/usr/bin/env sh
set -eu

root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
repo_root="$(CDPATH= cd -- "$root/.." && pwd)"
mkdir -p "$repo_root/.claude/agents"
ln -sf "$root/agents/clerk.md" "$repo_root/.claude/agents/clerk.md"
echo "Linked $repo_root/.claude/agents/clerk.md -> $root/agents/clerk.md"
