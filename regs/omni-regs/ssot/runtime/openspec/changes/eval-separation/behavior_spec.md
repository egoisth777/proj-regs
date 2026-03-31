# Eval Separation — Behavior Spec

## Module Relocation
`anti_gaming.py` moves from `orchestrator/` to `eval/gates/`. All three public
functions retain their exact signatures and behavior:

### validate_eval_integrity(eval_dir: Path) -> dict
- Verifies eval/ matches FROZEN.lock using frozen_lock.verify_lock
- Returns {"valid": bool, "violations": list[str]}

### validate_temporal_order(scripts_dir: Path, evidence_dir: Path) -> dict
- Checks pool-t scripts have earlier mtimes than pool-v evidence
- Returns {"valid": bool, "violations": list[str]}

### validate_no_regression(manifest_path: Path, candidate_id: str) -> dict
- Checks score regressions correlate with meaningful mutations
- Returns {"valid": bool, "suspicious_flips": list[str]}

## Import Changes
- `anti_gaming.py`: Remove sys.path hack; use direct `from frozen_lock import verify_lock`
  since the module is now co-located in eval/gates/
- `orchestrator/run_loop.py`: Add eval/gates/ to sys.path and import from there

## Invariants
- All existing tests pass without logic changes
- No function signatures or return types change
- No new dependencies introduced
