# evolution loop system — design spec

## 1. overview

this spec covers the four subsystems deferred from the omni restructure: the evolution loop orchestration, test project scaffolding, eval gates, and the /opsx command. together they complete the self-evolution capability described in the omni system design spec.

the evolution loop is not a long-running daemon. it is a set of python utilities that the orchestrator agent (claude code) calls to manage state transitions. the actual "dispatch" of pool agents happens through claude code's Agent tool. the python code handles: manifest state machine, worktree creation/cleanup for pool isolation, anti-gaming validation, and evidence parsing.

**parent spec:** `docs/superpowers/specs/2026-03-29-omni-system-design.md`

---

## 2. subsystem A: evolution loop (orchestrator/)

### 2.1 loop.py — phase state machine

a library the orchestrator agent imports (or calls as a script) to manage the 5-phase cycle.

**functions:**

```
get_current_phase(manifest_path) -> str
    # returns: prepare, mutate, execute, verify, decide

advance_phase(manifest_path, result: dict) -> str
    # validates current phase allows transition
    # writes result data into manifest (mutation desc, pass_rate, etc.)
    # returns new phase name

prepare_mutation(manifest_path) -> dict
    # reads pass_rate from active candidate
    # identifies lowest-scoring category (or random if tied)
    # returns {"directive": str, "target_category": str, "workspace_ready": bool}

decide_outcome(manifest_path, candidate_id: str) -> str
    # compares candidate pass_rate vs active pass_rate
    # returns: "promote", "reject", or "tie"
    # if promote: calls snapshot_manager.promote_candidate()
    # if reject: marks candidate as rejected in manifest

check_tier_progression(manifest_path) -> dict
    # checks if current tier is at 100% for 3 consecutive runs
    # returns {"should_advance": bool, "current_tier": str, "next_tier": str | None}
    # updates manifest tier field if advancing
```

**state machine:**

```
prepare -> mutate -> execute -> verify -> decide -> prepare (loop)
```

each phase transition is validated — calling `advance_phase("verify", ...)` when the current phase is "prepare" raises an error.

**mutation directive generation:**

the `prepare_mutation()` function analyzes pass_rate to pick the weakest area. the directive is a natural-language string like: "improve spec cascade enforcement in cli/hooks/spec_cascade_gate.py — p1 category is weakest at 1/3". the orchestrator agent passes this directive to pool-e.

### 2.2 dispatch.py — pool worktree management

creates sparse-checkout git worktrees that physically restrict each pool's file visibility.

**functions:**

```
create_pool_worktree(pool: str, base_branch: str = "main") -> dict
    # creates worktree at .worktrees/<pool>-<uuid>/
    # applies sparse-checkout config per pool
    # returns {"worktree_path": str, "branch": str}

cleanup_pool_worktree(worktree_path: str) -> None
    # removes worktree directory and git worktree entry

get_sparse_checkout_config(pool: str) -> list[str]
    # returns list of paths to include for each pool
```

**sparse-checkout configs:**

| pool | included paths | excluded |
|------|---------------|----------|
| pool-e (mutate) | tpls/snapshots/workspace/** | eval/, orchestrator/, regs/ |
| pool-e (execute) | tpls/sys/**, tpls/cli/**, regs/test-regs/** | eval/, orchestrator/ |
| pool-t | eval/criteria/**, eval/tiers/**, eval/scripts/** | tpls/, regs/, orchestrator/ |
| pool-v | eval/scripts/**, regs/test-regs/** | eval/criteria/, tpls/, orchestrator/ |
| pool-r | regs/** | eval/, tpls/, orchestrator/ |

worktrees are created in `.worktrees/` (gitignored). each worktree gets a unique name to allow concurrent pools.

**workspace management:**

`prepare_workspace(manifest_path, snapshots_dir) -> Path`
- copies active snapshot's sys/ and cli/ to tpls/snapshots/workspace/
- returns workspace path
- workspace is destroyed by snapshot_manager.create_candidate() after mutation

### 2.3 anti_gaming.py — integrity validation

stateless checks the orchestrator runs between phases.

**functions:**

```
validate_eval_integrity(eval_dir: Path, frozen_lock_path: Path) -> dict
    # verifies eval/ matches FROZEN.lock
    # returns {"valid": bool, "violations": list[str]}

validate_temporal_order(scripts_dir: Path, evidence_dir: Path) -> dict
    # checks pool-t scripts have earlier timestamps than pool-v evidence
    # returns {"valid": bool, "violations": list[str]}

validate_evidence_report(report_path: Path) -> dict
    # parses pool-v YAML, checks every answer has file_path evidence
    # returns {"valid": bool, "violations": list[str], "answers": list[dict]}

spot_check(evidence: list[dict], sample_size: int = 3) -> list[dict]
    # randomly samples answers from evidence report
    # returns list of {"question": str, "answer": str, "evidence": dict}
    # the orchestrator then dispatches pool-r to verify each sampled item

validate_no_regression(manifest_path: Path, candidate_id: str) -> dict
    # checks that question flips (yes->no or no->yes) correlate with file changes
    # returns {"valid": bool, "suspicious_flips": list[str]}
```

---

## 3. subsystem B: test projects (regs/test-regs/)

### 3.1 seed domain: cli-todo

the first test project is a simple CLI todo app. it exercises the core spec cascade without requiring complex dependencies.

**manifest:** `regs/test-regs/cli-todo-regs/manifest.yaml`

```yaml
name: cli-todo
domain: cli-tools
complexity: minimal
tier: seed
description: >
  a command-line todo list application. supports add, list, complete,
  and delete operations. stores tasks in a local json file.
features:
  - name: add-task
    description: add a new task with a title and optional priority
    spec_cascade: full
  - name: list-tasks
    description: list all tasks, optionally filtered by status
    spec_cascade: full
  - name: complete-task
    description: mark a task as completed by id
    spec_cascade: full
expected_roles:
  - behavior-spec-writer
  - test-spec-writer
  - team-lead
  - worker
  - sdet-unit
tech_stack:
  language: python
  test_framework: pytest
  min_python: "3.10"
```

**bootstrapped structure:** when pool-e runs the test project, it uses bootstrap.py to create the registry structure, then develops through the spec cascade. the resulting structure under `regs/test-regs/cli-todo-regs/` will be:

```
cli-todo-regs/
├── manifest.yaml          # project definition (pre-created)
├── cli/                   # copied from tpls/cli/
└── ssot/                  # copied from tpls/sys/tpl-proj/
    ├── blueprint/         # filled in by pool-e's spec-writers
    └── runtime/
        └── openspec/
            └── changes/
                ├── feat-001-add-task/
                ├── feat-002-list-tasks/
                └── feat-003-complete-task/
```

the project artifacts (actual source code) are produced in a separate directory: `regs/test-regs/cli-todo-regs/artifacts/` — this is where the actual todo app code lives.

### 3.2 test project lifecycle

1. orchestrator reads manifest.yaml to know what features to build
2. pool-e bootstraps the registry from active templates
3. pool-e develops each feature through the spec cascade
4. pool-t writes check scripts from eval/criteria + eval/tiers/seed.yaml
5. pool-v runs check scripts against the completed test project
6. orchestrator reads evidence report, updates manifest.json

### 3.3 future domains

after cli-todo converges at seed tier, additional domains are added by dropping new manifest.yaml files. these are NOT part of this implementation — they're added later:

- frontend (react component library)
- backend-api (rest api with database)
- networking (tcp server with connection pooling)

---

## 4. subsystem C: eval gates (eval/gates/)

### 4.1 pool_isolation.py

validates that a pool worktree's sparse-checkout config matches the expected permissions.

**function:**

```
validate_pool_isolation(worktree_path: Path, pool: str) -> dict
    # reads .git/info/sparse-checkout from worktree
    # compares against expected config from dispatch.get_sparse_checkout_config()
    # also checks that excluded files are truly absent (ls verification)
    # returns {"valid": bool, "violations": list[str]}
```

called by the orchestrator before dispatching any pool agent into a worktree.

### 4.2 evidence_validator.py

parses and validates pool-v's evidence reports.

**function:**

```
validate_evidence(report_path: Path) -> dict
    # parses YAML evidence report
    # for each answer:
    #   - must have "question", "answer" (yes/no), "evidence" list
    #   - each evidence item must have "type" and supporting data
    #   - type "file_timestamp" must have "path" pointing to existing file
    #   - type "command_output" must have "command" and "stdout"
    #   - type "reasoning" must have "text" > 20 chars
    # returns {"valid": bool, "errors": list[str], "parsed": list[dict]}
```

### 4.3 spot_check.py

implements the spot-check audit protocol.

**function:**

```
select_spot_checks(evidence: list[dict], sample_size: int = 3) -> list[dict]
    # randomly selects answers to verify
    # prefers answers where evidence is judgment-based (higher gaming risk)
    # returns selected items with their cited evidence

verify_spot_check(check: dict, project_path: Path) -> dict
    # independently verifies a single evidence claim
    # for file_timestamp: checks file exists and timestamp is plausible
    # for command_output: re-runs the command and compares output
    # for reasoning: flags for manual review (cannot auto-verify)
    # returns {"question": str, "verified": bool, "discrepancy": str | None}
```

---

## 5. subsystem D: /opsx command

a claude code skill (slash command) for operational tasks. registered as a superpowers skill.

### 5.1 commands

**`/opsx status`** — show current evolution loop state
- reads manifest.json
- displays: active candidate, current phase, tier, pass rates, next action
- no side effects

**`/opsx new-feature <name>`** — create a feature folder in the active project registry
- auto-increments sequence number (scans existing feat-NNN- folders)
- creates folder with all template files from openspec/template/
- updates openspec/index.md
- example: `/opsx new-feature add-task` creates `feat-001-add-task/`

**`/opsx evolve`** — run one iteration of the evolution loop
- reads manifest.json, determines current phase
- dispatches the appropriate pool for that phase
- advances state machine
- prints summary of what happened

**`/opsx rollback [candidate-id]`** — rollback to a previous candidate
- calls snapshot_manager.rollback_to()
- updates manifest.json
- prints confirmation

**`/opsx tier`** — show tier progression status
- reads manifest.json candidate history
- shows pass rates per tier, consecutive 100% count, unlock status

### 5.2 implementation

the skill is a markdown file at `.claude/skills/opsx.md` (or in the superpowers skill directory). it reads the command arguments and dispatches to the appropriate python utility or takes direct action.

alternatively, it can be a python CLI script at `tpls/cli/opsx.py` that the skill invokes via Bash. this is preferable because:
- python can read manifest.json natively
- auto-increment logic is easier in python
- the script can be tested with pytest

---

## 6. evidence report format

pool-v produces evidence reports as YAML files. the format is standardized:

```yaml
candidate: candidate-1
tier: seed
timestamp: "2026-03-30T12:00:00Z"
project: cli-todo
answers:
  - question: p1.1
    answer: yes
    evidence:
      - type: file_timestamp
        path: regs/test-regs/cli-todo-regs/ssot/runtime/openspec/changes/feat-001-add-task/proposal.md
        detail: "proposal.md created at 2026-03-30T11:00:00Z, before behavior_spec.md at 11:02:00Z"
      - type: reasoning
        text: "proposal exists and predates all other spec files for this feature"
  - question: o1.1
    answer: yes
    evidence:
      - type: command_output
        command: "cd artifacts/ && python -m py_compile todo.py"
        stdout: ""
        exit_code: 0
        detail: "application compiles without errors"
  - question: o1.2
    answer: no
    evidence:
      - type: command_output
        command: "cd artifacts/ && python -m pytest tests/ -v"
        stdout: "2 passed, 1 failed"
        exit_code: 1
        detail: "test_complete_task fails — marks wrong task id"
```

---

## 7. file inventory

### new files

```
orchestrator/
├── loop.py                          # phase state machine
├── dispatch.py                      # pool worktree management
├── anti_gaming.py                   # integrity validation
└── tests/
    ├── test_loop.py
    ├── test_dispatch.py
    └── test_anti_gaming.py

eval/gates/
├── pool_isolation.py                # worktree isolation validator
├── evidence_validator.py            # evidence report parser/validator
├── spot_check.py                    # random audit sampling
└── tests/
    ├── test_pool_isolation.py
    ├── test_evidence_validator.py
    └── test_spot_check.py

regs/test-regs/
└── cli-todo-regs/
    └── manifest.yaml                # seed test project definition

tpls/cli/opsx.py                     # /opsx CLI entry point (symlinked)
tpls/snapshots/candidate-0/cli/opsx.py  # actual file
```

### modified files

```
orchestrator/manifest.json           # updated as loop runs
eval/FROZEN.lock                     # regenerated after adding gate files
```

note: adding files to eval/gates/ requires regenerating FROZEN.lock. the gate files themselves are part of eval/ (frozen layer), so they must be added via a human-gated commit, then FROZEN.lock regenerated.

---

## 8. testing strategy

### unit tests

each module has its own test file. tests use tmp_path fixtures to avoid touching real state.

- **test_loop.py**: state machine transitions, mutation directive generation, tier progression
- **test_dispatch.py**: sparse-checkout config correctness, worktree creation/cleanup (mocked git)
- **test_anti_gaming.py**: evidence validation, temporal ordering, spot-check selection
- **test_pool_isolation.py**: config comparison against expected permissions
- **test_evidence_validator.py**: YAML parsing, rejection of incomplete evidence
- **test_spot_check.py**: sampling logic, verification against real files

### integration test

after all units pass, run one full loop iteration against cli-todo with mocked pool agents to verify end-to-end state transitions.

---

## 9. implementation order

these should be built as 4 separate implementation plans, executed in dependency order:

1. **eval gates** (no dependencies) — pool_isolation, evidence_validator, spot_check
2. **evolution loop** (depends on eval gates + snapshot_manager) — loop, dispatch, anti_gaming
3. **test projects** (depends on evolution loop) — cli-todo manifest + bootstrap verification
4. **/opsx command** (depends on evolution loop) — CLI wrapper + skill registration

plans 1 and 2 can potentially be parallelized since the gate functions have stable interfaces that the loop code can import.
