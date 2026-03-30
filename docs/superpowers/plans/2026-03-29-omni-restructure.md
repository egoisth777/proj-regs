# omni system restructure — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure proj-regs into the omni system: snapshot-immutable architecture with layered one-way dependencies, self-evolution loop, and stateless orchestrator.

**Architecture:** Single monorepo with four layers (eval, tpls, regs, artifacts). Templates are managed as immutable snapshots with symlink pointers. The evolution loop mutates templates, evaluates test projects, and keeps improvements. All orchestrator state lives in a single manifest.json file.

**Tech Stack:** Python 3.10+, TypeScript (existing hooks), pytest, vitest, git

**Spec:** `docs/superpowers/specs/2026-03-29-omni-system-design.md`

---

## file map

### new files to create

```
omni/
├── eval/
│   ├── criteria/p1-spec-cascade.yaml
│   ├── criteria/p2-role-boundary.yaml
│   ├── criteria/p3-orchestration.yaml
│   ├── criteria/p4-ssot-integrity.yaml
│   ├── criteria/o1-correctness.yaml
│   ├── criteria/o2-test-quality.yaml
│   ├── criteria/o3-code-quality.yaml
│   ├── criteria/o4-spec-fidelity.yaml
│   ├── tiers/seed.yaml
│   ├── tiers/tier-2.yaml
│   ├── tiers/tier-3.yaml
│   ├── pools/pool-e.md
│   ├── pools/pool-r.md
│   ├── pools/pool-t.md
│   ├── pools/pool-v.md
│   ├── gates/pool_isolation.py
│   ├── gates/evidence_validator.py
│   ├── gates/spot_check.py
│   └── FROZEN.lock
├── tpls/
│   └── snapshots/
│       └── candidate-0/
│           ├── sys/           (moved from reg-tpls/ + mas-harness/)
│           ├── cli/           (moved from harness-cli/)
│           └── meta.json
├── orchestrator/
│   ├── manifest.json
│   ├── loop.py
│   ├── dispatch.py
│   └── anti_gaming.py
└── new hooks:
    ├── tpls/snapshots/candidate-0/cli/hooks/layer_fence.py
    ├── tpls/snapshots/candidate-0/cli/hooks/blueprint_freeze.py
    └── tpls/snapshots/candidate-0/cli/hooks/destructive_git_gate.py
```

### files to move (current → new)

```
mas-harness/                    → tpls/snapshots/candidate-0/sys/tpl-proj/
reg-tpls/tpl-proj/             → (merged into candidate-0/sys/tpl-proj/)
reg-tpls/tpl-research/         → tpls/snapshots/candidate-0/sys/tpl-research/
harness-cli/hooks/             → tpls/snapshots/candidate-0/cli/hooks/
harness-cli/context/           → tpls/snapshots/candidate-0/cli/context/
harness-cli/setup/             → tpls/snapshots/candidate-0/cli/setup/
harness-cli/tests/             → tpls/snapshots/candidate-0/cli/tests/
harness-cli/package.json       → tpls/snapshots/candidate-0/cli/package.json
harness-cli/pyproject.toml     → tpls/snapshots/candidate-0/cli/pyproject.toml
harness-cli/tsconfig.json      → tpls/snapshots/candidate-0/cli/tsconfig.json
harness-cli/vitest.config.ts   → tpls/snapshots/candidate-0/cli/vitest.config.ts
mas-harness-regs/              → regs/omni-regs/ssot/
voice-input-to-markdown/       → regs/voice-input-regs/ssot/
```

### files to delete after move

```
mas-harness/           (moved to tpls/)
reg-tpls/              (merged into tpls/)
harness-cli/           (moved to tpls/)
mas-harness-regs/      (moved to regs/)
voice-input-to-markdown/ (moved to regs/)
registries/            (empty, replaced by regs/)
```

---

## phase 1: directory restructure

### task 1: create the omni directory skeleton

**Files:**
- Create: `eval/`, `tpls/`, `tpls/snapshots/`, `regs/`, `orchestrator/`

- [ ] **Step 1: Create the layer directories**

```bash
mkdir -p eval/criteria eval/tiers eval/scripts eval/pools eval/gates
mkdir -p tpls/snapshots/candidate-0/sys tpls/snapshots/candidate-0/cli
mkdir -p regs/omni-regs/cli regs/omni-regs/ssot
mkdir -p regs/test-regs
mkdir -p orchestrator
```

- [ ] **Step 2: Verify structure**

```bash
find eval tpls regs orchestrator -type d | sort
```

Expected: all directories exist, no files yet.

- [ ] **Step 3: Commit**

```bash
git add eval/ tpls/ regs/ orchestrator/
git commit -m "chore: create omni directory skeleton"
```

---

### task 2: move system templates to tpls/snapshots/candidate-0/sys/

**Files:**
- Move: `mas-harness/` → `tpls/snapshots/candidate-0/sys/tpl-proj/`
- Move: `reg-tpls/tpl-research/` → `tpls/snapshots/candidate-0/sys/tpl-research/`
- Delete: `reg-tpls/tpl-proj/` (duplicate of mas-harness, less complete)

- [ ] **Step 1: Copy mas-harness as tpl-proj**

```bash
cp -r mas-harness/* tpls/snapshots/candidate-0/sys/tpl-proj/
```

Note: mas-harness has 12 role definitions in orchestrate-members/ (including sdet-unit, sdet-integration, sdet-e2e separately). reg-tpls/tpl-proj/ only has a combined sdet.md. Use mas-harness as the canonical source.

- [ ] **Step 2: Copy tpl-research**

```bash
cp -r reg-tpls/tpl-research/* tpls/snapshots/candidate-0/sys/tpl-research/
```

- [ ] **Step 3: Remove .obsidian from templates**

```bash
rm -rf tpls/snapshots/candidate-0/sys/tpl-proj/.obsidian
rm -rf tpls/snapshots/candidate-0/sys/tpl-research/.obsidian
```

.obsidian is a local IDE config, not a template artifact.

- [ ] **Step 4: Verify template structure**

```bash
ls tpls/snapshots/candidate-0/sys/tpl-proj/blueprint/orchestrate-members/
```

Expected: orchestrator.md, worker.md, team-lead.md, sdet-unit.md, sdet-integration.md, sdet-e2e.md, behavior-spec-writer.md, test-spec-writer.md, auditor.md, sonders.md, negator.md, regression-runner.md (12 files)

- [ ] **Step 5: Commit**

```bash
git add tpls/snapshots/candidate-0/sys/
git commit -m "feat: move system templates to tpls/snapshots/candidate-0/sys/"
```

---

### task 3: move cli tooling to tpls/snapshots/candidate-0/cli/

**Files:**
- Move: `harness-cli/hooks/` → `tpls/snapshots/candidate-0/cli/hooks/`
- Move: `harness-cli/context/` → `tpls/snapshots/candidate-0/cli/context/`
- Move: `harness-cli/setup/` → `tpls/snapshots/candidate-0/cli/setup/`
- Move: `harness-cli/tests/` → `tpls/snapshots/candidate-0/cli/tests/`
- Move: `harness-cli/{package.json,pyproject.toml,tsconfig.json,vitest.config.ts}` → `tpls/snapshots/candidate-0/cli/`

- [ ] **Step 1: Copy cli files**

```bash
cp -r harness-cli/hooks tpls/snapshots/candidate-0/cli/
cp -r harness-cli/context tpls/snapshots/candidate-0/cli/
cp -r harness-cli/setup tpls/snapshots/candidate-0/cli/
cp -r harness-cli/tests tpls/snapshots/candidate-0/cli/
cp harness-cli/package.json tpls/snapshots/candidate-0/cli/
cp harness-cli/pyproject.toml tpls/snapshots/candidate-0/cli/
cp harness-cli/tsconfig.json tpls/snapshots/candidate-0/cli/
cp harness-cli/vitest.config.ts tpls/snapshots/candidate-0/cli/
```

- [ ] **Step 2: Remove __pycache__ and build artifacts**

```bash
find tpls/snapshots/candidate-0/cli/ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
rm -rf tpls/snapshots/candidate-0/cli/dist
rm -rf tpls/snapshots/candidate-0/cli/.pytest_cache
```

- [ ] **Step 3: Verify tests still pass from new location**

```bash
cd tpls/snapshots/candidate-0/cli && python -m pytest tests/ -v && cd -
```

Expected: tests may fail due to path changes in config_loader.py and test fixtures. That's expected — we'll fix paths in task 6.

- [ ] **Step 4: Commit**

```bash
git add tpls/snapshots/candidate-0/cli/
git commit -m "feat: move cli tooling to tpls/snapshots/candidate-0/cli/"
```

---

### task 4: move registries to regs/

**Files:**
- Move: `mas-harness-regs/` → `regs/omni-regs/ssot/`
- Move: `voice-input-to-markdown/` → `regs/voice-input-regs/ssot/`
- Create: `regs/omni-regs/cli/` (empty for now, populated at bootstrap)

- [ ] **Step 1: Copy registries**

```bash
cp -r mas-harness-regs/* regs/omni-regs/ssot/
cp -r voice-input-to-markdown/* regs/voice-input-regs/ssot/
mkdir -p regs/voice-input-regs/cli
```

- [ ] **Step 2: Remove .obsidian from registries**

```bash
rm -rf regs/omni-regs/ssot/.obsidian
rm -rf regs/voice-input-regs/ssot/.obsidian
```

- [ ] **Step 3: Remove .agents from registries** (these were subfolders, not the root symlink)

```bash
rm -rf regs/omni-regs/ssot/.agents
rm -rf regs/voice-input-regs/ssot/.agents
```

- [ ] **Step 4: Commit**

```bash
git add regs/
git commit -m "feat: move registries to regs/"
```

---

### task 5: create symlinks and candidate-0 meta.json

**Files:**
- Create: `tpls/snapshots/candidate-0/meta.json`
- Create: `tpls/snapshots/active` (symlink → candidate-0/)
- Create: `tpls/sys` (symlink → snapshots/active/sys/)
- Create: `tpls/cli` (symlink → snapshots/active/cli/)

- [ ] **Step 1: Create meta.json for candidate-0**

Create file `tpls/snapshots/candidate-0/meta.json`:

```json
{
  "id": "candidate-0",
  "parent": null,
  "created_at": "2026-03-29T00:00:00Z",
  "sha256_tree": null,
  "mutation_description": "genesis baseline — migrated from proj-regs structure"
}
```

- [ ] **Step 2: Create symlinks**

```bash
cd tpls/snapshots && ln -sfn candidate-0 active && cd -
cd tpls && ln -sfn snapshots/active/sys sys && ln -sfn snapshots/active/cli cli && cd -
```

- [ ] **Step 3: Verify symlink chain**

```bash
ls -la tpls/sys/
ls -la tpls/cli/
ls tpls/sys/tpl-proj/blueprint/orchestrate-members/
```

Expected: tpls/sys/ resolves to tpls/snapshots/candidate-0/sys/, shows tpl-proj/ and tpl-research/. orchestrate-members/ shows 12 role files.

- [ ] **Step 4: Commit**

```bash
git add tpls/snapshots/candidate-0/meta.json
# symlinks are tracked by git automatically
git add tpls/snapshots/active tpls/sys tpls/cli
git commit -m "feat: create candidate-0 snapshot with symlinks"
```

---

### task 6: update .harness.json and root config

**Files:**
- Modify: `.harness.json`
- Modify: `CLAUDE.md`
- Modify: `AGENTS.md`
- Update: `.agents` symlink
- Update: `.gitignore`

- [ ] **Step 1: Update .harness.json**

Replace contents of `.harness.json`:

```json
{
  "registry_path": "/home/aeonli/repos/proj-regs/regs/omni-regs/ssot",
  "cli_path": "/home/aeonli/repos/proj-regs/tpls/cli",
  "version": "2.0.0"
}
```

- [ ] **Step 2: Update .agents symlink**

```bash
rm .agents
ln -sfn regs/omni-regs/ssot/blueprint/orchestrate-members .agents
```

- [ ] **Step 3: Update CLAUDE.md**

Update the SSoT routing line to point to the new registry path:

```
## SSoT Routing
You MUST first _read_ the **Project Registry** as **SSoT**: `/home/aeonli/repos/proj-regs/regs/omni-regs/ssot`
```

- [ ] **Step 4: Update .gitignore**

Append to `.gitignore`:

```
# build artifacts
__pycache__/
*.pyc
dist/
node_modules/
.pytest_cache/

# ephemeral evolution workspace
tpls/snapshots/workspace/

# old directories (to be removed after migration verified)
```

- [ ] **Step 5: Commit**

```bash
git add .harness.json CLAUDE.md AGENTS.md .agents .gitignore
git commit -m "feat: update root config for omni structure"
```

---

### task 7: remove old directories

**Files:**
- Delete: `mas-harness/`, `mas-harness-regs/`, `reg-tpls/`, `harness-cli/`, `registries/`, `voice-input-to-markdown/`

- [ ] **Step 1: Verify new structure has everything**

```bash
# verify templates
diff -rq mas-harness tpls/snapshots/candidate-0/sys/tpl-proj/ --exclude=".obsidian" --exclude=".agents"
# verify cli
diff -rq harness-cli/hooks tpls/snapshots/candidate-0/cli/hooks/ --exclude="__pycache__"
# verify registries
diff -rq mas-harness-regs regs/omni-regs/ssot/ --exclude=".obsidian" --exclude=".agents"
```

Expected: files should be identical (or only differ in __pycache__, .obsidian, .agents).

- [ ] **Step 2: Remove old directories**

```bash
rm -rf mas-harness mas-harness-regs reg-tpls harness-cli registries voice-input-to-markdown
```

- [ ] **Step 3: Verify clean state**

```bash
ls -la
```

Expected: only `eval/`, `tpls/`, `regs/`, `orchestrator/`, `docs/`, `.agents`, `.claude`, `.git`, `.gitignore`, `.harness.json`, `CLAUDE.md`, `AGENTS.md`, `README.md`

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: remove old directory structure after migration"
```

---

## phase 2: snapshot system

### task 8: implement snapshot manager

**Files:**
- Create: `tpls/snapshots/candidate-0/cli/hooks/utils/snapshot_manager.py`
- Create: `tpls/snapshots/candidate-0/cli/tests/test_snapshot_manager.py`

- [ ] **Step 1: Write failing tests**

Create `tpls/snapshots/candidate-0/cli/tests/test_snapshot_manager.py`:

```python
"""Tests for snapshot_manager.py — immutable candidate management."""

import json
import os
import shutil
import stat
import tempfile
from pathlib import Path

import pytest

from hooks.utils.snapshot_manager import (
    create_candidate,
    promote_candidate,
    rollback_to,
    compute_tree_hash,
    load_manifest,
    save_manifest,
    get_active_candidate,
)


@pytest.fixture
def snapshot_dir(tmp_path):
    """Create a minimal snapshot structure for testing."""
    snapshots = tmp_path / "tpls" / "snapshots"
    snapshots.mkdir(parents=True)

    # create candidate-0
    c0 = snapshots / "candidate-0"
    c0.mkdir()
    (c0 / "sys").mkdir()
    (c0 / "sys" / "example.md").write_text("# template v0")
    (c0 / "cli").mkdir()
    (c0 / "cli" / "hook.py").write_text("print('v0')")
    (c0 / "meta.json").write_text(json.dumps({
        "id": "candidate-0",
        "parent": None,
        "created_at": "2026-03-29T00:00:00Z",
        "sha256_tree": None,
        "mutation_description": "genesis",
    }))

    # create active symlink
    active = snapshots / "active"
    active.symlink_to("candidate-0")

    # create tpls symlinks
    tpls = tmp_path / "tpls"
    (tpls / "sys").symlink_to("snapshots/active/sys")
    (tpls / "cli").symlink_to("snapshots/active/cli")

    # create manifest
    manifest_dir = tmp_path / "orchestrator"
    manifest_dir.mkdir()
    manifest = {
        "active": "candidate-0",
        "phase": "prepare",
        "tier": "seed",
        "test_domain": None,
        "candidates": [{
            "id": "candidate-0",
            "parent": None,
            "status": "active",
            "mutation": None,
            "sha256": None,
            "pass_rate": {},
            "created": "2026-03-29T00:00:00Z",
        }],
        "promoted": ["candidate-0"],
        "next_action": "begin evolution",
    }
    (manifest_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    return tmp_path


class TestComputeTreeHash:
    def test_same_content_same_hash(self, snapshot_dir):
        c0 = snapshot_dir / "tpls" / "snapshots" / "candidate-0"
        h1 = compute_tree_hash(c0)
        h2 = compute_tree_hash(c0)
        assert h1 == h2
        assert len(h1) == 64  # sha-256 hex

    def test_different_content_different_hash(self, snapshot_dir):
        c0 = snapshot_dir / "tpls" / "snapshots" / "candidate-0"
        h1 = compute_tree_hash(c0)
        (c0 / "sys" / "example.md").write_text("# modified")
        h2 = compute_tree_hash(c0)
        assert h1 != h2


class TestCreateCandidate:
    def test_creates_immutable_snapshot(self, snapshot_dir):
        workspace = snapshot_dir / "tpls" / "snapshots" / "workspace"
        workspace.mkdir()
        (workspace / "sys").mkdir()
        (workspace / "sys" / "example.md").write_text("# template v1")
        (workspace / "cli").mkdir()
        (workspace / "cli" / "hook.py").write_text("print('v1')")

        manifest_path = snapshot_dir / "orchestrator" / "manifest.json"
        snapshots_dir = snapshot_dir / "tpls" / "snapshots"

        result = create_candidate(
            workspace=workspace,
            snapshots_dir=snapshots_dir,
            manifest_path=manifest_path,
            parent_id="candidate-0",
            mutation_description="changed template to v1",
        )

        assert result["id"] == "candidate-1"
        assert (snapshots_dir / "candidate-1" / "sys" / "example.md").read_text() == "# template v1"
        assert (snapshots_dir / "candidate-1" / "meta.json").exists()
        assert not workspace.exists(), "workspace should be destroyed"

    def test_deduplicates_identical_content(self, snapshot_dir):
        workspace = snapshot_dir / "tpls" / "snapshots" / "workspace"
        workspace.mkdir()
        # copy exact same content as candidate-0
        c0 = snapshot_dir / "tpls" / "snapshots" / "candidate-0"
        shutil.copytree(c0 / "sys", workspace / "sys")
        shutil.copytree(c0 / "cli", workspace / "cli")

        manifest_path = snapshot_dir / "orchestrator" / "manifest.json"
        snapshots_dir = snapshot_dir / "tpls" / "snapshots"

        result = create_candidate(
            workspace=workspace,
            snapshots_dir=snapshots_dir,
            manifest_path=manifest_path,
            parent_id="candidate-0",
            mutation_description="no-op mutation",
        )

        assert result["id"] is None, "should detect no-op and return None id"
        assert not workspace.exists(), "workspace should still be destroyed"


class TestPromoteCandidate:
    def test_updates_symlink_and_manifest(self, snapshot_dir):
        # create candidate-1 manually
        snapshots_dir = snapshot_dir / "tpls" / "snapshots"
        c1 = snapshots_dir / "candidate-1"
        c1.mkdir()
        (c1 / "sys").mkdir()
        (c1 / "sys" / "example.md").write_text("# v1")
        (c1 / "cli").mkdir()
        (c1 / "cli" / "hook.py").write_text("print('v1')")

        manifest_path = snapshot_dir / "orchestrator" / "manifest.json"
        manifest = load_manifest(manifest_path)
        manifest["candidates"].append({
            "id": "candidate-1",
            "parent": "candidate-0",
            "status": "pending",
            "mutation": "test",
            "sha256": "abc",
            "pass_rate": {"overall": "6/6"},
            "created": "2026-03-29T01:00:00Z",
        })
        save_manifest(manifest_path, manifest)

        promote_candidate("candidate-1", snapshots_dir, manifest_path)

        manifest = load_manifest(manifest_path)
        assert manifest["active"] == "candidate-1"
        assert "candidate-1" in manifest["promoted"]
        active_target = os.readlink(snapshots_dir / "active")
        assert active_target == "candidate-1"

    def test_supersedes_old_active(self, snapshot_dir):
        snapshots_dir = snapshot_dir / "tpls" / "snapshots"
        c1 = snapshots_dir / "candidate-1"
        c1.mkdir()
        (c1 / "sys").mkdir()
        (c1 / "cli").mkdir()

        manifest_path = snapshot_dir / "orchestrator" / "manifest.json"
        manifest = load_manifest(manifest_path)
        manifest["candidates"].append({
            "id": "candidate-1", "parent": "candidate-0",
            "status": "pending", "mutation": "test",
            "sha256": "abc", "pass_rate": {}, "created": "2026-03-29T01:00:00Z",
        })
        save_manifest(manifest_path, manifest)

        promote_candidate("candidate-1", snapshots_dir, manifest_path)

        manifest = load_manifest(manifest_path)
        c0_entry = next(c for c in manifest["candidates"] if c["id"] == "candidate-0")
        assert c0_entry["status"] == "superseded"


class TestRollbackTo:
    def test_rollback_restores_previous(self, snapshot_dir):
        snapshots_dir = snapshot_dir / "tpls" / "snapshots"
        manifest_path = snapshot_dir / "orchestrator" / "manifest.json"

        # create and promote candidate-1
        c1 = snapshots_dir / "candidate-1"
        c1.mkdir()
        (c1 / "sys").mkdir()
        (c1 / "cli").mkdir()
        manifest = load_manifest(manifest_path)
        manifest["candidates"].append({
            "id": "candidate-1", "parent": "candidate-0",
            "status": "pending", "mutation": "bad",
            "sha256": "abc", "pass_rate": {}, "created": "2026-03-29T01:00:00Z",
        })
        save_manifest(manifest_path, manifest)
        promote_candidate("candidate-1", snapshots_dir, manifest_path)

        # rollback to candidate-0
        rollback_to("candidate-0", snapshots_dir, manifest_path)

        manifest = load_manifest(manifest_path)
        assert manifest["active"] == "candidate-0"
        active_target = os.readlink(snapshots_dir / "active")
        assert active_target == "candidate-0"


class TestGetActiveCandidate:
    def test_returns_active_id(self, snapshot_dir):
        manifest_path = snapshot_dir / "orchestrator" / "manifest.json"
        assert get_active_candidate(manifest_path) == "candidate-0"


class TestLoadSaveManifest:
    def test_round_trip(self, snapshot_dir):
        manifest_path = snapshot_dir / "orchestrator" / "manifest.json"
        manifest = load_manifest(manifest_path)
        manifest["phase"] = "mutate"
        save_manifest(manifest_path, manifest)
        reloaded = load_manifest(manifest_path)
        assert reloaded["phase"] == "mutate"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd tpls/snapshots/candidate-0/cli && python -m pytest tests/test_snapshot_manager.py -v && cd -
```

Expected: FAIL — `ModuleNotFoundError: No module named 'hooks.utils.snapshot_manager'`

- [ ] **Step 3: Implement snapshot_manager.py**

Create `tpls/snapshots/candidate-0/cli/hooks/utils/snapshot_manager.py`:

```python
"""Snapshot manager — immutable candidate lifecycle for the evolution loop."""

import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def compute_tree_hash(candidate_dir: Path) -> str:
    """Compute a sha-256 hash of all file contents in sys/ and cli/ subdirs."""
    hasher = hashlib.sha256()
    for subdir in sorted(["sys", "cli"]):
        target = candidate_dir / subdir
        if not target.exists():
            continue
        for root, _, files in sorted(os.walk(target)):
            for fname in sorted(files):
                fpath = Path(root) / fname
                rel = fpath.relative_to(candidate_dir)
                hasher.update(str(rel).encode())
                hasher.update(fpath.read_bytes())
    return hasher.hexdigest()


def load_manifest(manifest_path: Path) -> dict:
    """Load manifest.json."""
    return json.loads(manifest_path.read_text())


def save_manifest(manifest_path: Path, manifest: dict) -> None:
    """Save manifest.json atomically (write to tmp then rename)."""
    tmp = manifest_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(manifest, indent=2))
    tmp.rename(manifest_path)


def get_active_candidate(manifest_path: Path) -> str:
    """Return the id of the currently active candidate."""
    return load_manifest(manifest_path)["active"]


def _next_candidate_id(manifest: dict) -> str:
    """Compute the next candidate id from existing candidates."""
    existing = [c["id"] for c in manifest["candidates"]]
    nums = []
    for cid in existing:
        parts = cid.split("-")
        if len(parts) == 2 and parts[1].isdigit():
            nums.append(int(parts[1]))
    next_num = max(nums, default=-1) + 1
    return f"candidate-{next_num}"


def create_candidate(
    workspace: Path,
    snapshots_dir: Path,
    manifest_path: Path,
    parent_id: str,
    mutation_description: str,
) -> dict:
    """Capture workspace as an immutable snapshot. Destroys workspace after.

    Returns dict with 'id' key. If content is identical to an existing
    candidate (no-op), returns {'id': None}.
    """
    try:
        # compute hash of workspace content
        new_hash = compute_tree_hash(workspace)

        # check for duplicates
        manifest = load_manifest(manifest_path)
        for c in manifest["candidates"]:
            if c.get("sha256") == new_hash:
                return {"id": None}

        candidate_id = _next_candidate_id(manifest)
        target = snapshots_dir / candidate_id

        # copy workspace to candidate dir
        shutil.copytree(workspace / "sys", target / "sys")
        shutil.copytree(workspace / "cli", target / "cli")

        # write meta.json
        meta = {
            "id": candidate_id,
            "parent": parent_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "sha256_tree": new_hash,
            "mutation_description": mutation_description,
        }
        (target / "meta.json").write_text(json.dumps(meta, indent=2))

        # update manifest
        manifest["candidates"].append({
            "id": candidate_id,
            "parent": parent_id,
            "status": "pending",
            "mutation": mutation_description,
            "sha256": new_hash,
            "pass_rate": {},
            "created": meta["created_at"],
        })
        save_manifest(manifest_path, manifest)

        return {"id": candidate_id}
    finally:
        # always destroy workspace
        if workspace.exists():
            shutil.rmtree(workspace)


def promote_candidate(
    candidate_id: str,
    snapshots_dir: Path,
    manifest_path: Path,
) -> None:
    """Promote a candidate: update symlink + manifest."""
    manifest = load_manifest(manifest_path)

    # supersede old active
    for c in manifest["candidates"]:
        if c["id"] == manifest["active"]:
            c["status"] = "superseded"

    # activate new
    for c in manifest["candidates"]:
        if c["id"] == candidate_id:
            c["status"] = "active"

    manifest["active"] = candidate_id
    if candidate_id not in manifest["promoted"]:
        manifest["promoted"].append(candidate_id)

    save_manifest(manifest_path, manifest)

    # atomic symlink swap
    active_link = snapshots_dir / "active"
    tmp_link = snapshots_dir / "active.tmp"
    tmp_link.symlink_to(candidate_id)
    tmp_link.rename(active_link)


def rollback_to(
    candidate_id: str,
    snapshots_dir: Path,
    manifest_path: Path,
) -> None:
    """Rollback to a previous candidate: repoint symlink + update manifest."""
    manifest = load_manifest(manifest_path)
    manifest["active"] = candidate_id

    for c in manifest["candidates"]:
        if c["id"] == candidate_id:
            c["status"] = "active"

    save_manifest(manifest_path, manifest)

    active_link = snapshots_dir / "active"
    tmp_link = snapshots_dir / "active.tmp"
    tmp_link.symlink_to(candidate_id)
    tmp_link.rename(active_link)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd tpls/snapshots/candidate-0/cli && python -m pytest tests/test_snapshot_manager.py -v && cd -
```

Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add tpls/snapshots/candidate-0/cli/hooks/utils/snapshot_manager.py
git add tpls/snapshots/candidate-0/cli/tests/test_snapshot_manager.py
git commit -m "feat: implement snapshot manager with tdd"
```

---

## phase 3: new hooks

### task 9: implement layer_fence.py

**Files:**
- Create: `tpls/snapshots/candidate-0/cli/hooks/layer_fence.py`
- Create: `tpls/snapshots/candidate-0/cli/tests/test_layer_fence.py`

- [ ] **Step 1: Write failing tests**

Create `tpls/snapshots/candidate-0/cli/tests/test_layer_fence.py`:

```python
"""Tests for layer_fence.py — enforces one-way layer dependencies."""

import pytest

from hooks.layer_fence import get_layer, validate_layer_access


class TestGetLayer:
    def test_eval_paths(self):
        assert get_layer("eval/criteria/p1.yaml") == "eval"
        assert get_layer("eval/scripts/check.sh") == "eval"
        assert get_layer("eval/FROZEN.lock") == "eval"

    def test_tpls_paths(self):
        assert get_layer("tpls/snapshots/candidate-0/sys/tpl-proj/blueprint/design/arch.md") == "tpls"
        assert get_layer("tpls/cli/hooks/path_validator.py") == "tpls"
        assert get_layer("tpls/snapshots/workspace/sys/file.md") == "tpls"

    def test_regs_paths(self):
        assert get_layer("regs/omni-regs/ssot/runtime/active_sprint.md") == "regs"
        assert get_layer("regs/test-regs/cli-todo-regs/cli/hooks/hook.py") == "regs"

    def test_orchestrator_paths(self):
        assert get_layer("orchestrator/manifest.json") == "orchestrator"

    def test_unknown_paths(self):
        assert get_layer("docs/readme.md") is None
        assert get_layer("CLAUDE.md") is None


class TestValidateLayerAccess:
    def test_pool_e_can_write_tpls(self):
        result = validate_layer_access("pool-e", "tpls/snapshots/workspace/sys/file.md", "write")
        assert result["decision"] == "allow"

    def test_pool_e_cannot_write_eval(self):
        result = validate_layer_access("pool-e", "eval/criteria/p1.yaml", "write")
        assert result["decision"] == "block"

    def test_pool_e_cannot_read_eval(self):
        result = validate_layer_access("pool-e", "eval/criteria/p1.yaml", "read")
        assert result["decision"] == "block"

    def test_pool_t_can_write_eval_scripts(self):
        result = validate_layer_access("pool-t", "eval/scripts/check_p1.sh", "write")
        assert result["decision"] == "allow"

    def test_pool_t_cannot_write_eval_criteria(self):
        result = validate_layer_access("pool-t", "eval/criteria/p1.yaml", "write")
        assert result["decision"] == "block"

    def test_pool_t_can_read_eval_criteria(self):
        result = validate_layer_access("pool-t", "eval/criteria/p1.yaml", "read")
        assert result["decision"] == "allow"

    def test_pool_t_cannot_read_tpls(self):
        result = validate_layer_access("pool-t", "tpls/sys/tpl-proj/file.md", "read")
        assert result["decision"] == "block"

    def test_pool_v_can_read_eval_scripts(self):
        result = validate_layer_access("pool-v", "eval/scripts/check_p1.sh", "read")
        assert result["decision"] == "allow"

    def test_pool_v_cannot_write_eval(self):
        result = validate_layer_access("pool-v", "eval/scripts/check_p1.sh", "write")
        assert result["decision"] == "block"

    def test_pool_v_can_read_regs(self):
        result = validate_layer_access("pool-v", "regs/test-regs/cli-todo-regs/ssot/file.md", "read")
        assert result["decision"] == "allow"

    def test_pool_r_can_read_regs(self):
        result = validate_layer_access("pool-r", "regs/omni-regs/ssot/runtime/active_sprint.md", "read")
        assert result["decision"] == "allow"

    def test_pool_r_cannot_write_anything(self):
        result = validate_layer_access("pool-r", "regs/omni-regs/ssot/file.md", "write")
        assert result["decision"] == "block"

    def test_non_pool_role_passes_through(self):
        result = validate_layer_access("worker", "regs/proj-regs/ssot/file.md", "write")
        assert result["decision"] == "allow"

    def test_orchestrator_can_write_manifest(self):
        result = validate_layer_access("orchestrator", "orchestrator/manifest.json", "write")
        assert result["decision"] == "allow"

    def test_orchestrator_cannot_write_eval(self):
        result = validate_layer_access("orchestrator", "eval/criteria/p1.yaml", "write")
        assert result["decision"] == "block"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd tpls/snapshots/candidate-0/cli && python -m pytest tests/test_layer_fence.py -v && cd -
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement layer_fence.py**

Create `tpls/snapshots/candidate-0/cli/hooks/layer_fence.py`:

```python
"""PreToolUse hook: enforces one-way layer dependencies for pool agents."""

import json
import sys
from typing import Optional


POOL_PERMISSIONS = {
    "pool-e": {
        "read": ["tpls"],
        "write": ["tpls"],
    },
    "pool-t": {
        "read": ["eval"],
        "write": ["eval"],
        "write_allow": ["eval/scripts/"],
        "write_deny": ["eval/criteria/", "eval/tiers/", "eval/gates/", "eval/pools/", "eval/FROZEN.lock"],
        "read_allow": ["eval/criteria/", "eval/tiers/"],
    },
    "pool-v": {
        "read": ["eval", "regs"],
        "write": [],
        "read_allow": ["eval/scripts/"],
        "read_deny": ["eval/criteria/", "eval/tiers/"],
    },
    "pool-r": {
        "read": ["regs"],
        "write": [],
    },
    "orchestrator": {
        "read": ["orchestrator"],
        "write": ["orchestrator"],
    },
}


def get_layer(file_path: str) -> Optional[str]:
    """Determine which layer a file belongs to."""
    parts = file_path.split("/")
    if not parts:
        return None
    first = parts[0]
    if first in ("eval", "tpls", "regs", "orchestrator"):
        return first
    return None


def validate_layer_access(role: str, file_path: str, operation: str) -> dict:
    """Validate whether a pool role can access a file path.

    Args:
        role: pool-e, pool-t, pool-v, pool-r, orchestrator, or a project role
        file_path: relative path from repo root
        operation: 'read' or 'write'
    """
    if role not in POOL_PERMISSIONS:
        return {"decision": "allow"}

    perms = POOL_PERMISSIONS[role]
    layer = get_layer(file_path)

    if layer is None:
        return {"decision": "allow"}

    allowed_layers = perms.get(operation, [])

    # check explicit deny rules first
    deny_key = f"{operation}_deny"
    if deny_key in perms:
        for prefix in perms[deny_key]:
            if file_path.startswith(prefix):
                return {
                    "decision": "block",
                    "reason": f"Pool '{role}' denied {operation} to '{file_path}' (deny rule: {prefix})",
                }

    # check explicit allow rules
    allow_key = f"{operation}_allow"
    if allow_key in perms:
        for prefix in perms[allow_key]:
            if file_path.startswith(prefix):
                return {"decision": "allow"}
        # if allow rules exist but none matched, check layer-level
        if layer in allowed_layers:
            return {
                "decision": "block",
                "reason": f"Pool '{role}' can access layer '{layer}' but not path '{file_path}'",
            }

    if layer not in allowed_layers:
        return {
            "decision": "block",
            "reason": f"Pool '{role}' cannot {operation} layer '{layer}'. Allowed: {allowed_layers}",
        }

    return {"decision": "allow"}


def main():
    """Entry point for Claude Code hook."""
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        json.dump({"decision": "allow"}, sys.stdout)
        return

    tool_name = input_data.get("tool_name", "")
    file_path = input_data.get("tool_input", {}).get("file_path", "")

    if not file_path:
        json.dump({"decision": "allow"}, sys.stdout)
        return

    # determine operation from tool name
    write_tools = {"Edit", "Write", "NotebookEdit"}
    operation = "write" if tool_name in write_tools else "read"

    # determine pool role from environment or branch
    import os
    pool_role = os.environ.get("OMNI_POOL", "")

    if not pool_role:
        json.dump({"decision": "allow"}, sys.stdout)
        return

    # make path relative to project root
    from hooks.utils.config_loader import find_project_root
    project_root = find_project_root(os.getcwd())
    if project_root:
        try:
            from pathlib import Path
            file_path = str(Path(file_path).relative_to(project_root))
        except ValueError:
            pass

    result = validate_layer_access(pool_role, file_path, operation)
    json.dump(result, sys.stdout)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd tpls/snapshots/candidate-0/cli && python -m pytest tests/test_layer_fence.py -v && cd -
```

Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add tpls/snapshots/candidate-0/cli/hooks/layer_fence.py
git add tpls/snapshots/candidate-0/cli/tests/test_layer_fence.py
git commit -m "feat: implement layer_fence hook with tdd"
```

---

### task 10: implement blueprint_freeze.py

**Files:**
- Create: `tpls/snapshots/candidate-0/cli/hooks/blueprint_freeze.py`
- Create: `tpls/snapshots/candidate-0/cli/tests/test_blueprint_freeze.py`

- [ ] **Step 1: Write failing tests**

Create `tpls/snapshots/candidate-0/cli/tests/test_blueprint_freeze.py`:

```python
"""Tests for blueprint_freeze.py — blocks blueprint writes during active sprints."""

import pytest

from hooks.blueprint_freeze import is_sprint_active, check_blueprint_freeze


class TestIsSprintActive:
    def test_active_sprint(self, tmp_path):
        sprint_file = tmp_path / "active_sprint.md"
        sprint_file.write_text("# Active Sprint\n\n## Current Feature: feat-001-add-task\n**Phase:** execution\n")
        assert is_sprint_active(sprint_file) is True

    def test_no_active_sprint(self, tmp_path):
        sprint_file = tmp_path / "active_sprint.md"
        sprint_file.write_text("# Active Sprint\n\nNo active sprint.\n")
        assert is_sprint_active(sprint_file) is False

    def test_empty_file(self, tmp_path):
        sprint_file = tmp_path / "active_sprint.md"
        sprint_file.write_text("")
        assert is_sprint_active(sprint_file) is False

    def test_missing_file(self, tmp_path):
        sprint_file = tmp_path / "active_sprint.md"
        assert is_sprint_active(sprint_file) is False


class TestCheckBlueprintFreeze:
    def test_blocks_blueprint_write_during_sprint(self, tmp_path):
        sprint_file = tmp_path / "active_sprint.md"
        sprint_file.write_text("## Current Feature: feat-001-add-task\n**Phase:** execution\n")
        result = check_blueprint_freeze("blueprint/design/architecture_overview.md", sprint_file)
        assert result["decision"] == "block"
        assert "blueprint" in result["reason"].lower()

    def test_allows_runtime_write_during_sprint(self, tmp_path):
        sprint_file = tmp_path / "active_sprint.md"
        sprint_file.write_text("## Current Feature: feat-001-add-task\n**Phase:** execution\n")
        result = check_blueprint_freeze("runtime/active_sprint.md", sprint_file)
        assert result["decision"] == "allow"

    def test_allows_blueprint_write_when_no_sprint(self, tmp_path):
        sprint_file = tmp_path / "active_sprint.md"
        sprint_file.write_text("No active sprint.\n")
        result = check_blueprint_freeze("blueprint/design/architecture_overview.md", sprint_file)
        assert result["decision"] == "allow"

    def test_allows_non_blueprint_non_runtime_write(self, tmp_path):
        sprint_file = tmp_path / "active_sprint.md"
        sprint_file.write_text("## Current Feature: feat-001-add-task\n")
        result = check_blueprint_freeze("context_map.json", sprint_file)
        assert result["decision"] == "allow"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd tpls/snapshots/candidate-0/cli && python -m pytest tests/test_blueprint_freeze.py -v && cd -
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement blueprint_freeze.py**

Create `tpls/snapshots/candidate-0/cli/hooks/blueprint_freeze.py`:

```python
"""PreToolUse hook: blocks blueprint writes during active sprints."""

import json
import re
import sys
from pathlib import Path
from typing import Optional


def is_sprint_active(sprint_file: Path) -> bool:
    """Check if there is an active sprint by reading active_sprint.md."""
    if not sprint_file.exists():
        return False
    content = sprint_file.read_text().strip()
    if not content:
        return False
    return bool(re.search(r"(?i)(current feature|phase\s*:)", content))


def check_blueprint_freeze(file_path: str, sprint_file: Path) -> dict:
    """Check if a write to file_path is allowed given sprint state."""
    if not file_path.startswith("blueprint/"):
        return {"decision": "allow"}

    if not is_sprint_active(sprint_file):
        return {"decision": "allow"}

    return {
        "decision": "block",
        "reason": f"Blueprint is frozen during active sprints. Cannot write to '{file_path}'. "
                  f"Complete all sprints before modifying blueprint files.",
    }


def main():
    """Entry point for Claude Code hook."""
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        json.dump({"decision": "allow"}, sys.stdout)
        return

    file_path_abs = input_data.get("tool_input", {}).get("file_path", "")
    if not file_path_abs:
        json.dump({"decision": "allow"}, sys.stdout)
        return

    import os
    from hooks.utils.config_loader import find_project_root, load_harness_config

    project_root = find_project_root(os.getcwd())
    if not project_root:
        json.dump({"decision": "allow"}, sys.stdout)
        return

    config = load_harness_config(project_root)
    registry_path = config.get("registry_path") if config else None
    if not registry_path:
        json.dump({"decision": "allow"}, sys.stdout)
        return

    try:
        file_path = str(Path(file_path_abs).relative_to(registry_path))
    except ValueError:
        json.dump({"decision": "allow"}, sys.stdout)
        return

    sprint_file = Path(registry_path) / "runtime" / "active_sprint.md"
    result = check_blueprint_freeze(file_path, sprint_file)
    json.dump(result, sys.stdout)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd tpls/snapshots/candidate-0/cli && python -m pytest tests/test_blueprint_freeze.py -v && cd -
```

Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add tpls/snapshots/candidate-0/cli/hooks/blueprint_freeze.py
git add tpls/snapshots/candidate-0/cli/tests/test_blueprint_freeze.py
git commit -m "feat: implement blueprint_freeze hook with tdd"
```

---

### task 11: implement destructive_git_gate.py

**Files:**
- Create: `tpls/snapshots/candidate-0/cli/hooks/destructive_git_gate.py`
- Create: `tpls/snapshots/candidate-0/cli/tests/test_destructive_git_gate.py`

- [ ] **Step 1: Write failing tests**

Create `tpls/snapshots/candidate-0/cli/tests/test_destructive_git_gate.py`:

```python
"""Tests for destructive_git_gate.py — blocks destructive git operations."""

import pytest

from hooks.destructive_git_gate import check_destructive_git


class TestCheckDestructiveGit:
    def test_blocks_git_rm(self):
        result = check_destructive_git("git rm src/main.py")
        assert result["decision"] == "block"

    def test_blocks_git_reset_hard(self):
        result = check_destructive_git("git reset --hard HEAD~1")
        assert result["decision"] == "block"

    def test_blocks_git_push_force(self):
        result = check_destructive_git("git push --force origin main")
        assert result["decision"] == "block"

    def test_blocks_git_push_force_with_lease(self):
        result = check_destructive_git("git push --force-with-lease origin main")
        assert result["decision"] == "block"

    def test_blocks_git_branch_D(self):
        result = check_destructive_git("git branch -D feature-branch")
        assert result["decision"] == "block"

    def test_blocks_git_clean_f(self):
        result = check_destructive_git("git clean -f")
        assert result["decision"] == "block"

    def test_blocks_git_checkout_dot(self):
        result = check_destructive_git("git checkout -- .")
        assert result["decision"] == "block"

    def test_blocks_git_restore_dot(self):
        result = check_destructive_git("git restore .")
        assert result["decision"] == "block"

    def test_allows_git_commit(self):
        result = check_destructive_git("git commit -m 'feat: add feature'")
        assert result["decision"] == "allow"

    def test_allows_git_push(self):
        result = check_destructive_git("git push origin feat/auth/worker-1")
        assert result["decision"] == "allow"

    def test_allows_git_branch_create(self):
        result = check_destructive_git("git branch feat/auth/worker-1")
        assert result["decision"] == "allow"

    def test_allows_git_merge(self):
        result = check_destructive_git("git merge feat/auth/worker-1")
        assert result["decision"] == "allow"

    def test_allows_git_status(self):
        result = check_destructive_git("git status")
        assert result["decision"] == "allow"

    def test_allows_non_git_commands(self):
        result = check_destructive_git("python -m pytest tests/")
        assert result["decision"] == "allow"

    def test_blocks_rm_rf(self):
        result = check_destructive_git("rm -rf src/")
        assert result["decision"] == "block"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd tpls/snapshots/candidate-0/cli && python -m pytest tests/test_destructive_git_gate.py -v && cd -
```

Expected: FAIL

- [ ] **Step 3: Implement destructive_git_gate.py**

Create `tpls/snapshots/candidate-0/cli/hooks/destructive_git_gate.py`:

```python
"""PreToolUse hook: blocks destructive git and filesystem operations."""

import json
import re
import sys


DESTRUCTIVE_PATTERNS = [
    r"\bgit\s+rm\b",
    r"\bgit\s+reset\s+--hard\b",
    r"\bgit\s+push\s+--force\b",
    r"\bgit\s+push\s+--force-with-lease\b",
    r"\bgit\s+branch\s+-D\b",
    r"\bgit\s+clean\s+-f\b",
    r"\bgit\s+checkout\s+--\s+\.",
    r"\bgit\s+restore\s+\.",
    r"\brm\s+-rf\b",
]


def check_destructive_git(command: str) -> dict:
    """Check if a bash command contains destructive operations."""
    for pattern in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command):
            return {
                "decision": "block",
                "reason": f"Destructive operation detected: '{command}'. Requires user approval.",
            }
    return {"decision": "allow"}


def main():
    """Entry point for Claude Code hook."""
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd tpls/snapshots/candidate-0/cli && python -m pytest tests/test_destructive_git_gate.py -v && cd -
```

Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add tpls/snapshots/candidate-0/cli/hooks/destructive_git_gate.py
git add tpls/snapshots/candidate-0/cli/tests/test_destructive_git_gate.py
git commit -m "feat: implement destructive_git_gate hook with tdd"
```

---

## phase 4: eval harness

### task 12: create eval criteria and tier files

**Files:**
- Create: `eval/criteria/p1-spec-cascade.yaml` through `eval/criteria/o4-spec-fidelity.yaml` (8 files)
- Create: `eval/tiers/seed.yaml`, `eval/tiers/tier-2.yaml`, `eval/tiers/tier-3.yaml`

- [ ] **Step 1: Create p1-spec-cascade.yaml**

```yaml
category: p1-spec-cascade
description: "did the spec cascade execute in the correct order?"
questions:
  - id: p1.1
    text: "did every feature have a proposal created before any other spec?"
    type: timestamp
    tier: seed
  - id: p1.2
    text: "did behavior_spec exist before test_spec was written?"
    type: timestamp
    tier: tier-2
  - id: p1.3
    text: "did test_spec exist before any test files were written?"
    type: timestamp
    tier: seed
  - id: p1.4
    text: "did test files exist before implementation code was written?"
    type: timestamp
    tier: tier-2
  - id: p1.5
    text: "are all spec documents non-trivial (>50 lines or substantive content)?"
    type: judgment
    tier: tier-3
  - id: p1.6
    text: "did every feature complete the full cascade (no skipped stages)?"
    type: timestamp
    tier: seed
```

- [ ] **Step 2: Create remaining 7 criteria files**

Follow the same format for p2-role-boundary.yaml, p3-orchestration.yaml, p4-ssot-integrity.yaml, o1-correctness.yaml, o2-test-quality.yaml, o3-code-quality.yaml, o4-spec-fidelity.yaml. Use the question text from the spec (section 6).

Each question gets a `tier` field: seed, tier-2, or tier-3. The seed assignments from the spec are: p1.1, p1.3, p1.6, p2.1, p2.3, o1.1, o1.2, o4.1, p4.1.

- [ ] **Step 3: Create tier files**

Create `eval/tiers/seed.yaml`:

```yaml
tier: seed
description: "foundational questions — must pass before expanding"
questions:
  - p1.1
  - p1.3
  - p1.6
  - p2.1
  - p2.3
  - o1.1
  - o1.2
  - o4.1
  - p4.1
unlock_condition: "always active"
```

Create `eval/tiers/tier-2.yaml`:

```yaml
tier: tier-2
description: "expanded questions — unlocked when seed is at 100% for 3 consecutive runs"
questions:
  - p1.2
  - p1.4
  - p2.2
  - p2.4
  - p2.5
  - p3.1
  - p3.2
  - p3.3
  - p4.2
  - p4.3
  - o1.3
  - o1.4
  - o2.1
  - o2.2
  - o3.1
  - o3.2
  - o4.2
  - o4.3
unlock_condition: "seed at 100% for 3 consecutive runs"
```

Create `eval/tiers/tier-3.yaml`:

```yaml
tier: tier-3
description: "full question set — unlocked when tier-2 is at 90%+ for 3 consecutive runs"
questions:
  - p1.5
  - p2.6
  - p3.4
  - p3.5
  - p3.6
  - p4.4
  - p4.5
  - p4.6
  - o1.5
  - o1.6
  - o2.3
  - o2.4
  - o2.5
  - o2.6
  - o3.3
  - o3.4
  - o3.5
  - o3.6
  - o4.4
  - o4.5
  - o4.6
unlock_condition: "tier-2 at 90%+ for 3 consecutive runs"
```

- [ ] **Step 4: Commit**

```bash
git add eval/criteria/ eval/tiers/
git commit -m "feat: create eval criteria and tier definitions"
```

---

### task 13: create pool role definitions

**Files:**
- Create: `eval/pools/pool-e.md`, `eval/pools/pool-r.md`, `eval/pools/pool-t.md`, `eval/pools/pool-v.md`

- [ ] **Step 1: Create pool-e.md**

```markdown
# pool-e: execution pool

## purpose
mutate templates and develop test projects using the mas system.

## permissions
- read: tpls/snapshots/workspace/ only
- write: tpls/snapshots/workspace/ only
- blind to: eval/ entirely, pass rates, scores, other pools

## instructions
you are a template mutation agent. you receive a workspace directory and a mutation directive. you modify the templates in the workspace to improve the system. you do NOT know what you are being evaluated on. just make the system better based on the directive.

when developing test projects, you follow the full mas process: spec cascade, role enforcement, all hooks. you are a normal orchestrator running a project — not an evaluator.

## constraints
- never read from eval/
- never read orchestrator/manifest.json
- never ask about pass rates or scores
- destroy workspace state between mutation and execution phases
```

- [ ] **Step 2: Create pool-t.md, pool-v.md, pool-r.md**

Follow the same format. pool-t writes check scripts from criteria (blind to artifacts). pool-v runs scripts against artifacts (blind to criteria wording). pool-r returns structured json only (blind to eval and tpls).

- [ ] **Step 3: Commit**

```bash
git add eval/pools/
git commit -m "feat: create eval pool role definitions"
```

---

### task 14: generate FROZEN.lock

**Files:**
- Create: `eval/gates/frozen_lock.py`
- Create: `eval/FROZEN.lock`

- [ ] **Step 1: Create frozen_lock.py**

Create `eval/gates/frozen_lock.py`:

```python
"""Generate and verify FROZEN.lock for eval/ directory integrity."""

import hashlib
import json
import sys
from pathlib import Path


def generate_lock(eval_dir: Path) -> dict:
    """Generate sha-256 hashes for all files in eval/ (excluding FROZEN.lock itself)."""
    hashes = {}
    for fpath in sorted(eval_dir.rglob("*")):
        if fpath.is_file() and fpath.name != "FROZEN.lock":
            rel = str(fpath.relative_to(eval_dir))
            hashes[rel] = hashlib.sha256(fpath.read_bytes()).hexdigest()
    return {"version": "1.0", "hashes": hashes}


def verify_lock(eval_dir: Path) -> tuple[bool, list[str]]:
    """Verify eval/ files match FROZEN.lock. Returns (ok, list_of_mismatches)."""
    lock_path = eval_dir / "FROZEN.lock"
    if not lock_path.exists():
        return False, ["FROZEN.lock missing"]

    lock = json.loads(lock_path.read_text())
    expected = lock.get("hashes", {})
    actual = generate_lock(eval_dir)["hashes"]

    mismatches = []
    for path, expected_hash in expected.items():
        actual_hash = actual.get(path)
        if actual_hash is None:
            mismatches.append(f"MISSING: {path}")
        elif actual_hash != expected_hash:
            mismatches.append(f"CHANGED: {path}")

    for path in actual:
        if path not in expected:
            mismatches.append(f"NEW: {path}")

    return len(mismatches) == 0, mismatches


if __name__ == "__main__":
    eval_dir = Path(__file__).parent.parent
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        ok, mismatches = verify_lock(eval_dir)
        if ok:
            print("FROZEN.lock: OK")
        else:
            print("FROZEN.lock: MISMATCH")
            for m in mismatches:
                print(f"  {m}")
            sys.exit(1)
    else:
        lock = generate_lock(eval_dir)
        lock_path = eval_dir / "FROZEN.lock"
        lock_path.write_text(json.dumps(lock, indent=2))
        print(f"Generated FROZEN.lock with {len(lock['hashes'])} entries")
```

- [ ] **Step 2: Generate the initial FROZEN.lock**

```bash
python eval/gates/frozen_lock.py
```

Expected: `Generated FROZEN.lock with N entries`

- [ ] **Step 3: Verify it passes**

```bash
python eval/gates/frozen_lock.py verify
```

Expected: `FROZEN.lock: OK`

- [ ] **Step 4: Commit**

```bash
git add eval/gates/frozen_lock.py eval/FROZEN.lock
git commit -m "feat: generate FROZEN.lock for eval integrity"
```

---

## phase 5: orchestrator manifest

### task 15: create initial manifest.json

**Files:**
- Create: `orchestrator/manifest.json`

- [ ] **Step 1: Create manifest.json**

Create `orchestrator/manifest.json`:

```json
{
  "active": "candidate-0",
  "phase": "prepare",
  "tier": "seed",
  "test_domain": null,
  "candidates": [
    {
      "id": "candidate-0",
      "parent": null,
      "status": "active",
      "mutation": null,
      "sha256": null,
      "pass_rate": {},
      "created": "2026-03-29T00:00:00Z"
    }
  ],
  "promoted": ["candidate-0"],
  "next_action": "begin self-evolution loop — run first test project against seed tier"
}
```

- [ ] **Step 2: Commit**

```bash
git add orchestrator/manifest.json
git commit -m "feat: create initial orchestrator manifest"
```

---

## phase 6: update existing hooks for new paths

### task 16: update config_loader.py for new structure

**Files:**
- Modify: `tpls/snapshots/candidate-0/cli/hooks/utils/config_loader.py`
- Modify: `tpls/snapshots/candidate-0/cli/tests/test_config_loader.py`

- [ ] **Step 1: Update config_loader.py**

The current `load_harness_config` reads `registry_path` and `harness_cli_path`. Update to also support `cli_path` (new field name):

In `config_loader.py`, update `load_harness_config` to handle both old and new field names:

```python
def load_harness_config(project_root):
    """Load .harness.json from project root."""
    harness_path = Path(project_root) / ".harness.json"
    if not harness_path.exists():
        return None
    config = json.loads(harness_path.read_text())
    # support both old and new field names
    if "cli_path" not in config and "harness_cli_path" in config:
        config["cli_path"] = config["harness_cli_path"]
    return config
```

- [ ] **Step 2: Run existing tests**

```bash
cd tpls/snapshots/candidate-0/cli && python -m pytest tests/test_config_loader.py -v && cd -
```

Expected: all existing tests pass

- [ ] **Step 3: Commit**

```bash
git add tpls/snapshots/candidate-0/cli/hooks/utils/config_loader.py
git commit -m "fix: update config_loader for new harness.json field names"
```

---

### task 17: update bootstrap.py for new structure

**Files:**
- Modify: `tpls/snapshots/candidate-0/cli/setup/bootstrap.py`

- [ ] **Step 1: Update bootstrap to use tpls/ as template source**

The current bootstrap copies from `mas-harness/` (the old path). Update to copy from `tpls/sys/tpl-proj/` (resolved through symlink) and `tpls/cli/`.

Key changes to `create_registry()`:
- template source: `tpls/sys/tpl-proj/` instead of `mas-harness/`
- cli source: `tpls/cli/` instead of `harness-cli/`
- output structure: `regs/<name>-regs/ssot/` and `regs/<name>-regs/cli/`

Key changes to `bootstrap()`:
- registry dir default: `regs/` instead of root
- harness config: writes `cli_path` instead of `harness_cli_path`

This is a significant rewrite of bootstrap.py. The full implementation should be done by a worker subagent with the existing test suite as a safety net.

- [ ] **Step 2: Update tests to match new paths**

Update `test_bootstrap.py` to expect the new directory structure (`regs/<name>-regs/ssot/` and `regs/<name>-regs/cli/`).

- [ ] **Step 3: Run updated tests**

```bash
cd tpls/snapshots/candidate-0/cli && python -m pytest tests/test_bootstrap.py -v && cd -
```

Expected: all tests pass

- [ ] **Step 4: Commit**

```bash
git add tpls/snapshots/candidate-0/cli/setup/bootstrap.py
git add tpls/snapshots/candidate-0/cli/tests/test_bootstrap.py
git commit -m "feat: update bootstrap for omni directory structure"
```

---

## phase 7: run full test suite

### task 18: verify all tests pass

**Files:** all test files

- [ ] **Step 1: Run python tests**

```bash
cd tpls/snapshots/candidate-0/cli && python -m pytest tests/ -v && cd -
```

Expected: all tests pass

- [ ] **Step 2: Run typescript tests**

```bash
cd tpls/snapshots/candidate-0/cli && npm install && npx vitest run && cd -
```

Expected: all tests pass

- [ ] **Step 3: Verify FROZEN.lock**

```bash
python eval/gates/frozen_lock.py verify
```

Expected: `FROZEN.lock: OK`

- [ ] **Step 4: Verify symlink chain**

```bash
ls -la tpls/sys/tpl-proj/blueprint/orchestrate-members/ | head -5
cat orchestrator/manifest.json | python -m json.tool | head -5
```

Expected: symlinks resolve correctly, manifest is valid json

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "chore: verify full test suite passes on omni structure"
```

---

## summary

| phase | tasks | what it produces |
|-------|-------|------------------|
| 1: directory restructure | 1-7 | omni layout with eval/, tpls/, regs/, orchestrator/ |
| 2: snapshot system | 8 | snapshot_manager.py with create/promote/rollback |
| 3: new hooks | 9-11 | layer_fence, blueprint_freeze, destructive_git_gate |
| 4: eval harness | 12-14 | criteria yamls, tier files, pool defs, FROZEN.lock |
| 5: orchestrator manifest | 15 | initial manifest.json |
| 6: update existing hooks | 16-17 | config_loader + bootstrap adapted to new paths |
| 7: verify | 18 | all tests green, symlinks working |

**note on chmod a-w**: the spec requires `chmod a-w` on eval/ and promoted snapshots. this is an os-level operation that should be applied after each phase:
- after task 14 (FROZEN.lock generated): `chmod -R a-w eval/`
- after task 5 (candidate-0 created): `chmod -R a-w tpls/snapshots/candidate-0/`
- the `create_candidate()` function in snapshot_manager.py should call `chmod -R a-w` on new snapshots after capture (add to implementation)

**not included in this plan** (separate plans needed):
- evolution loop implementation (orchestrator/loop.py, dispatch.py, anti_gaming.py) — depends on this restructure being complete
- `/opsx` command implementation — external CLI tool
- test project creation (regs/test-regs/*) — depends on evolution loop
- eval/gates/ implementation (pool_isolation.py, evidence_validator.py, spot_check.py) — depends on evolution loop
