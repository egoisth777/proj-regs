"""Tests for snapshot_manager — immutable candidate lifecycle."""

import json
import os
from pathlib import Path

import pytest

from hooks.utils.snapshot_manager import (
    compute_tree_hash,
    create_candidate,
    get_active_candidate,
    load_manifest,
    promote_candidate,
    rollback_to,
    save_manifest,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def workspace(tmp_path):
    """Create a workspace with sys/ and cli/ subdirectories containing files."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "sys").mkdir()
    (ws / "cli").mkdir()
    (ws / "sys" / "template.yaml").write_text("key: value\n")
    (ws / "cli" / "main.py").write_text("print('hello')\n")
    return ws


@pytest.fixture
def snapshots_dir(tmp_path):
    """Empty snapshots directory."""
    sd = tmp_path / "snapshots"
    sd.mkdir()
    return sd


@pytest.fixture
def manifest_path(tmp_path):
    """Path for manifest.json (does not exist yet)."""
    return tmp_path / "manifest.json"


@pytest.fixture
def base_manifest():
    """A minimal valid manifest."""
    return {
        "active": None,
        "candidates": {},
        "promoted": [],
    }


# ---------------------------------------------------------------------------
# compute_tree_hash
# ---------------------------------------------------------------------------

class TestComputeTreeHash:
    def test_same_content_same_hash(self, tmp_path):
        """Identical directory trees produce the same hash."""
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        for d in (dir_a, dir_b):
            (d / "sys").mkdir(parents=True)
            (d / "cli").mkdir(parents=True)
            (d / "sys" / "file.txt").write_text("hello\n")
            (d / "cli" / "run.py").write_text("pass\n")

        assert compute_tree_hash(str(dir_a)) == compute_tree_hash(str(dir_b))

    def test_different_content_different_hash(self, tmp_path):
        """Different content produces different hashes."""
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        for d in (dir_a, dir_b):
            (d / "sys").mkdir(parents=True)
            (d / "cli").mkdir(parents=True)

        (dir_a / "sys" / "file.txt").write_text("hello\n")
        (dir_a / "cli" / "run.py").write_text("pass\n")
        (dir_b / "sys" / "file.txt").write_text("world\n")
        (dir_b / "cli" / "run.py").write_text("pass\n")

        assert compute_tree_hash(str(dir_a)) != compute_tree_hash(str(dir_b))

    def test_hash_is_64_hex_chars(self, tmp_path):
        """SHA-256 hex digest is exactly 64 characters."""
        d = tmp_path / "d"
        (d / "sys").mkdir(parents=True)
        (d / "cli").mkdir(parents=True)
        (d / "sys" / "f.txt").write_text("x\n")

        h = compute_tree_hash(str(d))
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_ignores_files_outside_sys_cli(self, tmp_path):
        """Only sys/ and cli/ subdirs are hashed; other files are ignored."""
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        for d in (dir_a, dir_b):
            (d / "sys").mkdir(parents=True)
            (d / "cli").mkdir(parents=True)
            (d / "sys" / "f.txt").write_text("same\n")
            (d / "cli" / "f.txt").write_text("same\n")

        # Add an extra file outside sys/cli to dir_b
        (dir_b / "extra.txt").write_text("noise\n")

        assert compute_tree_hash(str(dir_a)) == compute_tree_hash(str(dir_b))

    def test_hash_sensitive_to_filename(self, tmp_path):
        """Same content under different filenames produces different hashes."""
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        for d in (dir_a, dir_b):
            (d / "sys").mkdir(parents=True)
            (d / "cli").mkdir(parents=True)

        (dir_a / "sys" / "alpha.txt").write_text("data\n")
        (dir_b / "sys" / "beta.txt").write_text("data\n")

        assert compute_tree_hash(str(dir_a)) != compute_tree_hash(str(dir_b))


# ---------------------------------------------------------------------------
# load_manifest / save_manifest
# ---------------------------------------------------------------------------

class TestManifestRoundTrip:
    def test_save_and_load(self, manifest_path, base_manifest):
        """Round-trip: save then load produces identical data."""
        save_manifest(str(manifest_path), base_manifest)
        loaded = load_manifest(str(manifest_path))
        assert loaded == base_manifest

    def test_save_is_atomic(self, manifest_path, base_manifest):
        """After save, no tmp file remains and manifest exists."""
        save_manifest(str(manifest_path), base_manifest)
        assert manifest_path.exists()
        # No leftover .tmp file
        parent = manifest_path.parent
        tmp_files = list(parent.glob("*.tmp"))
        assert len(tmp_files) == 0

    def test_load_nonexistent_raises(self, tmp_path):
        """Loading a nonexistent manifest raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_manifest(str(tmp_path / "nope.json"))

    def test_save_overwrites(self, manifest_path, base_manifest):
        """Saving twice overwrites the first manifest."""
        save_manifest(str(manifest_path), base_manifest)
        updated = {**base_manifest, "active": "candidate-1"}
        save_manifest(str(manifest_path), updated)
        loaded = load_manifest(str(manifest_path))
        assert loaded["active"] == "candidate-1"


# ---------------------------------------------------------------------------
# get_active_candidate
# ---------------------------------------------------------------------------

class TestGetActiveCandidate:
    def test_returns_active_id(self, manifest_path):
        manifest = {"active": "candidate-3", "candidates": {}, "promoted": []}
        save_manifest(str(manifest_path), manifest)
        assert get_active_candidate(str(manifest_path)) == "candidate-3"

    def test_returns_none_when_no_active(self, manifest_path):
        manifest = {"active": None, "candidates": {}, "promoted": []}
        save_manifest(str(manifest_path), manifest)
        assert get_active_candidate(str(manifest_path)) is None


# ---------------------------------------------------------------------------
# create_candidate
# ---------------------------------------------------------------------------

class TestCreateCandidate:
    def test_creates_snapshot_directory(
        self, workspace, snapshots_dir, manifest_path, base_manifest
    ):
        """Creates a candidate-N directory in snapshots/."""
        save_manifest(str(manifest_path), base_manifest)
        result = create_candidate(
            str(workspace), str(snapshots_dir), str(manifest_path),
            parent_id=None, mutation_description="initial",
        )
        cid = result["id"]
        assert cid is not None
        candidate_dir = snapshots_dir / cid
        assert candidate_dir.is_dir()
        assert (candidate_dir / "sys" / "template.yaml").exists()
        assert (candidate_dir / "cli" / "main.py").exists()

    def test_writes_meta_json(
        self, workspace, snapshots_dir, manifest_path, base_manifest
    ):
        """Each candidate has a meta.json with hash, parent_id, description."""
        save_manifest(str(manifest_path), base_manifest)
        result = create_candidate(
            str(workspace), str(snapshots_dir), str(manifest_path),
            parent_id=None, mutation_description="first snapshot",
        )
        meta_path = snapshots_dir / result["id"] / "meta.json"
        assert meta_path.exists()
        meta = json.loads(meta_path.read_text())
        assert "hash" in meta
        assert meta["parent_id"] is None
        assert meta["mutation_description"] == "first snapshot"

    def test_destroys_workspace_after_create(
        self, workspace, snapshots_dir, manifest_path, base_manifest
    ):
        """Workspace is destroyed after snapshot is captured."""
        save_manifest(str(manifest_path), base_manifest)
        create_candidate(
            str(workspace), str(snapshots_dir), str(manifest_path),
            parent_id=None, mutation_description="test",
        )
        assert not workspace.exists()

    def test_destroys_workspace_on_error(
        self, workspace, manifest_path, base_manifest, tmp_path
    ):
        """Workspace is destroyed even if snapshot creation errors."""
        save_manifest(str(manifest_path), base_manifest)
        # Use a non-writable snapshots dir to trigger error
        bad_snapshots = tmp_path / "no-write"
        bad_snapshots.mkdir()
        os.chmod(str(bad_snapshots), 0o444)
        try:
            with pytest.raises(Exception):
                create_candidate(
                    str(workspace), str(bad_snapshots), str(manifest_path),
                    parent_id=None, mutation_description="fail",
                )
            assert not workspace.exists()
        finally:
            # Restore permissions for tmp_path cleanup
            os.chmod(str(bad_snapshots), 0o755)

    def test_dedup_identical_content(
        self, tmp_path, snapshots_dir, manifest_path, base_manifest
    ):
        """If hash matches an existing candidate, returns {id: None}."""
        save_manifest(str(manifest_path), base_manifest)

        # Create first workspace and snapshot
        ws1 = tmp_path / "ws1"
        ws1.mkdir()
        (ws1 / "sys").mkdir()
        (ws1 / "cli").mkdir()
        (ws1 / "sys" / "f.txt").write_text("same\n")
        (ws1 / "cli" / "f.txt").write_text("same\n")
        result1 = create_candidate(
            str(ws1), str(snapshots_dir), str(manifest_path),
            parent_id=None, mutation_description="first",
        )
        assert result1["id"] is not None

        # Create second workspace with identical content
        ws2 = tmp_path / "ws2"
        ws2.mkdir()
        (ws2 / "sys").mkdir()
        (ws2 / "cli").mkdir()
        (ws2 / "sys" / "f.txt").write_text("same\n")
        (ws2 / "cli" / "f.txt").write_text("same\n")
        result2 = create_candidate(
            str(ws2), str(snapshots_dir), str(manifest_path),
            parent_id=result1["id"], mutation_description="dupe",
        )
        assert result2["id"] is None
        # Workspace still destroyed
        assert not ws2.exists()

    def test_updates_manifest(
        self, workspace, snapshots_dir, manifest_path, base_manifest
    ):
        """Manifest is updated with new candidate entry."""
        save_manifest(str(manifest_path), base_manifest)
        result = create_candidate(
            str(workspace), str(snapshots_dir), str(manifest_path),
            parent_id=None, mutation_description="test",
        )
        manifest = load_manifest(str(manifest_path))
        assert result["id"] in manifest["candidates"]

    def test_increments_candidate_id(
        self, tmp_path, snapshots_dir, manifest_path, base_manifest
    ):
        """Each new candidate gets an incrementing id."""
        save_manifest(str(manifest_path), base_manifest)

        ws1 = tmp_path / "ws1"
        ws1.mkdir()
        (ws1 / "sys").mkdir(); (ws1 / "cli").mkdir()
        (ws1 / "sys" / "a.txt").write_text("one\n")
        r1 = create_candidate(
            str(ws1), str(snapshots_dir), str(manifest_path),
            parent_id=None, mutation_description="first",
        )

        ws2 = tmp_path / "ws2"
        ws2.mkdir()
        (ws2 / "sys").mkdir(); (ws2 / "cli").mkdir()
        (ws2 / "sys" / "a.txt").write_text("two\n")
        r2 = create_candidate(
            str(ws2), str(snapshots_dir), str(manifest_path),
            parent_id=r1["id"], mutation_description="second",
        )

        # Extract numeric suffixes
        n1 = int(r1["id"].split("-")[-1])
        n2 = int(r2["id"].split("-")[-1])
        assert n2 == n1 + 1


# ---------------------------------------------------------------------------
# promote_candidate
# ---------------------------------------------------------------------------

class TestPromoteCandidate:
    def _setup_two_candidates(self, tmp_path, snapshots_dir, manifest_path):
        """Helper: create two candidates and return their ids."""
        manifest = {"active": None, "candidates": {}, "promoted": []}
        save_manifest(str(manifest_path), manifest)

        ws1 = tmp_path / "ws1"
        ws1.mkdir()
        (ws1 / "sys").mkdir(); (ws1 / "cli").mkdir()
        (ws1 / "sys" / "f.txt").write_text("v1\n")
        r1 = create_candidate(
            str(ws1), str(snapshots_dir), str(manifest_path),
            parent_id=None, mutation_description="v1",
        )

        ws2 = tmp_path / "ws2"
        ws2.mkdir()
        (ws2 / "sys").mkdir(); (ws2 / "cli").mkdir()
        (ws2 / "sys" / "f.txt").write_text("v2\n")
        r2 = create_candidate(
            str(ws2), str(snapshots_dir), str(manifest_path),
            parent_id=r1["id"], mutation_description="v2",
        )
        return r1["id"], r2["id"]

    def test_creates_active_symlink(self, tmp_path, snapshots_dir, manifest_path):
        """promote_candidate creates an 'active' symlink in snapshots_dir."""
        c1, _ = self._setup_two_candidates(tmp_path, snapshots_dir, manifest_path)
        promote_candidate(c1, str(snapshots_dir), str(manifest_path))

        active_link = snapshots_dir / "active"
        assert active_link.is_symlink()
        assert active_link.resolve() == (snapshots_dir / c1).resolve()

    def test_updates_manifest_active(self, tmp_path, snapshots_dir, manifest_path):
        """Manifest active field is set to promoted candidate."""
        c1, _ = self._setup_two_candidates(tmp_path, snapshots_dir, manifest_path)
        promote_candidate(c1, str(snapshots_dir), str(manifest_path))

        manifest = load_manifest(str(manifest_path))
        assert manifest["active"] == c1
        assert c1 in manifest["promoted"]

    def test_supersedes_old_active(self, tmp_path, snapshots_dir, manifest_path):
        """Promoting a new candidate supersedes the old active."""
        c1, c2 = self._setup_two_candidates(tmp_path, snapshots_dir, manifest_path)

        promote_candidate(c1, str(snapshots_dir), str(manifest_path))
        promote_candidate(c2, str(snapshots_dir), str(manifest_path))

        manifest = load_manifest(str(manifest_path))
        assert manifest["active"] == c2
        assert manifest["candidates"][c1]["status"] == "superseded"
        assert manifest["candidates"][c2]["status"] == "active"

    def test_symlink_points_to_new_candidate(
        self, tmp_path, snapshots_dir, manifest_path
    ):
        """After promoting c2, active symlink points to c2."""
        c1, c2 = self._setup_two_candidates(tmp_path, snapshots_dir, manifest_path)
        promote_candidate(c1, str(snapshots_dir), str(manifest_path))
        promote_candidate(c2, str(snapshots_dir), str(manifest_path))

        active_link = snapshots_dir / "active"
        assert active_link.resolve() == (snapshots_dir / c2).resolve()

    def test_promoted_list_accumulates(
        self, tmp_path, snapshots_dir, manifest_path
    ):
        """The promoted list grows with each promotion."""
        c1, c2 = self._setup_two_candidates(tmp_path, snapshots_dir, manifest_path)
        promote_candidate(c1, str(snapshots_dir), str(manifest_path))
        promote_candidate(c2, str(snapshots_dir), str(manifest_path))

        manifest = load_manifest(str(manifest_path))
        assert manifest["promoted"] == [c1, c2]


# ---------------------------------------------------------------------------
# rollback_to
# ---------------------------------------------------------------------------

class TestRollbackTo:
    def _setup_promoted(self, tmp_path, snapshots_dir, manifest_path):
        """Helper: create two candidates, promote both. Return ids."""
        manifest = {"active": None, "candidates": {}, "promoted": []}
        save_manifest(str(manifest_path), manifest)

        ws1 = tmp_path / "ws1"
        ws1.mkdir()
        (ws1 / "sys").mkdir(); (ws1 / "cli").mkdir()
        (ws1 / "sys" / "f.txt").write_text("v1\n")
        r1 = create_candidate(
            str(ws1), str(snapshots_dir), str(manifest_path),
            parent_id=None, mutation_description="v1",
        )

        ws2 = tmp_path / "ws2"
        ws2.mkdir()
        (ws2 / "sys").mkdir(); (ws2 / "cli").mkdir()
        (ws2 / "sys" / "f.txt").write_text("v2\n")
        r2 = create_candidate(
            str(ws2), str(snapshots_dir), str(manifest_path),
            parent_id=r1["id"], mutation_description="v2",
        )

        promote_candidate(r1["id"], str(snapshots_dir), str(manifest_path))
        promote_candidate(r2["id"], str(snapshots_dir), str(manifest_path))
        return r1["id"], r2["id"]

    def test_rollback_changes_symlink(self, tmp_path, snapshots_dir, manifest_path):
        """rollback_to repoints active symlink to the specified candidate."""
        c1, c2 = self._setup_promoted(tmp_path, snapshots_dir, manifest_path)
        rollback_to(c1, str(snapshots_dir), str(manifest_path))

        active_link = snapshots_dir / "active"
        assert active_link.resolve() == (snapshots_dir / c1).resolve()

    def test_rollback_updates_manifest_active(
        self, tmp_path, snapshots_dir, manifest_path
    ):
        """rollback_to sets manifest active field to the target candidate."""
        c1, c2 = self._setup_promoted(tmp_path, snapshots_dir, manifest_path)
        rollback_to(c1, str(snapshots_dir), str(manifest_path))

        manifest = load_manifest(str(manifest_path))
        assert manifest["active"] == c1
