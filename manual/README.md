# omni System Manual

omni is a Multi-Agent System (MAS) with self-evolution capability. It orchestrates specialized AI agents through a structured workflow to produce software, enforcing quality through a spec cascade, role boundaries, and an automated evaluation loop that iteratively improves the system's own templates.

This manual covers every major subsystem. Start with the system overview for the big picture, then follow links to specific topics.

## Table of Contents

1. [System Overview](system-overview.md) -- Architecture, delegation model, and core concepts.
2. [SSoT Registries](registries.md) -- The Single Source of Truth registry: blueprint vs runtime, context map, harness config.
3. [Templates](templates.md) -- The `tpls/` subsystem: snapshots, CLI tools, hooks, and snapshot management.
4. [Evaluation Framework](eval-framework.md) -- Criteria, tier progression, check scripts, gates, and FROZEN.lock integrity.
5. [Evolution Loop](evolution-loop.md) -- The 5-phase cycle: prepare, mutate, execute, verify, decide.
6. [Eval-Loop Guide](eval-loop-guide.md) -- Using `opsx.py` CLI commands and running the evolution loop.
7. [Agent Roles](agent-roles.md) -- All 12 agent roles: orchestrator, team-lead, worker, spec writers, SDETs, and more.
8. [Spec Cascade](spec-cascade.md) -- The mandatory workflow: proposal, behavior spec, test spec, tests, code.
9. [Knowledge Graph](knowledge-graph.md) -- Retrieval-augmented documentation: generation, auto-regeneration, and agent integration.

## Quick Reference

| Path | Purpose |
|---|---|
| `regs/omni-regs/ssot/` | SSoT registry (blueprint + runtime state) |
| `tpls/` | Templates (snapshots, CLI tools, hooks) |
| `eval/` | Evaluation framework (criteria, gates, scripts, tiers, pools) |
| `eval-loop/` | Evolution loop engine (loop, dispatch, anti-gaming, opsx CLI) |
| `.harness.json` | Project harness config |
| `docs/` | Planning documents and design specs (e.g., `docs/superpowers/`) |
| `.agents` | Symlink to agent role definitions |
| `CLAUDE.md` | Agent instructions for the MAS |
| `.understand-anything/` | Knowledge graph (generated, gitignored) |
| `.githooks/` | Git hooks (post-commit graph regeneration) |
