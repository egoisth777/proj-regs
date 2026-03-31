# Eval Separation — Proposal

## Problem
`orchestrator/anti_gaming.py` contains eval validation logic (validate_eval_integrity,
validate_temporal_order, validate_no_regression) that was incorrectly placed in
`orchestrator/` during the evolution loop implementation. It uses a sys.path hack
to import from `eval/gates/frozen_lock.py`, which indicates it belongs in `eval/gates/`
alongside `frozen_lock.py`, `evidence_validator.py`, and `pool_isolation.py`.

## Solution
Move `anti_gaming.py` and its tests into `eval/gates/` where they belong.
Update all imports in `orchestrator/run_loop.py` to reference the new location.
Remove the sys.path hack from anti_gaming.py since it will be co-located with
its dependency `frozen_lock.py`.

## Scope
- `eval/gates/anti_gaming.py` — moved from `orchestrator/anti_gaming.py`
- `eval/gates/tests/test_anti_gaming.py` — moved from `orchestrator/tests/test_anti_gaming.py`
- `orchestrator/run_loop.py` — update import path
- Delete `orchestrator/anti_gaming.py` and `orchestrator/tests/test_anti_gaming.py`
