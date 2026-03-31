"""Snapshot manager — immutable candidate lifecycle for the evolution loop.

Handles creation, promotion, rollback, and deduplication of immutable
candidate snapshots. Each candidate captures workspace/{sys,cli} as a
frozen directory under snapshots/candidate-N/.
"""

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def compute_tree_hash(candidate_dir: str) -> str:
    """Compute a SHA-256 hash over all file contents in sys/ and cli/ subdirs.

    The hash is deterministic: files are sorted by their relative path, and
    both the path and contents contribute to the digest. Files outside sys/
    and cli/ are ignored.
    """
    root = Path(candidate_dir)
    hasher = hashlib.sha256()

    entries: list[tuple[str, bytes]] = []
    for subdir_name in ("sys", "cli"):
        subdir = root / subdir_name
        if not subdir.is_dir():
            continue
        for file_path in sorted(subdir.rglob("*")):
            if file_path.is_file():
                rel = file_path.relative_to(root)
                entries.append((str(rel), file_path.read_bytes()))

    # Sort for determinism
    entries.sort(key=lambda e: e[0])
    for rel_path, content in entries:
        hasher.update(rel_path.encode("utf-8"))
        hasher.update(content)

    return hasher.hexdigest()


# ---------------------------------------------------------------------------
# Manifest I/O
# ---------------------------------------------------------------------------

def load_manifest(manifest_path: str) -> dict[str, Any]:
    """Load manifest.json from disk. Raises FileNotFoundError if missing."""
    p = Path(manifest_path)
    if not p.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    with open(p) as f:
        return json.load(f)


def save_manifest(manifest_path: str, manifest: dict[str, Any]) -> None:
    """Save manifest.json atomically (write to tmp then rename)."""
    p = Path(manifest_path)
    fd, tmp_path = tempfile.mkstemp(
        suffix=".tmp", prefix="manifest_", dir=str(p.parent)
    )
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(manifest, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.rename(tmp_path, str(p))
    except BaseException:
        # Clean up tmp on failure
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def get_active_candidate(manifest_path: str) -> Optional[str]:
    """Return the active candidate id from the manifest, or None."""
    manifest = load_manifest(manifest_path)
    return manifest.get("active")


# ---------------------------------------------------------------------------
# Candidate creation
# ---------------------------------------------------------------------------

def _next_candidate_id(manifest: dict[str, Any]) -> str:
    """Derive next candidate-N id from existing candidates in manifest."""
    existing = manifest.get("candidates", [])
    if not existing:
        return "candidate-0"
    max_n = max(int(c["id"].split("-")[-1]) for c in existing)
    return f"candidate-{max_n + 1}"


def _find_existing_hash(manifest: dict[str, Any], tree_hash: str) -> Optional[str]:
    """Check if any existing candidate already has this tree hash."""
    for candidate in manifest.get("candidates", []):
        sha = candidate.get("sha256")
        if sha is None:
            continue
        if sha == tree_hash:
            return candidate["id"]
    return None


def create_candidate(
    workspace: str,
    snapshots_dir: str,
    manifest_path: str,
    parent_id: Optional[str],
    mutation_description: str,
) -> dict[str, Any]:
    """Capture workspace as immutable snapshot, then ALWAYS destroy workspace.

    Returns {"id": "candidate-N"} on success, or {"id": None} if the content
    is a duplicate of an existing candidate (no-op dedup).
    """
    ws = Path(workspace)
    try:
        return _create_candidate_inner(
            ws, snapshots_dir, manifest_path, parent_id, mutation_description
        )
    finally:
        # ALWAYS destroy workspace, even on error
        if ws.exists():
            shutil.rmtree(str(ws))


def _create_candidate_inner(
    ws: Path,
    snapshots_dir: str,
    manifest_path: str,
    parent_id: Optional[str],
    mutation_description: str,
) -> dict[str, Any]:
    """Inner logic for create_candidate (workspace cleanup in caller)."""
    tree_hash = compute_tree_hash(str(ws))

    manifest = load_manifest(manifest_path)

    # Dedup: if hash matches existing candidate, return no-op
    existing = _find_existing_hash(manifest, tree_hash)
    if existing is not None:
        return {"id": None}

    cid = _next_candidate_id(manifest)
    candidate_dir = Path(snapshots_dir) / cid
    candidate_dir.mkdir(parents=True)

    # Copy sys/ and cli/ from workspace
    for subdir_name in ("sys", "cli"):
        src = ws / subdir_name
        dst = candidate_dir / subdir_name
        if src.is_dir():
            shutil.copytree(str(src), str(dst))

    # Write meta.json
    meta = {
        "id": cid,
        "hash": tree_hash,
        "parent_id": parent_id,
        "mutation_description": mutation_description,
    }
    (candidate_dir / "meta.json").write_text(json.dumps(meta, indent=2))

    # Update manifest
    manifest.setdefault("candidates", []).append({
        "id": cid,
        "parent": parent_id,
        "status": "pending",
        "mutation": mutation_description,
        "sha256": tree_hash,
        "pass_rate": {},
        "created": None,
    })
    save_manifest(manifest_path, manifest)

    return {"id": cid}


# ---------------------------------------------------------------------------
# Promotion
# ---------------------------------------------------------------------------

def _atomic_symlink(target: str, link_path: str) -> None:
    """Create/replace a symlink atomically (create tmp, rename over)."""
    link = Path(link_path)
    tmp_link = link.with_suffix(".tmp")
    # Remove stale tmp if exists
    if tmp_link.is_symlink() or tmp_link.exists():
        tmp_link.unlink()
    os.symlink(target, str(tmp_link))
    os.rename(str(tmp_link), str(link))


def promote_candidate(
    candidate_id: str,
    snapshots_dir: str,
    manifest_path: str,
) -> None:
    """Promote a candidate: update symlink + manifest.

    - Old active candidate's status becomes "superseded".
    - New candidate's status becomes "active".
    - candidate_id is appended to the promoted list.
    - The 'active' symlink in snapshots_dir points to the candidate.
    """
    sd = Path(snapshots_dir)
    manifest = load_manifest(manifest_path)

    # Supersede old active
    old_active = manifest.get("active")
    if old_active:
        for c in manifest.get("candidates", []):
            if c["id"] == old_active:
                c["status"] = "superseded"
                break

    # Activate new candidate
    manifest["active"] = candidate_id
    for c in manifest.get("candidates", []):
        if c["id"] == candidate_id:
            c["status"] = "active"
            break
    if candidate_id not in manifest.get("promoted", []):
        manifest.setdefault("promoted", []).append(candidate_id)

    save_manifest(manifest_path, manifest)

    # Atomic symlink swap
    target = str(sd / candidate_id)
    link_path = str(sd / "active")
    _atomic_symlink(target, link_path)


# ---------------------------------------------------------------------------
# Rollback
# ---------------------------------------------------------------------------

def rollback_to(
    candidate_id: str,
    snapshots_dir: str,
    manifest_path: str,
) -> None:
    """Rollback: repoint active symlink + update manifest active field.

    Demotes the current active candidate to 'superseded' before activating
    the rollback target.
    """
    sd = Path(snapshots_dir)
    manifest = load_manifest(manifest_path)

    # Demote old active
    old_active = manifest.get("active")
    if old_active and old_active != candidate_id:
        for c in manifest.get("candidates", []):
            if c["id"] == old_active:
                c["status"] = "superseded"
                break

    # Activate rollback target
    manifest["active"] = candidate_id
    for c in manifest.get("candidates", []):
        if c["id"] == candidate_id:
            c["status"] = "active"
            break
    save_manifest(manifest_path, manifest)

    # Atomic symlink swap
    target = str(sd / candidate_id)
    link_path = str(sd / "active")
    _atomic_symlink(target, link_path)
