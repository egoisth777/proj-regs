# API / Data Contracts

This document defines the JSON data contracts used for inter-flow data passing between harness components.

> **Status:** The executable layer (Python/TypeScript CLI, hooks, skills) is planned for M1/M2. This document will be populated as those components are built. For now, the only structured data contract is `context_map.json`.

## 1. context_map.json

See `context_map.json` at the registry root. Schema documented in the design spec Section 6.

## 2. OpenSpec Status (Planned — M2)

```json
{
  "feature": "<feature-name>",
  "phase": "design | spec-cascade | execution | quality-gate | wrap-up",
  "locked": true,
  "worktree": "<path-to-worktree>",
  "assigned_milestone": "<milestone-id>"
}
```

## 3. Hook Payloads (Planned — M1)

Hook input/output JSON contracts will be defined here as hooks are implemented.
