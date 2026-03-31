# Evolution Loop Wiring — Behavior Spec

## Phase Functions
Each phase function accepts manifest_path and relevant directories, performs
its phase logic, advances the phase state machine, and returns a JSON-
serializable dict describing the result.

### run_phase_prepare
- Validates eval integrity via anti_gaming
- Calls prepare_mutation to generate a directive
- Advances phase from prepare to mutate

### run_phase_mutate
- Calls prepare_workspace to create mutable copy
- Returns workspace path and directive for Pool-E

### run_phase_execute
- Calls create_candidate to snapshot workspace
- Handles dedup case (returns dedup: true)
- Advances phase from execute to verify

### run_phase_verify
- Validates temporal order via anti_gaming
- Runs evaluation round
- Updates candidate pass_rate in manifest

### run_phase_decide
- Validates no regression via anti_gaming
- Calls decide_outcome to compare candidate vs active
- Promotes candidate if outcome is "promote"

## CLI Mode
`python run_loop.py --phase <name>` runs one phase, prints JSON, exits.
Existing `--rounds` mode remains unchanged for backward compatibility.

## opsx.py Integration
`python opsx.py phase <name>` delegates to run_loop.py --phase.
