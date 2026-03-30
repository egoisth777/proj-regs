# omni system design spec

## 1. overview

omni is a multi-agent system (mas) harness that manages software projects through ai agent orchestration. it has two modes:

- **self-evolution**: an automated loop that improves the system's own templates by running test projects, measuring pass rates against yes/no questions, and keeping mutations that improve scores
- **project use**: a human-driven mode where a user collaborates with an orchestrator agent to design and build real software projects through a disciplined spec cascade

the system is built on three principles:
- **stateless orchestrator**: the orchestrator clears its context at 40% capacity. all state is externalized in files. a user can resume at any point by reading the same state files.
- **snapshot immutability**: every evolution candidate is a frozen copy. rollback is a pointer swap. previous states are never corrupted.
- **layered one-way dependencies**: eval depends on nothing. templates depend on eval. registries depend on templates. artifacts depend on registries. information flows downward only.

---

## 2. directory structure

```
omni/
├── eval/                                    # frozen examiner
│   ├── criteria/                            # 48 yes/no questions, 8 categories
│   │   ├── p1-spec-cascade.yaml
│   │   ├── p2-role-boundary.yaml
│   │   ├── p3-orchestration.yaml
│   │   ├── p4-ssot-integrity.yaml
│   │   ├── o1-correctness.yaml
│   │   ├── o2-test-quality.yaml
│   │   ├── o3-code-quality.yaml
│   │   └── o4-spec-fidelity.yaml
│   ├── tiers/                               # question unlock tiers
│   │   ├── seed.yaml                        # ~10 foundational questions
│   │   ├── tier-2.yaml
│   │   └── tier-3.yaml
│   ├── scripts/                             # pool t check scripts (frozen per cycle)
│   ├── pools/                               # pool role definitions (eval-owned)
│   │   ├── pool-r.md
│   │   ├── pool-e.md
│   │   ├── pool-t.md
│   │   └── pool-v.md
│   ├── gates/                               # anti-gaming enforcement
│   │   ├── pool_isolation.py
│   │   ├── evidence_validator.py
│   │   └── spot_check.py
│   └── FROZEN.lock                          # sha-256 manifest of all eval/ files
│
├── tpls/                                    # evolvable templates
│   ├── sys/ -> snapshots/active/sys/        # symlink to active snapshot
│   ├── cli/ -> snapshots/active/cli/        # symlink to active snapshot
│   └── snapshots/
│       ├── active -> candidate-N/           # pointer to current promoted
│       ├── candidate-0/                     # genesis baseline
│       │   ├── sys/
│       │   │   ├── tpl-proj/
│       │   │   │   ├── 00-project-memory.md
│       │   │   │   ├── context_map.json
│       │   │   │   ├── blueprint/
│       │   │   │   │   ├── design/
│       │   │   │   │   │   ├── architecture_overview.md
│       │   │   │   │   │   ├── design_principles.md
│       │   │   │   │   │   └── api_mapping.md
│       │   │   │   │   ├── engineering/
│       │   │   │   │   │   ├── dev_workflow.md
│       │   │   │   │   │   ├── testing_strategy.md
│       │   │   │   │   │   └── performance_goals.md
│       │   │   │   │   ├── orchestrate-members/
│       │   │   │   │   │   ├── orchestrator.md
│       │   │   │   │   │   ├── worker.md
│       │   │   │   │   │   ├── team-lead.md
│       │   │   │   │   │   ├── sdet.md
│       │   │   │   │   │   ├── behavior-spec-writer.md
│       │   │   │   │   │   ├── test-spec-writer.md
│       │   │   │   │   │   ├── auditor.md
│       │   │   │   │   │   ├── sonders.md
│       │   │   │   │   │   ├── negator.md
│       │   │   │   │   │   └── regression-runner.md
│       │   │   │   │   └── planning/
│       │   │   │   │       └── roadmap.md
│       │   │   │   └── runtime/
│       │   │   │       ├── active_sprint.md
│       │   │   │       ├── backlog.md
│       │   │   │       ├── milestones.md
│       │   │   │       ├── resolved_bugs.md
│       │   │   │       └── openspec/
│       │   │   │           ├── index.md
│       │   │   │           ├── changes/
│       │   │   │           ├── archive/
│       │   │   │           └── template/
│       │   │   │               ├── proposal.md
│       │   │   │               ├── behavior_spec.md
│       │   │   │               ├── test_spec.md
│       │   │   │               ├── tasks.md
│       │   │   │               └── status.md
│       │   │   └── tpl-research/
│       │   ├── cli/
│       │   │   ├── hooks/
│       │   │   │   ├── path_validator.py
│       │   │   │   ├── layer_fence.py
│       │   │   │   ├── spec_cascade_gate.py
│       │   │   │   ├── blueprint_freeze.py
│       │   │   │   └── destructive_git_gate.py
│       │   │   ├── context/
│       │   │   │   └── inject.py
│       │   │   └── setup/
│       │   │       ├── bootstrap.py
│       │   │       └── templates/
│       │   │           ├── CLAUDE.md.tpl
│       │   │           └── AGENTS.md.tpl
│       │   └── meta.json
│       ├── candidate-N/
│       │   ├── sys/
│       │   ├── cli/
│       │   └── meta.json
│       └── workspace/                       # ephemeral, destroyed after snapshot
│
├── regs/                                    # instantiated registries
│   ├── omni-regs/                           # self-referential
│   │   ├── cli/
│   │   └── ssot/
│   ├── test-regs/                           # evolution loop targets
│   │   ├── cli-todo-regs/
│   │   │   ├── manifest.yaml
│   │   │   ├── cli/
│   │   │   └── ssot/
│   │   ├── frontend-x-regs/
│   │   ├── backend-api-regs/
│   │   └── ...
│   └── <real-proj>-regs/                    # user projects
│       ├── cli/
│       └── ssot/
│
├── orchestrator/
│   ├── manifest.json                        # the one state file
│   ├── loop.py
│   ├── dispatch.py
│   └── anti_gaming.py
│
└── docs/
```

### dependency direction

```
eval  <--  tpls  <--  regs  <--  artifacts (external repos)
  ^          ^
  └── orchestrator/manifest.json
```

each layer depends only on the layer below. no upward or lateral references. the orchestrator reads eval verdicts and mutates tpls through pools — the only controlled violation of one-way flow.

---

## 3. layer rules

### eval (frozen)

- **never auto-modified**. changes require a human-gated pr on a dedicated branch.
- protected by three independent mechanisms:
  1. `chmod a-w` — os-level, kernel-enforced. no process can write regardless of agent behavior.
  2. `FROZEN.lock` — sha-256 hash of every file in eval/. a pre-commit hook rejects any commit that alters eval/ unless on a human-gated branch. ci verifies the manifest.
  3. `layer_fence.py` — hook-level. blocks any agent write targeting eval/ based on pool assignment.
- contains its own pool role definitions in `eval/pools/`. these are separate from and independent of the project role definitions in `tpls/sys/tpl-proj/blueprint/orchestrate-members/`.

### tpls (evolvable, snapshot-immutable)

- the mutation surface for the self-evolution loop. only `tpls/sys/` and `tpls/cli/` are modified.
- every mutation produces a new immutable snapshot under `tpls/snapshots/candidate-N/`.
- promoted snapshots are set to `chmod a-w` after promotion.
- the active version is a symlink: `tpls/sys/ -> snapshots/active/sys/`, `tpls/cli/ -> snapshots/active/cli/`.
- rollback = `ln -sfn candidate-M tpls/snapshots/active` (one command, atomic).

### regs (instantiated)

- each project registry is scaffolded from the active tpls/sys/ and tpls/cli/ templates via `bootstrap.py`.
- registries are independent of each other. project A's registry cannot reference project B's.
- test registries in `regs/test-regs/` are the targets for the self-evolution loop.
- real project registries in `regs/<proj>-regs/` are used by humans to build software.

### artifacts (external)

- the actual source code produced by agents. lives in separate repos outside the omni monorepo.
- connected to its registry via `.harness.json` in the project repo root:
  ```json
  {
    "registry_path": "/path/to/omni/regs/<proj>-regs",
    "project_path": "/path/to/repos/<proj>",
    "version": "1.0.0"
  }
  ```

---

## 4. the state file: orchestrator/manifest.json

this is the single file the orchestrator reads after every context clear. it contains everything needed to resume the evolution loop.

```json
{
  "active": "candidate-3",
  "phase": "decide",
  "tier": "seed",
  "test_domain": "cli-todo",
  "candidates": [
    {
      "id": "candidate-0",
      "parent": null,
      "status": "superseded",
      "mutation": null,
      "sha256": "abc123...",
      "pass_rate": {
        "p1": "2/3", "o1": "2/3", "overall": "4/6"
      },
      "created": "2026-03-29T10:00:00Z"
    },
    {
      "id": "candidate-3",
      "parent": "candidate-2",
      "status": "active",
      "mutation": "added spec ordering enforcement to cli/hooks/spec_cascade_gate.py",
      "sha256": "ghi789...",
      "pass_rate": {
        "p1": "3/3", "o1": "3/3", "overall": "6/6"
      },
      "created": "2026-03-29T14:00:00Z"
    }
  ],
  "promoted": ["candidate-0", "candidate-2", "candidate-3"],
  "next_action": "tier at 100% - expand to tier-2 questions"
}
```

### fields

| field | purpose |
|-------|---------|
| `active` | which candidate is currently promoted (symlink target) |
| `phase` | current loop phase: prepare, mutate, execute, verify, decide |
| `tier` | which question tier is active: seed, tier-2, tier-3 |
| `test_domain` | which test project domain is being evaluated |
| `candidates[]` | full lineage of every candidate ever produced |
| `candidates[].sha256` | content hash for deduplication and integrity |
| `candidates[].pass_rate` | yes/no scores per category |
| `candidates[].mutation` | natural language description of what changed |
| `promoted[]` | ordered list of candidates that were accepted |
| `next_action` | what the orchestrator should do next (human-readable) |

after any context clear, the orchestrator reads this file and knows exactly where it is, what happened, and what to do next. a user can also read this file at any time to understand the system's state.

---

## 5. self-evolution loop

### overview

the loop mutates templates, runs test projects against them, measures pass rates, and keeps improvements. it follows the karpathy autoresearch pattern: start with a minimal seed of questions, converge to 100%, then unlock more questions.

### phases

**phase 1: prepare**
- orchestrator reads manifest.json
- identifies the lowest-scoring category from pass_rate
- writes a mutation directive (natural language: "improve X because Y")
- copies active snapshot to `tpls/snapshots/workspace/`
- updates manifest: `phase = "mutate"`

**phase 2: mutate (pool e)**
- pool e receives: workspace/ (writable copy) + mutation directive
- pool e cannot see: eval/, pass rates, scores, other pools
- pool e modifies sys/ and/or cli/ in workspace/
- on completion:
  - workspace/ captured as `snapshots/candidate-N/`
  - sha-256 computed. if it matches an existing snapshot, the candidate is discarded (no-op dedup)
  - candidate-N/ set to `chmod a-w`
  - workspace/ destroyed
  - manifest updated: `phase = "execute"`

**phase 3: execute (pool e, fresh instance)**
- pool e receives: candidate-N's sys/ and cli/ templates + a test project spec from regs/test-regs/
- pool e cannot see: eval/, scores, mutation history
- pool e develops the test project using the mas system (spec cascade, role enforcement, all hooks active)
- produces: code, specs, tests in the test registry
- manifest updated: `phase = "verify"`

**phase 4: verify (pool t + pool v)**
- pool t receives: eval/criteria/ + eval/tiers/seed.yaml (which questions are active)
- pool t cannot see: test project output, code, mutation details
- pool t writes: eval/scripts/check_*.sh (frozen after write)
- pool v receives: eval/scripts/ (pre-written) + test project artifacts
- pool v cannot see: eval/criteria/ wording, mutation details, pool e reasoning
- pool v runs scripts, produces evidence report per question:
  ```yaml
  question: p1.2
  answer: no
  evidence:
    - type: file_timestamp
      path: regs/test-regs/cli-todo-regs/ssot/runtime/openspec/changes/feat-001-add-task/test_spec.md
      created: 2026-03-29T14:02:00
    - type: reasoning
      text: "test_spec created before behavior_spec - cascade violated"
  ```
- manifest updated: `phase = "decide"`, candidate-N.pass_rate = computed matrix

**phase 5: decide**
- orchestrator reads manifest.json
- compares candidate-N.pass_rate vs active candidate's pass_rate
- if improved:
  - `ln -sfn candidate-N tpls/snapshots/active`
  - candidate-N.status = "active", old active.status = "superseded"
  - added to promoted list
- if regressed:
  - candidate-N.status = "rejected"
  - active symlink unchanged
- if current tier at 100% pass rate:
  - next_action = "expand to tier-N+1 questions"
  - unlock more questions from eval/tiers/
- manifest updated: `phase = "prepare"`, loop continues

### tier progression

| tier | questions | unlock condition |
|------|-----------|------------------|
| seed | ~10 foundational (p1.1, p1.3, p1.6, p2.1, p2.3, o1.1, o1.2, o4.1, p4.1) | always active |
| tier-2 | ~20 additional | seed at 100% for 3 consecutive runs |
| tier-3 | all 48 | tier-2 at 90%+ for 3 consecutive runs |

### test project domains

each domain exercises different harness capabilities:

| domain | what it stresses |
|--------|------------------|
| cli-tools | spec cascade basics, simple i/o testing |
| frontend | component decomposition, visual spec fidelity |
| backend-api | contract-driven specs, integration testing |
| networking | concurrency in specs, edge-case coverage |
| graphics | build pipeline complexity, non-trivial deps |
| os-drivers | low-level spec precision, safety constraints |

new domains are added by dropping a manifest into regs/test-regs/:

```yaml
# regs/test-regs/networking-regs/manifest.yaml
name: networking-tcp-server
domain: networking
complexity: moderate
tier: expanded
features:
  - name: connection-pool
    spec_cascade: full
  - name: graceful-shutdown
    spec_cascade: full
expected_roles:
  - behavior-spec-writer
  - test-spec-writer
  - team-lead
  - worker
  - sdet-unit
  - sdet-integration
```

the pass rate becomes a matrix (domain x category), and the evolution loop targets the lowest-scoring cell.

---

## 6. performance metrics

### 48 yes/no questions across 8 categories

**process metrics (p1-p4)**

p1 - spec cascade compliance:
- p1.1: did every feature have a proposal created before any other spec?
- p1.2: did behavior_spec exist before test_spec was written?
- p1.3: did test_spec exist before any test files were written?
- p1.4: did test files exist before implementation code was written?
- p1.5: are all spec documents non-trivial (>50 lines or substantive content)?
- p1.6: did every feature complete the full cascade (no skipped stages)?

p2 - role boundary adherence:
- p2.1: did the orchestrator produce zero direct file writes to the project?
- p2.2: did each spec-writer only write to their designated spec file?
- p2.3: did workers only modify files listed in their tasks.md file scope?
- p2.4: did sdets only write to test paths?
- p2.5: were there zero hook violations (blocked writes) during the sprint?
- p2.6: did no agent write outside the project registry boundary?

p3 - orchestration quality:
- p3.1: was every agent dispatched with an explicit task description?
- p3.2: were independent tasks dispatched in parallel?
- p3.3: were there zero redundant dispatches (same work assigned twice)?
- p3.4: did the orchestrator detect and resolve blockers without human intervention?
- p3.5: was the total agent count within the expected range for the project scope?
- p3.6: did no agent idle (dispatched but produce no output)?

p4 - ssot integrity:
- p4.1: was active_sprint.md updated at each phase transition?
- p4.2: does status.md for each feature reflect its actual final state?
- p4.3: is the openspec index consistent with completed/archived features?
- p4.4: were implementation records created for all completed features?
- p4.5: does context_map.json accurately reflect the final project structure?
- p4.6: was milestones.md updated upon sprint completion?

**output metrics (o1-o4)**

o1 - functional correctness:
- o1.1: does the application build without errors?
- o1.2: do all unit tests pass?
- o1.3: do all integration tests pass?
- o1.4: does the app start and run without runtime errors?
- o1.5: does each behavior in the spec have a corresponding working feature?
- o1.6: do api contracts match what the spec defined?

o2 - test quality:
- o2.1: does line coverage exceed 70%?
- o2.2: do tests cover both happy-path and error cases for each feature?
- o2.3: are there zero trivially passing tests (e.g., assert true)?
- o2.4: do tests fail when the corresponding implementation is removed? (mutation check)
- o2.5: do test names clearly describe the behavior being tested?
- o2.6: are there no test files with zero assertions?

o3 - code quality:
- o3.1: does the code pass linting with zero errors?
- o3.2: are there zero unused imports or dead variables?
- o3.3: does the project follow its own stated conventions (naming, structure)?
- o3.4: is there no duplicated logic beyond a trivial threshold?
- o3.5: are dependencies properly declared (no implicit/missing deps)?
- o3.6: does the project have a working entry point?

o4 - spec-to-implementation fidelity:
- o4.1: does every behavior in behavior_spec have at least one test?
- o4.2: does every test in test_spec have a corresponding test file?
- o4.3: are there zero implemented features that lack a spec?
- o4.4: do function/class names align with terminology used in the spec?
- o4.5: does the file structure match what was laid out in tasks.md?
- o4.6: are there zero todo/fixme markers left in delivered code?

### measurement

each question is binary: yes (1) or no (0). pass rate = passed / total.

automated questions (unforgeable — command output, not agent judgment):
- o1.1 (build), o1.2 (unit tests), o1.3 (integration tests), o3.1 (lint), o2.1 (coverage)

timestamp questions (verifiable from git log):
- p1.1-p1.4 (cascade order), p4.1 (ssot updates)

judgment questions (pool v assesses, must cite evidence):
- p1.5 (non-trivial specs), o2.2 (error case coverage), o4.4 (naming alignment)

---

## 7. pool architecture

### five pools

| pool | purpose | reads | writes | blind to |
|------|---------|-------|--------|----------|
| e (execute) | mutates templates, develops test projects | tpls/snapshots/workspace/ | tpls/snapshots/workspace/ | eval/ entirely, scores, other pools |
| t (test author) | writes check scripts from criteria | eval/criteria/, eval/tiers/ | eval/scripts/ | tpls/, regs/, pool e output, scores |
| v (verify) | runs check scripts, produces evidence | eval/scripts/, test project artifacts | evidence reports (structured yaml) | eval/criteria/ wording, tpls/, mutation details |
| r (read) | returns structured json to orchestrator | regs/ structure (read-only) | nothing | eval/, tpls/, pool internals |
| orchestrator | coordinates, decides | manifest.json, pool r json | manifest.json | raw code, raw artifacts, eval/ internals |

### isolation enforcement (3 independent layers)

1. **os-level**: `chmod a-w` on eval/ and promoted snapshots. the kernel blocks writes regardless of agent behavior.
2. **git-level**: `FROZEN.lock` + pre-commit hook + ci gate. rejects commits that alter eval/ unless on a human-gated branch.
3. **hook-level**: `layer_fence.py` reads pool assignment, blocks file i/o that crosses layer boundaries. extends existing `path_validator.py`.

each pool operates in a sparse-checkout worktree that physically excludes files outside its scope. pool e's worktree does not contain eval/. pool t's worktree does not contain tpls/ or regs/.

---

## 8. anti-gaming gates

all gates are stateless — they work by checking files, not by remembering previous checks.

| gate | what it checks | mechanism |
|------|----------------|-----------|
| information asymmetry | pool e never saw eval/ | sparse-checkout config excludes eval/ from pool e worktree |
| eval immutability | eval/ was not modified | `sha256sum eval/**` matches FROZEN.lock (one command) |
| temporal ordering | pool t scripts predate pool v execution | git timestamps on eval/scripts/ predate pool v evidence report |
| evidence-based reporting | pool v cites specific files/lines | evidence_validator.py parses yaml, rejects entries without file paths |
| spot-check audit | random answers independently verified | orchestrator picks 3 from evidence report, dispatches pool r to verify cited files exist |
| cross-run consistency | question flips match artifact changes | compare pass_rate in manifest.json across candidates, flag flips where no relevant files changed |
| no-op deduplication | identical mutations are caught | sha-256 of candidate content matches existing snapshot = discard |

### spot-check protocol

after pool v delivers its report, the orchestrator randomly samples 3 answers and dispatches pool r to independently verify them:
- if any sampled answer is wrong, the entire report is marked untrusted
- pool v is re-dispatched with a fresh instance
- the discrepancy is logged in manifest.json

---

## 9. project use mode

### bootstrap

```bash
python tpls/cli/setup/bootstrap.py <project-name> --type proj
```

creates:
- `regs/<project-name>-regs/cli/` — copied from active tpls/cli/
- `regs/<project-name>-regs/ssot/` — copied from active tpls/sys/tpl-proj/
- `.harness.json` in the target project repo linking back to the registry

### blueprint discovery (collaborative)

the user talks to the orchestrator about what they want to build. the orchestrator asks clarifying questions one at a time, explores approaches, and dispatches spec-writing subagents to capture decisions.

subagents involved in blueprint discovery:
- **sonders**: explores possibilities, asks "what if" questions, writes to `blueprint/design/`
- **negator**: challenges assumptions, finds gaps, writes to `blueprint/design/`
- **behavior-spec-writer**: captures architectural decisions in `blueprint/design/architecture_overview.md`, `api_mapping.md`
- **test-spec-writer**: writes `blueprint/engineering/testing_strategy.md` based on architecture
- **team-lead**: writes `blueprint/planning/roadmap.md` with milestones

the orchestrator mediates between the user and subagents. the user makes decisions; subagents capture them in the registry. the user never edits files directly.

### sprint execution

once the blueprint is complete, the orchestrator begins sprints (one feature per sprint):

1. **create feature folder**: `ssot/runtime/openspec/changes/feat-<NNN>-<feature-name>/` with proposal, behavior_spec, test_spec, tasks, status files
2. **spec cascade**: orchestrator dispatches subagents in strict order:
   - behavior-spec-writer writes behavior_spec.md
   - test-spec-writer writes test_spec.md (only after behavior_spec exists)
   - team-lead writes tasks.md with file scopes per worker
   - workers implement (only after all specs + tests exist)
   - sdets write tests
   - auditor reviews (read-only)
3. **merge**: orchestrator opens pr, squash merges all feature branches
4. **archive**: move feature folder to `ssot/runtime/openspec/archive/feat-<NNN>-<feature-name>/`
5. **update ssot**: milestones.md, active_sprint.md, index.md

### resumability

the user can interrupt at any point and resume later. the orchestrator reads:
- `ssot/00-project-memory.md` — finds ssot routing
- `ssot/runtime/active_sprint.md` — current sprint state
- `ssot/runtime/openspec/changes/feat-<NNN>-<name>/status.md` — per-feature progress

no conversation history needed. the registry is the memory.

---

## 10. enforcement rules

### rule 1: blueprint freeze during sprints

**when**: `runtime/active_sprint.md` shows an active sprint
**enforcement**: `blueprint_freeze.py` hook (PreToolUse on write tools)
**behavior**: blocks ALL writes to `blueprint/**`. only `runtime/**` is writable during sprints.
**unlock**: blueprint modifications allowed only when active_sprint.md shows no active sprint (between milestones).

### rule 2: destructive git operations require user approval

**enforcement**: `destructive_git_gate.py` hook (PreToolUse on Bash tool)
**blocked commands**:
- `git rm`
- `git reset --hard`
- `git push --force`
- `git branch -D`
- `git clean -f`
- `git checkout -- .`

**behavior**: returns `{"decision": "block", "reason": "destructive git operation requires user approval"}`. all other git operations (commit, push, branch, merge, rebase) pass through.

### rule 3: feature folder naming convention

**format**: `feat-<NNN>-<feature-name>` where NNN is a zero-padded sequence number.
**enforcement**: dual mechanism:
1. `/opsx new-feature` command auto-generates the folder with correct naming and auto-incrementing sequence number
2. hook validates any new folder under `runtime/openspec/changes/` matches the pattern `feat-\d{3}-.+`

**examples**:
- `feat-001-add-task` — valid
- `feat-002-list-tasks` — valid
- `add-task` — blocked

### rule 4: spec cascade ordering

**enforcement**: `spec_cascade_gate.py` hook (PreToolUse on write tools)
**behavior**: blocks writes to implementation files unless the full spec cascade is complete for the feature:
1. `proposal.md` must exist
2. `behavior_spec.md` must exist
3. `test_spec.md` must exist
4. test files must exist
5. only then can implementation code be written

### rule 5: role-scoped file access

**enforcement**: `path_validator.py` hook (PreToolUse on write tools)
**behavior**: each role can only write to specific paths:

| role | allowed write paths |
|------|---------------------|
| orchestrator | nothing (pure delegator) |
| behavior-spec-writer | `<feature>/behavior_spec.md` only |
| test-spec-writer | `<feature>/test_spec.md` only |
| team-lead | `<feature>/tasks.md`, `<feature>/status.md` |
| worker-N | only files listed in tasks.md task N file scope |
| sdet-* | `tests/**/*`, `test/**/*` only |
| auditor | nothing (read-only) |
| sonders, negator | `blueprint/design/*` only |

### rule 6: no ai/assistant references in commits

**enforcement**: pre-commit hook
**behavior**: scans commit messages for terms like "ai", "assistant", "generated", "claude", "llm". blocks the commit if found.

---

## 11. the two loops

```
self-evolution loop (automated)          project use loop (human-driven)
────────────────────────────             ──────────────────────────────
improves tpls/sys/ and tpls/cli/         uses tpls/ to scaffold registries
runs against regs/test-regs/             runs against regs/<proj>-regs/
measures with 48 yes/no pass rate        delivers working software
automated, no human in the loop          user drives the orchestrator
modifies the SYSTEM                      uses the system AS-IS
orchestrator = manifest.json             orchestrator = active_sprint.md
pools: e, t, v, r                        roles: spec-writers, workers, sdets, etc.
```

the self-evolution loop makes templates better. better templates produce better role definitions, better hooks, and better spec cascade enforcement — which means real projects run more smoothly.

the two loops share no state. the evolution loop reads/writes `orchestrator/manifest.json`. the project loop reads/writes `regs/<proj>-regs/ssot/runtime/`. they can run concurrently without interference.

---

## 12. stateless orchestrator protocol

the orchestrator clears its context when usage exceeds 40%. the protocol for both loops:

### evolution loop

```
1. read orchestrator/manifest.json
2. determine phase (prepare / mutate / execute / verify / decide)
3. dispatch the appropriate pool for that phase
4. receive pool result (structured json)
5. update manifest.json with result
6. (context may clear here)
7. next invocation reads manifest.json, picks up at next phase
```

### project loop

```
1. read regs/<proj>-regs/ssot/00-project-memory.md (finds ssot routing)
2. read runtime/active_sprint.md (current sprint state)
3. read runtime/openspec/changes/feat-<NNN>-<name>/status.md (feature progress)
4. determine what to do next (dispatch next subagent, merge, archive)
5. dispatch subagent, update status.md
6. (context may clear here)
7. next invocation reads the same files, picks up where it left off
```

a user can resume any project at any time. the registry files are the complete state. no conversation history is needed.
