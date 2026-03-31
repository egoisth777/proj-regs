# Templates

The `tpls/` directory contains the templates that define how projects are structured, how CLI tools work, and how hooks enforce system rules. The evolution loop mutates these templates to improve the system over time.

## Directory Structure

```
tpls/
  cli/           -- CLI tools, hooks, setup scripts
  sys/           -- System-level templates (project structure templates)
  snapshots/     -- Snapshot management for evolution loop
```

## Snapshots

The `tpls/snapshots/` directory manages versioned snapshots of the template system. This is the core of the evolution loop's mutation and selection mechanism.

### Layout

```
tpls/snapshots/
  candidate-0/     -- The baseline (original) snapshot
    cli/           -- CLI tools for this snapshot
    sys/           -- System templates for this snapshot
    meta.json      -- Metadata about this snapshot
  active           -- Symlink pointing to the current best snapshot
  workspace/       -- Temporary mutable copy (exists only during mutation)
```

### How Snapshots Work

1. **candidate-0** is the initial baseline snapshot containing the original templates.
2. **active** is a symlink that always points to the currently promoted snapshot (e.g., `candidate-0`).
3. During evolution, a **workspace/** directory is created by copying the active snapshot's `sys/` and `cli/` directories. Pool-E agents mutate the workspace.
4. After mutation, the workspace is captured as a new candidate (e.g., `candidate-1`). The workspace is destroyed after capture.
5. If the new candidate scores better than the active one, it is promoted (the `active` symlink is updated to point to the new candidate).

### Snapshot Management

The snapshot lifecycle is managed by `tpls/cli/hooks/utils/snapshot_manager.py` (imported by the orchestrator). Key operations:

- **create_candidate**: Captures a workspace as a new candidate. Computes a SHA-256 hash to detect duplicates. Records the parent candidate ID and mutation description.
- **promote_candidate**: Updates the `active` symlink to point to a promoted candidate. Records the promotion in the manifest.
- **rollback_to**: Reverts the `active` symlink to a previous candidate.
- **load_manifest**: Reads the evolution loop manifest (`orchestrator/manifest.json`).

## CLI Tools

The `tpls/cli/` directory contains the CLI tooling used by projects:

| Path | Purpose |
|---|---|
| `context/` | Context management utilities |
| `hooks/` | Git hooks and enforcement utilities |
| `setup/` | Project initialization scripts |
| `tests/` | Test infrastructure |
| `package.json` | Node.js dependencies |
| `pyproject.toml` | Python dependencies |

### Hooks

Hooks enforce system rules at commit time, including:

- Role boundary enforcement (agents cannot write outside their scope)
- Spec cascade ordering (ensures specs exist before tests, tests before code)
- Path-based write restrictions

## System Templates

The `tpls/sys/` directory contains templates for project structure:

| Path | Purpose |
|---|---|
| `tpl-proj/` | Project structure templates |
| `tpl-research/` | Research document templates |

These templates are used by `init_project.py` (in `tpls/cli/setup/`) to scaffold new projects that follow the omni conventions.
