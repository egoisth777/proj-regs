---
slug: workflow
type: workflow
status: active
last_updated: 2026-05-05
topic: process
---

# End-to-End Feature Workflow

## Overview

Every feature ships through 5 phases: OpenSpec → Implementation → Review → PR + Merge → Wrap-up. The pattern is enforced for any user-visible change. Trivial doc tweaks may skip Phase 1.

## Phase 1 — OpenSpec (design-first)

1. Maintainer aligns on scope. Open questions surfaced as Q1/Q2/... before draft.
2. Cut feature branch from main: `git checkout -b feat-<short-name> main`.
3. mkdir `openspec/changes/feat-<short-name>/`.
4. Dispatch parallel subagents:
   - Worker O1 → `proposal.md` (why, scope, out-of-scope, acceptance bar)
   - Worker O2 → `design.md` (architecture, algorithm, file-level changes, edge cases)
   - Worker O3 → `tasks.md` (numbered checklist, stage breakdown)
5. Wait ALL openspec workers complete. Single agent reviews triplet — surface inconsistencies between proposal/design/tasks.
6. Apply review fix-ups (separate workers — never the original writers).
7. Maintainer signs off on triplet OR raises additional Q for re-alignment.

## Phase 2 — Implementation (code + proofs)

1. **Rule 8 gate (non-simple algorithms ONLY):** Lean4 proof MUST land green BEFORE production-code impl. `lake build` exits 0, zero `sorry`, zero `admit`, axiom counts unchanged unless justified in `Bridge.lean` / `Types.lean`. Single Lean worker (proofs are serial).
2. After Lean green: dispatch parallel implementation workers.
3. Worker partition: split by file. Avoid 2 workers touching the same file. If a single file needs many changes, bundle into one worker.
4. **Per-worker quick check (iterative inner loop):** the language's incremental compile / targeted test for the worker's modified files. Reports clean/dirty during iteration.
5. Bump version per the project's release manifest (e.g. `Cargo.toml` for Rust, `pyproject.toml` for Python, `package.json` for JS/TS). Update any version-mirror files that pin the same number (test fixtures, generated man pages, schema files). All version mirrors MUST move in lockstep with the canonical version.
6. Update `CHANGELOG.md` + `.omne/archive/history.md` (v2 will be aggregator-driven; v1 is hand-edited).
7. **Full pre-push gate sequence — MUST exit 0 before push to remote:** the project's full lint / build / test / doc-build matrix. Add proof-build (e.g. `lake build`) and any axiom / invariant audits if the project uses formal verification.

## Phase 3 — Review (parallel + Codex)

1. Dispatch 4-6 parallel subagent reviewers, each with a distinct lens (proof-to-impl correspondence / correctness / test coverage / SemVer + BC / concurrency safety / idiomatic style for the project's language / etc).
2. Reviewers return severity-tagged findings (BLOCKER / HIGH / MED / LOW / NIT).
3. Triage: separate must-fix (correctness adjacent) from defer (cosmetic/scope-creep).
4. Dispatch fix-up workers for must-fix items. Re-run gates.
5. Optional second-round: Codex rescue review via `Skill: codex:rescue` (or skip if no return per maintainer escalation).
6. Apply codex fix-ups if any. Re-run gates.

## Phase 4 — PR + Merge + Ship

1. Conventional Commit: `<type>(<scope>): <subject>` with body. NO `Co-Authored-By:` trailer per discipline #13. NO AI/assistant/generated/Anthropic/Claude mentions.
2. `git push origin feat-<short-name>`.
3. `gh pr create --base main --head feat-<short-name>` with full PR body covering summary, locked decisions, test plan, behavior change matrix, migration notes, SemVer label.
4. Watch CI: `gh pr checks <num> --watch --interval 30`. ALL gates the project defines (platform builds, lint, type-check, proof gate, MSRV / runtime-version matrix, dependency audit, axiom policy) MUST pass.
5. If CI fails on something local gates missed: file as a process-gap entry in next progress.md endpoint. Fix + push + re-watch.
6. After CI green: maintainer authorizes `gh pr merge <num> --squash --delete-branch`.
7. `git checkout main && git pull origin main` to update local.
8. **Registry publish (if applicable):** topo order — dependency-free packages first. Wait for index propagation between dependent packages. Use language-specific dirty-tree allowances ONLY if drift is non-source (telemetry artefacts, line-ending normalisation).
9. **Tag:** `git tag -a v<version> -m "..." <commit>` then `git push origin v<version>`.

## Phase 5 — Wrap-up (session boundary)

1. Append new `## Endpoint (YYYY-MM-DD, branch — short-title)` section to `progress.md` (canonical state per discipline #5).
2. Update top `## Where we are` block.
3. Promote draft entries in `.omne/archive/history.md` to SHIPPED with date + commit SHA.
4. Commit `progress.md` (consuming-repo-tracked) + `history.md` (SSOT-tracked, separate repo).
5. Carry-forwards: list deferred items in the new endpoint for next-cycle pickup.
