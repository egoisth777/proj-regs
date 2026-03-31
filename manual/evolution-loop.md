# Evolution Loop

The evolution loop is the self-improvement engine of the omni system. It iteratively mutates templates, tests them against a reference project, evaluates the results, and promotes improvements. The loop operates through 5 phases with strict pool isolation to prevent gaming.

## The 5-Phase Cycle

```
prepare -> mutate -> execute -> verify -> decide
   ^                                        |
   +----------------------------------------+
```

### Phase 1: Prepare

**Purpose**: Analyze current pass rates and generate a mutation directive targeting the weakest area.

**What happens**:
1. Anti-gaming check: verify `eval/` integrity against `FROZEN.lock`.
2. Load the active candidate's pass rates from `eval-loop/manifest.json`.
3. Identify the worst-performing category (lowest pass rate ratio).
4. Generate a directive string, e.g.: "improve spec cascade (p1) -- currently at 4/6. analyze template weaknesses that cause spec cascade failures and strengthen enforcement."
5. Advance phase to `mutate`.

**Output**: A mutation directive and target category.

### Phase 2: Mutate

**Purpose**: Create a mutable workspace for pool-e to modify templates.

**What happens**:
1. Copy the active snapshot's `sys/` and `cli/` directories into `tpls/snapshots/workspace/`.
2. Return the workspace path and directive to the orchestrator.
3. The orchestrator dispatches pool-e to mutate the workspace based on the directive.

**Output**: A workspace directory ready for mutation. Requires manual dispatch of pool-e before proceeding.

### Phase 3: Execute

**Purpose**: Capture the mutated workspace as a new candidate and run the test project.

**What happens**:
1. Capture the workspace as a new candidate using `snapshot_manager.create_candidate()`. This computes a SHA-256 hash and detects duplicates.
2. If the candidate is a duplicate (same hash as an existing candidate), skip with a dedup marker.
3. Otherwise, record the new candidate in the manifest.
4. The orchestrator dispatches pool-e to run a full spec cascade on a test project using the new templates, then dispatches pool-v to verify.

**Output**: A new candidate ID. Requires manual dispatch of pool-e (to develop the test project) and pool-v (to verify) before proceeding.

### Phase 4: Verify

**Purpose**: Run evaluation scripts and anti-gaming checks against the test project.

**What happens**:
1. Anti-gaming check: validate temporal ordering (pool-t scripts must have earlier modification times than pool-v evidence).
2. Run all check scripts from `eval/scripts/` against the test project.
3. Filter results by the active tier's question list.
4. Compute per-category and overall pass rates.
5. Update the candidate's pass rates in the manifest.
6. Advance phase to `decide`.

**Output**: Pass rates and a list of failed questions.

### Phase 5: Decide

**Purpose**: Compare the candidate against the active snapshot and promote or reject.

**What happens**:
1. Anti-gaming check: validate no regression with identical content (if a candidate has the same SHA-256 as its parent but scores lower, it is suspicious).
2. Compare the candidate's overall pass rate against the active snapshot's pass rate.
3. If the candidate scores higher: **promote** it (update the `active` symlink).
4. If the candidate scores lower: **reject** it.
5. If scores are equal: **tie** (no change).
6. Advance phase to `prepare`, restarting the cycle.

**Output**: An outcome (promote, reject, or tie) and the candidate ID.

## Pool Dispatch

The evolution loop uses four isolated pools, each with restricted permissions enforced by sparse-checkout configurations.

### pool-e (Execution Pool)

**Purpose**: Mutate templates and develop test projects.

**Permissions**:
- Mutate phase: read/write `tpls/snapshots/workspace/` only.
- Execute phase: read `tpls/` and `regs/test-regs/`; write `regs/test-regs/`.
- Blind to: `eval/` entirely, pass rates, scores, `eval-loop/manifest.json`.

**Key constraint**: Pool-e does not know what it is being evaluated on. It receives a directive (e.g., "improve spec cascade") and must improve the templates based on that guidance alone.

### pool-t (Test Author Pool)

**Purpose**: Write check scripts that verify yes/no questions against project artifacts.

**Permissions**:
- Read: `eval/criteria/` and `eval/tiers/` only.
- Write: `eval/scripts/` only.
- Blind to: `tpls/`, `regs/`, pool-e output, scores.

**Key constraint**: Pool-t writes scripts from the criteria definitions alone, without seeing the test project or what pool-e produced.

### pool-v (Verification Pool)

**Purpose**: Run check scripts and produce evidence reports.

**Permissions**:
- Read: `eval/scripts/` and `regs/test-regs/`.
- Write: evidence reports (structured YAML) only.
- Blind to: `eval/criteria/` wording, `tpls/`, mutation details.

**Key constraint**: Pool-v executes scripts and records results without interpreting or judging them. It does not know the criteria wording.

### pool-r (Read Pool)

**Purpose**: Return structured JSON summaries to the orchestrator.

**Permissions**:
- Read: `regs/` structure only (directory listings, file metadata, line counts).
- Write: nothing (returns JSON to orchestrator only).
- Blind to: `eval/`, `tpls/`, pool internals.

**Key constraint**: Pool-r never returns raw file contents. It provides structured summaries (directory trees, existence checks, metadata, status, diffs).

## Sparse-Checkout Isolation

Each pool's visibility is enforced through sparse-checkout configurations defined in `eval-loop/dispatch.py`. The configurations specify:

- **include**: Directories the pool can see.
- **exclude**: Directories that must NOT be present in the pool's worktree.

The `eval/gates/pool_isolation.py` gate can independently verify that a worktree contains only what the pool should see.

## Anti-Gaming Validation

Three anti-gaming checks run during the loop, implemented in `eval/gates/anti_gaming.py`:

1. **Eval integrity** (prepare phase): Verify `eval/` files match `FROZEN.lock` hashes. Detects tampering with criteria, scripts, or gates.

2. **Temporal order** (verify phase): Check that pool-t scripts have earlier modification times than pool-v evidence. Detects evidence fabrication that predates script creation.

3. **No regression** (decide phase): If a candidate has the same SHA-256 content hash as its parent but shows score regressions, it is flagged as suspicious and rejected. Detects non-deterministic or fabricated results.

## Tier Progression

The loop tracks consecutive perfect scores. When the active candidate achieves 100% on all active questions for 3 consecutive runs, the system advances to the next tier:

```
seed (9 questions) -> tier-2 (27 cumulative) -> tier-3 (48 cumulative)
```

After advancing, the consecutive counter resets and the loop continues with the expanded question set. See [Evaluation Framework](eval-framework.md) for tier details.

## Manifest State

All evolution loop state is stored in `eval-loop/manifest.json`:

```json
{
  "active": "candidate-0",
  "phase": "prepare",
  "tier": "tier-3",
  "test_domain": "cli-todo",
  "consecutive_passes": 3,
  "candidates": [
    {
      "id": "candidate-0",
      "parent": null,
      "status": "active",
      "mutation": null,
      "sha256": null,
      "pass_rate": {
        "p1": "6/6",
        "o1": "6/6",
        "overall": "48/48"
      }
    }
  ],
  "promoted": ["candidate-0"],
  "next_action": "consecutive 100%: 3/3 for tier advance"
}
```

Key fields:
- **active**: The currently promoted candidate ID.
- **phase**: Current phase in the 5-phase cycle.
- **tier**: Current evaluation tier (seed, tier-2, tier-3).
- **consecutive_passes**: Number of consecutive perfect-score runs.
- **candidates**: Array of all candidates with their pass rates.
- **promoted**: History of promoted candidate IDs.

> **Note**: The manifest may also contain additional internal state fields not shown in the example above, such as `_last_directive`, `_last_candidate`, and `_last_evidence`. These are used by the loop engine to carry context between phases and should be treated as opaque internal state.
