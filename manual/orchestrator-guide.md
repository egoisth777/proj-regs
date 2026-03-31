# Orchestrator Guide

This guide covers the operational commands available through `opsx.py` and the `run_loop.py` runner for managing the evolution loop.

## opsx.py CLI

`opsx.py` is the CLI entry point for evolution loop operations. All commands are run from the project root.

### status

Show the current evolution loop state.

```bash
python orchestrator/opsx.py status [--manifest PATH]
```

Output includes:
- Active candidate ID
- Current phase
- Current tier
- Pass rates for the active candidate
- Number of candidates and promotions
- Next action

Example output:
```
Active: candidate-0
Phase: prepare
Tier: tier-3
Pass rate: {'p1': '6/6', 'o1': '6/6', ..., 'overall': '48/48'}
Candidates: 1
Promoted: 1
Next action: consecutive 100%: 3/3 for tier advance
```

### tier

Show tier progression status.

```bash
python orchestrator/opsx.py tier [--manifest PATH]
```

Output:
```
Current tier: tier-3
Consecutive 100% passes: 3
Need 3 consecutive to advance
```

### new-feature

Create a new feature folder with an auto-incrementing sequence number.

```bash
python orchestrator/opsx.py new-feature NAME --changes-dir PATH --template-dir PATH
```

Arguments:
- `NAME`: Feature name (e.g., `add-task`)
- `--changes-dir`: Path to the `runtime/openspec/changes/` directory
- `--template-dir`: Path to the feature template directory

Creates a folder like `feat-001-add-task/` with files copied from the template directory.

### phase

Run a single phase of the evolution loop.

```bash
python orchestrator/opsx.py phase PHASE_NAME [--project PROJECT]
```

Valid phase names: `prepare`, `mutate`, `execute`, `verify`, `decide`.

The `--project` flag specifies the test project name (default: `cli-todo`). The test project is located at `regs/test-regs/<project>-regs/`.

> **Note:** The `phase` subcommand accepts `--manifest` in its argument parser but does not forward it to `run_loop.py`. The manifest path is always resolved by `run_loop.py` internally.

Each phase outputs JSON describing its result.

### rollback

Revert the active snapshot to a previous candidate.

```bash
python orchestrator/opsx.py rollback CANDIDATE_ID [--manifest PATH] [--snapshots-dir PATH]
```

This updates the `active` symlink in `tpls/snapshots/` to point to the specified candidate and updates the manifest accordingly.

### reset-test

Reset a test project to its post-development baseline state.

```bash
python orchestrator/opsx.py reset-test NAME
```

Arguments:
- `NAME`: Test project name (e.g., `cli-todo`)

This checks out the tagged version of the test project files (using the git tag `test-baseline/<name>`), removes untracked files (evidence reports, caches), and unstages the checkout.

## run_loop.py

The evolution loop runner supports two modes: rounds-based evaluation and single-phase execution.

### Rounds-Based Mode

Run multiple evaluation rounds against the test project:

```bash
python orchestrator/run_loop.py [--rounds N] [--project NAME]
```

Arguments:
- `--rounds N`: Maximum number of evaluation rounds (default: 100).
- `--project NAME`: Test project name (default: `cli-todo`).

In this mode, the runner:
1. Runs all check scripts against the test project for each round.
2. Updates the manifest with pass rates.
3. Tracks consecutive perfect scores for tier advancement.
4. Stops when either tier-3 converges at 100% for 3 consecutive runs, or the round limit is reached, or a tier advances (pausing for pool-t to write new scripts).

Example output:
```
=== Evolution Loop: 100 rounds on cli-todo ===

--- Tier: seed ---
  Round   1: 9/9 | consecutive: 1/3 | tier: seed
  Round   2: 9/9 | consecutive: 2/3 | tier: seed
  Round   3: 9/9 | consecutive: 3/3 | tier: seed

  *** TIER ADVANCED: seed -> tier-2 ***
```

### Single-Phase Mode

Run one phase of the 5-phase cycle:

```bash
python orchestrator/run_loop.py --phase PHASE_NAME [--project NAME]
```

This is the mode used by `opsx.py phase`. Each phase returns a JSON result. Phases that require manual pool dispatch (mutate and execute) include an `action_required` field in their output.

## Typical Workflow

A typical evolution loop iteration looks like this:

1. **Prepare**: `python orchestrator/opsx.py phase prepare`
   - Validates eval integrity, generates mutation directive.

2. **Mutate**: `python orchestrator/opsx.py phase mutate`
   - Creates workspace. Dispatch pool-e to mutate templates.

3. **Execute**: `python orchestrator/opsx.py phase execute`
   - Captures candidate. Dispatch pool-e to develop test project, then pool-v to verify.

4. **Verify**: `python orchestrator/opsx.py phase verify`
   - Runs check scripts, computes pass rates.

5. **Decide**: `python orchestrator/opsx.py phase decide`
   - Compares candidate vs active, promotes or rejects.

Between phases 2-3 and 3-4, manual pool dispatch is required. The orchestrator agent handles this dispatch based on the `action_required` field in the phase output.
