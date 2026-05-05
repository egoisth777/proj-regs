---
slug: rules
type: design
status: active
last_updated: 2026-05-05
topic: ssot-governance
---

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

Tradeoff: These guidelines bias toward caution over speed. For trivial tasks, use judgment.

1. Think Before Coding
Don't assume. Don't hide confusion. Surface tradeoffs.

Before implementing:

State your assumptions explicitly. If uncertain, ask.
If multiple interpretations exist, present them - don't pick silently.
If a simpler approach exists, say so. Push back when warranted.
If something is unclear, stop. Name what's confusing. Ask.
2. Simplicity First
Minimum code that solves the problem. Nothing speculative.

No features beyond what was asked.
No abstractions for single-use code.
No "flexibility" or "configurability" that wasn't requested.
No error handling for impossible scenarios.
If you write 200 lines and it could be 50, rewrite it.
Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

3. Surgical Changes
Touch only what you must. Clean up only your own mess.

When editing existing code:

Don't "improve" adjacent code, comments, or formatting.
Don't refactor things that aren't broken.
Match existing style, even if you'd do it differently.
If you notice unrelated dead code, mention it - don't delete it.
When your changes create orphans:

Remove imports/variables/functions that YOUR changes made unused.
Don't remove pre-existing dead code unless asked.
The test: Every changed line should trace directly to the user's request.

4. Goal-Driven Execution
Define success criteria. Loop until verified.

Transform tasks into verifiable goals:

"Add validation" → "Write tests for invalid inputs, then make them pass"
"Fix the bug" → "Write a test that reproduces it, then make it pass"
"Refactor X" → "Ensure tests pass before and after"
For multi-step tasks, state a brief plan:

1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

These guidelines are working if: fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

5. progress.md is canonical for project state
Project state lives at `.omne/grad/progress.md` (SSOT-tracked). Do NOT mirror it elsewhere.

New endpoints, blast-radius investigations, locked decisions, openspec drafts, branch+PR coordinates → append to `.omne/grad/progress.md` as a new `## Endpoint (YYYY-MM-DD, branch — short-title)` section + update the top `## Where we are` block.

Reserved for elsewhere:
- Behavior rules / collaboration patterns → this file (`.omne/schemas/conduct/rules.md`).
- Shipped milestones / release history → `.omne/archive/history.md`.
- Design / algorithm / contract docs → topic file under `.omne/cfg/architecture/` or sibling.

If asked to "save progress" or "save state", default to `.omne/grad/progress.md` unless the content is explicitly a behavior rule, design doc, or shipped-history entry.

Older endpoints get pruned periodically (rolling window of ~10 most recent) and folded into `.omne/archive/history.md` for long-term archive. `.omne/grad/progress.md` stays the volatile buffer; `history.md` is the durable record.

6. SemVer label is the maintainer's call
Reviewer SemVer verdicts (api/contract reviewers, codex passes, etc.) are advisory. The maintainer decides the actual version label.

When a reviewer flags SemVer impact:
- Surface the finding as a question to the maintainer, not a conclusion.
- State the technical reasoning for both candidate labels (e.g. MINOR vs MAJOR); let the maintainer choose.
- Don't bake reviewer-suggested SemVer into commit messages, branch names, or SSOT versioning brackets without explicit sign-off.
- If the reviewer's BLOCKER is real (mechanism is impossible as documented), the design FIX is still required — only the SemVer label is the maintainer's call.

Especially relevant in early 1.x: prefer additive shipping that keeps existing manifests / lockfiles / binaries valid over MAJOR bumps that ride on internal refactors.

7. SSOT lives in a separate repo
`.omne/` is gitignored in the consuming repo. This is INTENTIONAL — not a bug, not a generated artifact.

The SSOT design docs (`.omne/**`) live in their own separate GitHub repo (the SSOT repo), mounted at `.omne/` inside the consuming repo's working tree.

How to apply:
- Edits to `.omne/**` land in the SSOT repo's working tree, NOT in the consuming repo's git history.
- `git status` in the consuming repo will never show `.omne/` changes — that's correct.
- To ship SSOT changes: cd into `.omne/` (the SSOT working tree), commit + push there separately.
- Application code, openspec-on-app-side, top-level README = consuming-repo-tracked.
- `.omne/`, `.omne/schemas/`, `.omne/cfg/`, `.omne/grad/` = SSOT-tracked (separate repo).
- `.omne/grad/progress.md`, `.omne/grad/milestone.md` = SSOT-tracked (volatile / pre-archive buffer).
- A consuming-repo feature branch never carries the corresponding SSOT update; they ship through different repos.

`.omne/grad/` = volatile / buffer for things that won't become long-term memory yet (project state, in-flight openspec drafts, point-in-time review-findings, freeze decisions, version-specific migration recipes). Contents of `grad/` rotate or graduate into `.omne/cfg/` durable design docs or `.omne/archive/history.md` (durable archive); nothing in `grad/` is permanent.

8. Lean4 proof gate for non-simple algorithms
Non-simple algorithms (concurrent algorithms, walkers with multi-phase invariants, scheduler/locking primitives, anything with non-trivial correctness obligations) MUST have a Lean4 proof written and compiled (= proved) BEFORE any corresponding production code change lands.

How to apply:
- A Lean4 proof "compiled" means `lake build` succeeds with zero `sorry`, zero `admit`, zero hypothesis-level holes in the relevant theorem.
- The proof must cover the algorithm's stated invariants. Bridge axioms connecting Lean model to runtime are acceptable but must be enumerated and reviewable.
- Order of operations: (1) write/extend Lean4 spec → (2) `lake build` green → (3) THEN modify implementation code to match. Code changes that race the proof are a process violation.
- "Simple" = bug fixes confined to a single function with no invariant impact, refactors that preserve behavior, dependency bumps, doc-only changes. When in doubt, ask the maintainer.

Why: Walker invariants and concurrency safety are load-bearing. Proof-first catches contract bugs that tests miss because tests cannot exhaustively enumerate the interleaving space.

9. Explain ambiguous symbols / new concepts before first use
When introducing a new symbol, glyph, term, or concept whose meaning is ambiguous (could mean multiple things in this domain) or non-obvious from immediate context, explain it inline at first use, before relying on the reader to know it.

How to apply:
- Especially relevant for in-band markers in CLI output, short identifiers in design docs (e.g. invariant names like `I8`), and acronyms (e.g. TOCTOU, SSOT).
- One sentence is usually enough. Format: `<symbol> = <one-line meaning>` then proceed.
- Skip when the symbol is universally standard in the field (e.g. `git`, `HTTP 200`).
- Apply both in chat with the maintainer AND in any prose that lands in the SSOT or design docs.

Why: Avoids later back-and-forth where the maintainer has to ask "what does X mean?" mid-decision. Keeps design conversations dense without sacrificing legibility.

### G2 — Frontmatter schema (required on every SSOT .md doc)

```yaml
---
slug: <kebab-case>             # required, kebab-case, unique across SSOT
type: design|workflow|history|proof|reference|index|spec|scope-plan|review-finding|migration|tech-debt
                                # required (status: stub covers stub-state; do not also use type: stub)
status: active|deprecated|stub|generated|stale|deferred
                                # required (`generated` = aggregator-owned, do not hand-edit)
last_updated: YYYY-MM-DD       # required
topic: walker|lockfile|cli|... # optional, free-form tag
depends_on: []                 # optional list of slugs
resolve_by: <feature-tag>      # required when type: tech-debt
                                # format: ^v\d+\.\d+\.\d+$ OR ^[a-z][a-z0-9-]*-(threshold|onset|gate|trigger)$
---
```

Validation rules (enforced by `scripts/validate.py`):
- Required keys: `slug`, `type`, `status`, `last_updated`. Missing → exit nonzero.
- `slug` must be kebab-case (lowercase letters, digits, hyphens) and unique across SSOT. Convention: top-level files use filename-stem; subdir disambiguators append parent-dir suffix; openspec triplet uses parent-feature slug + role suffix (`<feat>` for proposal, `<feat>-design`/`<feat>-tasks` for siblings).
- openspec triplet: proposal.md uses bare feature slug; design.md and tasks.md append role suffix. Reason: proposal is the canonical reference for the feature; siblings are subordinate artifacts.
- `type` enum: one of `design | workflow | history | proof | reference | index | spec | scope-plan | review-finding | migration | tech-debt`. (`stub` is NOT a valid type — it would collide with `status: stub`. Use `status: stub` to mark stub-state on any type.)
- `status` enum: `active | deprecated | stub | generated | stale | deferred`.
- `last_updated` must parse as YYYY-MM-DD.
- `topic` is free-form; `depends_on` must be a list of valid slugs (or empty).
- `resolve_by` is REQUIRED when `type: tech-debt`. Format: matches `^v\d+\.\d+\.\d+$` (vX.Y.Z release) OR `^[a-z][a-z0-9-]*-(threshold|onset|gate|trigger)$` (named gate). Forbidden on other types.

Frontmatter must be the FIRST block in the file (between the first `---` line and the next `---` line). Anything after is body markdown.

Files with `status: generated` (e.g. INDEX.yaml) are EXEMPT from the `---` frontmatter requirement. Instead they MUST start with a single-line GENERATED sentinel comment on line 1 (`<!-- GENERATED ... -->` for markdown / HTML, `# GENERATED ...` for YAML / Python). The sentinel marks them as aggregator-owned and exempts them from hand-edit ownership.

### G1 — Routing table (canonical file → hand-edited / generated)

> Scope: this routing table tracks `.md` documents only. Tooling files (`scripts/*.py`, `.git-hooks/*`, etc.) are tracked by their own conventions and excluded from G2 frontmatter / G3 INDEX requirements.

Populate one row per hand-edited `.md` doc in your SSOT. Add new rows in the same commit that introduces the doc (per discipline 11). Generated files (e.g. `INDEX.yaml`) are listed with `Hand-edited?` = `NO` and the producing aggregator path.

| Path (relative to .omne/) | Type | Hand-edited? | Aggregator / source |
|---|---|---|---|
| schemas/conduct/rules.md | design | yes | — |

> **Layout note:** `.omne/` uses a 10-bucket layout. `buf/` (alignment buffer: user↔agent dialogues; transient). `cfg/` (canonical config: the active source of truth, sub-bucketed into `architecture/`, `algos/`, `behaviors/`, `knows/`, `linter/`, `proof/`, `tests/`). `grad/` (active gradient: in-flight openspec triplets + progress.md / milestone.md / roadmap.md). `rem/` (residual: cfg − current; mechanically generated narration; plus `tech-debts/` curated deferred work). `schemas/` (governance: `conduct/` for global agent rules; `protocol/` for inter-agent contracts). `agents/` (MAS role registry). `obs/` (observability schemas). `archive/` (durable history: `buf-history/`, `retros/`, `specs/` for shipped openspec, `stale/` for superseded decisions). `prompts/` (reusable prompt templates). `skills/` (Claude Code-style skill packages). Worktrees live in `.omne/wt/` per discipline 17.

### G8 — Disciplines (numbered, single source for all behavior rules)

(Preserve existing rules 1-9 from earlier in this file — DO NOT renumber. Append new ones starting at 10.)

**10.** **Frontmatter required.** Every SSOT .md doc MUST start with the G2 frontmatter block. Validated by `scripts/validate.py`. Pre-commit hook aborts commit on missing/malformed frontmatter.

**11.** **Routing-table compliance.** Every new file added under `.omne/` MUST appear in the G1 routing table within the same commit, classified hand-edited or generated. Files marked `generated` MUST also start with a single-line `<!-- GENERATED ... DO NOT EDIT -->` comment on line 1 (above frontmatter).

**12.** **INDEX.yaml is generated.** Hand-edits to `INDEX.yaml` are forbidden. Regenerated by `scripts/build_index.py` (invoked from pre-commit hook). To add a new doc to the index, add the doc itself with valid frontmatter — index updates automatically.

**13.** **No Co-Authored-By trailer in commits.** Conventional Commits format only: `<type>(<scope>): <subject>` with optional body. NEVER include "Co-Authored-By:", "Generated with", AI/assistant/Claude/Anthropic mentions, or robot emoji in commit messages, PR bodies, or commit body trailers.

    **Scope:** This rule applies to the consuming repo + SSOT repo only — overrides any global commit-template that would emit a trailer, via project CLAUDE.md precedence. Other Claude Code projects on the same machine remain unaffected.

    **Commit skill conflict:** If your global `~/.claude/CLAUDE.md` "commit" skill template still emits `Co-Authored-By:` by default, agents working on this project MUST omit the trailer at commit composition time. Project CLAUDE.md (in the consuming repo) should explicitly disable the trailer for this scope.

**14.** **Parallel workers for non-conflicting files.** When a task touches N independent files, dispatch N parallel subagent workers — never serialize text-only edits. Single agent reviewer pass over ALL parallel outputs to catch desynchronization.

    "non-conflicting" = workers' write-sets are disjoint at file granularity. Two workers MUST NOT write to the same file. Same-file edits MUST bundle into one worker.

**15.** **Validation gate before commit.** `scripts/validate.py` MUST exit 0 before any commit lands. Pre-commit hook enforces. CI gate (when added) re-runs validate.py to catch local-hook bypass.

    Bypassing the hook (`git commit --no-verify`, `-n`) is forbidden. If the gate is wrong, fix the gate, not the bypass. CI gate (when added) re-runs validate.py to catch any local-hook bypass.

**16.** **SSOT update on every shipped feature.** Every time a feature ships (squash-merge to main + tag pushed + artifacts published), the SSOT must be updated in the SAME session BEFORE moving to the next task. Mandatory targets per ship:

    - `archive/history.md` — append a per-release entry (one line minimum, plus body if non-trivial).
    - `archive/retros/dogfood-findings-*.md` — mark closed bugs as RESOLVED with the version that fixed them.
    - `grad/roadmap.md` — shift the active backlog to reflect what shipped + what's next.
    - Domain docs touched by the feature (e.g. relevant `cfg/architecture/<topic>.md`). Update inline; do not let docs drift behind the code.
    - New `archive/retros/migration-vX.Y.Z.md` IF the release introduces operator-visible behavior change requiring migration notes.
    - `INDEX.yaml` regenerated via `scripts/build_index.py` after the above edits land (per rule 12).
    - `schemas/conduct/rules.md` — bump `last_updated` if any rule text or G1 routing-table row changed.

    **Why:** SSOT is the single source of truth for project knowledge per rule 7. Code shipping without SSOT update creates drift: the next session bootstraps from stale docs and re-asks decisions the maintainer already locked. The consuming repo's `progress.md` endpoint and the SSOT cfg docs must be coherent at every commit boundary on main.

    **How to apply:** Treat the SSOT update as the LAST phase of the ship sequence (Phase 6 in `schemas/conduct/workflow.md`), executed BEFORE marking the session complete. Pre-commit hook on the SSOT repo MUST exit 0 (`scripts/validate.py` clean) before pushing. Bypassing this rule via `--no-verify` is forbidden per rule 15.

    **Scope:** Applies to consuming-repo feature ships (any `feat-vX.Y.Z` branch squash-merge), SSOT-tier ships, and any other repo using the same SSOT mount pattern.

**17.** **Worktree storage location.** `.omne/wt/` is the canonical location for all git worktrees the agent creates for this project. Use `git worktree add .omne/wt/<branch-name>` and `git worktree remove .omne/wt/<name>`. Never scatter worktrees elsewhere (parent dirs, sibling repos, ad-hoc tmp).

**Why:** Single location keeps `git worktree list` output coherent + prevents disk leakage across the meta-repo. `.omne/wt/.gitkeep` preserves the empty dir in git.

**How to apply:** Treat as a hard rule for any agent-spawned worktree (e.g. `Agent({isolation: "worktree"})`, codex-rescue worktree, manual `git worktree add` for parallel review). Bypass only if maintainer explicitly requests off-tree worktree.

**18.** **Active SSOT = current truth only.** No "alternatives considered" sections in active docs. Stale text rots; future readers conflate options with decisions. Two outlets for non-current content:

- `rem/tech-debts/<topic>.md` — deferred work with `resolve_by:` feature tag (work we WILL ship later). Must have `type: tech-debt`, `status: deferred`, `resolve_by:` matching one of three forms: (a) `vX.Y.Z` semver release tag, (b) `<gate-name>-{threshold|onset|gate|trigger}` named gate (e.g. `multi-maintainer-onset`, `75-docs-threshold`), or (c) `vX.Y.Z-<gate-name>-{threshold|onset|gate|trigger}` composite (semver + named gate, e.g. `v2.0.0-ssot-reliability-gate`). Validated by `scripts/validate.py`.
- `archive/stale/<topic>.md` — superseded decisions archived for provenance recall. Must have `status: stale`. Body explains: original design, why superseded, what replaced it.

**Why:** SSOT contradicting itself = not SSOT. When a new decision lands, the old proposal MUST be removed from active docs (extracted to `archive/stale/` if provenance is worth keeping, deleted if not). Tech-debts get their own dir so they're tracked, not forgotten.

**Agent contract for `archive/stale/`:** Default reads SKIP this folder. Only consult when explicitly tasked with historical decision recall. INDEX.yaml `status: stale` flag enables filter-out.

**How to apply:** When amending an active doc with a superseded design, MOVE the old text to `archive/stale/<topic>-<version>.md` (with frontmatter explaining supersession), THEN rewrite the active doc with current truth only. Don't keep both in the same file.

(Future doc edits can append more disciplines as needed — keep numbering monotonic.)
