# Evolution Loop Wiring — Test Spec

## Verification Strategy
Since the phase functions wire together already-tested building blocks, the
primary verification is:

1. Existing unit tests in orchestrator/tests/ must continue to pass
2. Dry-run of `--phase prepare` must produce valid JSON output
3. The opsx.py phase subcommand must delegate correctly

## Test Cases
- test_existing_suite: run full pytest orchestrator/tests/ — all pass
- test_phase_prepare_dry: run --phase prepare, verify JSON output
- test_backward_compat: run --rounds still works as before
