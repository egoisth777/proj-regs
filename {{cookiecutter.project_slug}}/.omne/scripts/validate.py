#!/usr/bin/env python3
"""Validate SSOT frontmatter and reorg layout."""

from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

TYPE_ENUM = {
    "design",
    "workflow",
    "history",
    "proof",
    "reference",
    "index",
    "spec",
    "scope-plan",
    "review-finding",
    "migration",
    "tech-debt",
}
STATUS_ENUM = {"active", "deprecated", "stub", "generated", "stale", "deferred"}
REQUIRED = ("slug", "type", "status", "last_updated")
KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RESOLVE_BY_RE = re.compile(
    r"^(v\d+\.\d+\.\d+(-[a-z0-9][a-z0-9-]*-(threshold|onset|gate|trigger))?"
    r"|[a-z0-9][a-z0-9-]*-(threshold|onset|gate|trigger))$"
)
SKIP_PARTS = {".git", ".git-hooks", ".obsidian", "__pycache__", "wt"}
CONTENT_BUCKETS = {
    "buf",
    "cfg",
    "grad",
    "rem",
    "schemas",
    "agents",
    "obs",
    "archive",
    "prompts",
    "skills",
}
CFG_BUCKETS = {"knows", "architecture", "linter", "behaviors", "tests", "algos", "proof"}
SCHEMA_BUCKETS = {"conduct", "protocol"}


def root() -> Path:
    here = Path.cwd().resolve()
    for candidate in (here, *here.parents):
        if (candidate / ".git").exists() and (candidate / "INDEX.yaml").exists():
            return candidate
    return here


def md_files(base: Path):
    for path in sorted(base.rglob("*.md")):
        rel = path.relative_to(base).as_posix()
        if any(part in SKIP_PARTS for part in rel.split("/")):
            continue
        yield path, rel


def parse_frontmatter(text: str) -> tuple[dict[str, object] | None, list[str]]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, []
    body: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            return parse_yamlish(body), body
        body.append(line)
    return None, body


def parse_yamlish(lines: list[str]) -> dict[str, object]:
    data: dict[str, object] = {}
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("#"):
            i += 1
            continue
        if ":" not in line:
            i += 1
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            data[key] = [item.strip().strip("'\"") for item in value[1:-1].split(",") if item.strip()]
        elif value:
            data[key] = value.strip("'\"")
        else:
            block: list[str] = []
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith("- "):
                block.append(lines[j].strip()[2:].strip().strip("'\""))
                j += 1
            data[key] = block if block else ""
            i = j - 1
        i += 1
    return data


def bucket_for(rel: str) -> tuple[str, str | None, str | None]:
    parts = rel.split("/")
    bucket = parts[0]
    sub_bucket = None
    role = None
    if bucket == "cfg" and len(parts) > 1:
        sub_bucket = parts[1]
    if bucket == "schemas" and len(parts) > 1:
        sub_bucket = parts[1]
    if bucket == "agents" and len(parts) == 2 and parts[1] != "IDX.md":
        role = Path(parts[1]).stem
    return bucket, sub_bucket, role


def validate() -> list[str]:
    base = root()
    errors: list[str] = []

    for dirname in CONTENT_BUCKETS:
        if not (base / dirname).is_dir():
            errors.append(f"{dirname}/: missing content bucket")
    for dirname in CFG_BUCKETS:
        if not (base / "cfg" / dirname).is_dir():
            errors.append(f"cfg/{dirname}/: missing cfg sub-bucket")
    for old in ("cfg/what", "cfg/how", "cfg/goals", "cfg/why", "cfg/issues", "cfg/synths", "nav", "stale", "var"):
        if (base / old).exists():
            errors.append(f"{old}/: old bucket must not exist")

    slugs: dict[str, str] = {}
    for path, rel in md_files(base):
        data, _ = parse_frontmatter(path.read_text(encoding="utf-8-sig"))
        if data is None:
            errors.append(f"{rel}:1: missing or unterminated frontmatter")
            continue
        for key in REQUIRED:
            if not data.get(key):
                errors.append(f"{rel}:1: {key}: required key missing or empty")
        slug = data.get("slug")
        if isinstance(slug, str) and slug:
            if not KEBAB_RE.match(slug):
                errors.append(f"{rel}:1: slug: not kebab-case")
            prior = slugs.setdefault(slug, rel)
            if prior != rel:
                errors.append(f"{rel}:1: slug: duplicate of {prior}")
        doc_type = data.get("type")
        status = data.get("status")
        if isinstance(doc_type, str) and doc_type not in TYPE_ENUM:
            errors.append(f"{rel}:1: type: unknown {doc_type!r}")
        if isinstance(status, str) and status not in STATUS_ENUM:
            errors.append(f"{rel}:1: status: unknown {status!r}")
        last_updated = data.get("last_updated")
        if isinstance(last_updated, str):
            if not DATE_RE.match(last_updated):
                errors.append(f"{rel}:1: last_updated: not YYYY-MM-DD")
            else:
                try:
                    datetime.strptime(last_updated, "%Y-%m-%d")
                except ValueError:
                    errors.append(f"{rel}:1: last_updated: invalid date")
        if doc_type == "tech-debt":
            resolve_by = data.get("resolve_by")
            if not isinstance(resolve_by, str) or not RESOLVE_BY_RE.match(resolve_by):
                errors.append(f"{rel}:1: resolve_by: required for tech-debt")
        bucket, sub_bucket, _ = bucket_for(rel)
        if bucket not in CONTENT_BUCKETS and bucket not in {".claude"}:
            errors.append(f"{rel}:1: bucket: unexpected top-level bucket {bucket!r}")
        if rel.startswith("cfg/") and sub_bucket not in CFG_BUCKETS:
            errors.append(f"{rel}:1: sub_bucket: unexpected cfg sub-bucket {sub_bucket!r}")
        if rel.startswith("schemas/") and sub_bucket not in SCHEMA_BUCKETS:
            errors.append(f"{rel}:1: sub_bucket: unexpected schemas sub-bucket {sub_bucket!r}")
        if rel.startswith("agents/") and rel != "agents/IDX.md":
            for key in ("capability", "tools", "forbidden"):
                if not data.get(key):
                    errors.append(f"{rel}:1: {key}: required for agent docs")
        if rel.startswith("cfg/knows/") and rel != "cfg/knows/IDX.md":
            text = path.read_text(encoding="utf-8-sig")
            if "\n## what" not in text or "\n## why" not in text:
                errors.append(f"{rel}:1: cfg/knows entries require ## what and ## why")
        if rel.startswith("cfg/algos/") and rel != "cfg/algos/IDX.md":
            text = path.read_text(encoding="utf-8-sig")
            if "cfg/proof/" not in text and not data.get("resolve_by"):
                errors.append(f"{rel}:1: cfg/algos entries require cfg/proof link or resolve_by")
    return errors


def main() -> int:
    # Accept legacy hook flags such as --quiet; validation output is already concise.
    _ = sys.argv[1:]
    errors = validate()
    for error in errors:
        print(error)
    if errors:
        print(f"validate.py: {len(errors)} violation(s).", file=sys.stderr)
        return 1
    print("validate.py: OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
