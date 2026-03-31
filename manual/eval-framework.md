# Evaluation Framework

The `eval/` directory contains the evaluation framework that scores the system's output. It defines 48 yes/no questions across 8 categories, organizes them into 3 tiers of increasing difficulty, and provides the scripts, gates, and pool definitions that make the evaluation trustworthy.

## Directory Structure

```
eval/
  criteria/        -- YAML files defining the 48 questions
  tiers/           -- YAML files defining which questions belong to each tier
  scripts/         -- Python check scripts (one per question)
  gates/           -- Integrity validators (frozen_lock, evidence_validator, pool_isolation, spot_check)
  pools/           -- Pool role definitions (pool-e, pool-t, pool-v, pool-r)
  FROZEN.lock      -- SHA-256 hashes of all eval/ files for tamper detection
```

## Criteria

Eight YAML files in `eval/criteria/` define the evaluation questions. Each question has an ID, text, type, and tier assignment.

### Process Categories (p1-p4)

These measure whether the system followed its own rules:

| Category | Description | Example Question |
|---|---|---|
| **p1** -- spec cascade | Did the spec cascade execute in the correct order? | "Did every feature have a proposal created before any other spec?" |
| **p2** -- role boundary | Did agents stay within their designated write scopes? | "Did the orchestrator produce zero direct file writes to the project?" |
| **p3** -- orchestration | Did the orchestrator coordinate agents effectively? | "Were independent tasks dispatched in parallel?" |
| **p4** -- SSoT integrity | Did the SSoT registry stay consistent and up-to-date? | "Was active_sprint.md updated at each phase transition?" |

### Output Categories (o1-o4)

These measure the quality of the produced software:

| Category | Description | Example Question |
|---|---|---|
| **o1** -- correctness | Does the produced software work correctly? | "Does the application build without errors?" |
| **o2** -- test quality | Are the produced tests meaningful and comprehensive? | "Does line coverage exceed 70%?" |
| **o3** -- code quality | Is the produced code clean and well-structured? | "Does the code pass linting with zero errors?" |
| **o4** -- spec fidelity | Does the implementation match what the specs described? | "Does every behavior in behavior_spec have at least one test?" |

Each category contains 6 questions, for 48 total.

### Question Types

- **timestamp** -- Verified by checking file creation/modification timestamps or git commit history.
- **automated** -- Verified by running tools (compilers, linters, test runners).
- **judgment** -- Verified by reasoning about project artifacts (higher gaming risk, weighted 3x in spot-check audits).

## Tier Progression

Questions are unlocked progressively across three tiers. The system must demonstrate consistent performance at one tier before advancing.

### seed (9 questions)

Foundational questions that are always active. Covers the basics:
- p1.1, p1.3, p1.6 (spec cascade ordering)
- p2.1, p2.3 (role boundaries)
- o1.1, o1.2 (builds and unit tests pass)
- o4.1 (spec fidelity)
- p4.1 (SSoT updates)

### tier-2 (18 questions)

Unlocked when seed is at 100% for 3 consecutive evaluation runs. Adds:
- More spec cascade checks (p1.2, p1.4)
- More role boundary checks (p2.2, p2.4, p2.5)
- Orchestration quality (p3.1, p3.2, p3.3)
- SSoT consistency (p4.2, p4.3)
- Integration tests and runtime correctness (o1.3, o1.4)
- Test coverage and quality (o2.1, o2.2)
- Linting and dead code (o3.1, o3.2)
- Spec fidelity depth (o4.2, o4.3)

### tier-3 (21 questions)

Unlocked when tier-2 is at 100% for 3 consecutive runs. The full question set:
- Substantive spec content (p1.5)
- Cross-boundary violations (p2.6)
- Advanced orchestration (p3.4, p3.5, p3.6)
- Implementation records and context map accuracy (p4.4, p4.5, p4.6)
- Behavioral completeness (o1.5, o1.6)
- Test mutation resilience and naming (o2.3, o2.4, o2.5, o2.6)
- Conventions, duplication, dependencies, entry points (o3.3, o3.4, o3.5, o3.6)
- Naming alignment and clean delivery (o4.4, o4.5, o4.6)

### Tier Advancement

The evolution loop tracks `consecutive_passes` in `eval-loop/manifest.json`. When the active candidate achieves 100% on all active questions for 3 consecutive runs, the tier advances and the counter resets.

## Check Scripts

Each question has a corresponding Python script in `eval/scripts/` (e.g., `check_p1_1.py` for question p1.1). These scripts:

1. Accept a project path as a command-line argument.
2. Inspect the project's artifacts (files, timestamps, git history, build output).
3. Output structured YAML with the question ID, a yes/no answer, and evidence.

Example output format:

```yaml
question: p1.1
answer: yes
evidence:
  - type: file_timestamp
    path: regs/test-regs/cli-todo-regs/ssot/runtime/openspec/changes/feat-001-add-task/proposal.md
    detail: "Feature 'feat-001-add-task': proposal.md (git_commit=1711612800) <= behavior_spec.md (git_commit=1711612900) -- OK"
```

The runner (`eval-loop/run_loop.py`) executes all check scripts, filters results by the active tier's question list, and computes per-category and overall pass rates.

## Gates

Gates in `eval/gates/` provide integrity validation:

### frozen_lock.py

Generates and verifies `FROZEN.lock`, which contains SHA-256 hashes of every file in `eval/` (excluding `FROZEN.lock` itself and build artifacts). This detects tampering with criteria, scripts, or gates.

- **generate**: Compute hashes for all files and write `FROZEN.lock`.
- **verify**: Compare current file hashes against the lock. Reports MISSING, CHANGED, or NEW files.

Usage:
```bash
python eval/gates/frozen_lock.py           # Generate FROZEN.lock
python eval/gates/frozen_lock.py verify    # Verify integrity
```

### evidence_validator.py

Parses and validates YAML evidence reports produced by pool-v. Checks that each answer has:
- A question ID
- A yes/no answer
- A non-empty evidence list with valid evidence items (file_timestamp, command_output, or reasoning with >= 20 characters)

### pool_isolation.py

Validates that a pool worktree's sparse-checkout matches expected permissions. Each pool has defined include and exclude paths. The gate checks that excluded directories are NOT present in the worktree.

### spot_check.py

Randomly samples evidence answers for independent verification. Judgment-based evidence (reasoning type) is weighted 3x for selection since it is harder to verify automatically. Can also independently verify that cited file paths actually exist.

## FROZEN.lock

The `FROZEN.lock` file at `eval/FROZEN.lock` is a JSON file containing SHA-256 hashes for every file in the `eval/` directory. It is checked at the start of each evolution loop iteration (the prepare phase) by `eval/gates/anti_gaming.py`.

If any file has been added, removed, or modified without updating the lock, the evolution loop halts with an integrity violation. This prevents the system (or any pool agent) from gaming the evaluation by modifying criteria or scripts.

## Pools

Pool definitions in `eval/pools/` describe the four isolation pools used in the evolution loop. Each pool has restricted read/write permissions and is blind to certain parts of the system. See [Evolution Loop](evolution-loop.md) for how pools are dispatched.
