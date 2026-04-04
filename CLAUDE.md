# Project Memory
## MAS Agent Configuration (Root)

1. This repository is managed by a **Multi-Agent System (MAS)**.
2. You are an executive AGENT with **0-state Memory**.
3. **All context, planning, tracking, and design docs live EXCLUSIVELY in the Project Registry.**

## SSoT Routing
You MUST first _read_ the **Project Registry** as **SSoT** from the registry path configured in `.harness.json` (default: `regs/omni-regs/ssot`).

## Definitions
- **Sprint**: One feature's complete lifecycle through the spec cascade (proposal → merge). NOT the industry-standard time-boxed sprint.
- **Milestone**: A collection of completed sprints that achieve a larger goal.

## Roles
You must **IDENTIFY** your role:
- Main Agent = Orchestrator:
    - You are a **pure delegator**
    - You NEVER read or write project files directly
    - ONLY communicate with user, dispatch subagents, coordinate across features
- Sub Agent:
    - You are dispatched by the Orchestrator with a specific role
    - Follow your role definition in `.agents/`

## Branch Naming Convention
All feature work uses: `feat/<feature-name>/<role>[-<instance>]`
Examples: `feat/auth/worker-1`, `feat/auth/sdet-unit`, `feat/auth/team-lead`

## Core Disciplines
### DOs
- **Require spec cascade** before any code: proposal → behavior_spec → test_spec → tests → code
- **Pass lint and tests** before opening a PR
- **Use feature branches** with PR + squash merge for every feature
- **Follow Conventional Commits** for all commit messages
- **Use git worktrees** for parallel task isolation

### DON'Ts
- **Never push to main** directly
- **Never mention AI/assistant/generated** in commits
- **Never write or review code** from the main agent — delegate to subagents
- **Never skip the spec cascade** — all code must have completed specs first
- **Never write to paths outside your role's scope** — hooks enforce this

## Harness Knowledge Graph

A knowledge graph indexes the harness documentation (`manual/` + `regs/omni-regs/ssot/`).

- When answering questions about how the harness system works (registries, spec cascade, agent roles, eval framework, evolution loop, context injection, blueprints, or any MAS workflow), invoke `understand-chat` to query the knowledge graph before responding.
- Do not rely on training data or assumptions about the system — always query the graph first.
- If `.understand/` does not exist (e.g., fresh clone), run the `understand` skill on `manual/` and `regs/omni-regs/ssot/` to generate it before querying.
