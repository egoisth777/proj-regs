# Eval Separation — Test Spec

## Verification Strategy
This is a pure relocation refactor with no logic changes. Verification confirms
all existing tests pass from their new locations.

## Test Cases
1. `eval/gates/tests/test_anti_gaming.py` — all 7 existing tests pass from new location
2. `orchestrator/tests/` — existing orchestrator tests still pass (run_loop imports work)
3. No import errors when running the relocated test file
