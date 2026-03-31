# Evolution Loop Wiring — Proposal

## Problem
The evolution loop has all building blocks implemented and unit-tested, but
`run_loop.py` only runs evaluation rounds (verify phase). It never calls the
mutation, candidate creation, or promotion functions. The phase state machine
in `loop.py` sits at "prepare" forever.

## Solution
Add a `--phase` CLI mode to `run_loop.py` that runs a SINGLE phase of the
evolution loop and outputs a JSON result. The Claude Code orchestrator calls
this repeatedly, dispatching agents between phases. Also add a `phase`
subcommand to `opsx.py` for convenience.

## Scope
- `orchestrator/run_loop.py` — add phase functions and --phase CLI arg
- `orchestrator/opsx.py` — add phase subcommand
