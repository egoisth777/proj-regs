# Knowledge Graph

The harness documentation is indexed as an Understand-Anything knowledge graph, enabling on-demand retrieval for both users and agents.

## What It Indexes

The graph covers two documentation scopes:

- **`manual/`** — System guides covering architecture, registries, templates, evaluation, evolution, agent roles, and the spec cascade.
- **`regs/omni-regs/ssot/`** — The SSoT registry: blueprint (design, engineering, agent role definitions, hooks, planning) and runtime structure (active sprint, milestones, backlog, OpenSpec).

## Where It Lives

The graph is stored in `.understand-anything/` at the repo root. This directory is gitignored — it is a generated artifact, not source content. Each machine maintains its own local copy.

## How to Generate or Regenerate

Run the `understand` skill targeting both documentation scopes:

```
understand --path manual/ --path regs/omni-regs/ssot/
```

This overwrites the existing graph in `.understand/`.

## Automatic Regeneration

A post-commit git hook (`.githooks/post-commit`) automatically regenerates the graph when a commit touches files in `manual/` or `regs/omni-regs/ssot/`. The regeneration runs synchronously (blocking) — the commit completes only after the graph is updated.

To activate the hook on a fresh clone:

```bash
git config core.hooksPath .githooks
```

## How It Is Used

### Users (Automatic)

`CLAUDE.md` instructs Claude to invoke `understand-chat` automatically when answering questions about the harness system. No manual skill invocation is needed — just ask the question.

If `.understand-anything/` does not exist (e.g., fresh clone), Claude will prompt you to run the `understand` skill first.

### Orchestrator (Mediated Retrieval)

The orchestrator role definition includes a knowledge graph retrieval instruction. Before dispatching a subagent on a task that requires harness context, the orchestrator queries the graph via `understand-chat` and includes the relevant context in the subagent's dispatch prompt.

Subagents do not have direct access to the knowledge graph. The orchestrator is the sole mediator.

## Querying the Graph

Use the `understand-chat` skill to ask questions:

- "How does the spec cascade work?"
- "What documents does the worker role receive?"
- "How does the evaluation tier progression work?"
- "What is the orchestrator's coupling detection responsibility?"

The graph returns answers sourced from the indexed documentation.
