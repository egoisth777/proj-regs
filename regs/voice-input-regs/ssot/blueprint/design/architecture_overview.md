# Architecture Overview

This document provides a high-level overview of the MAS Harness system architecture.

## 1. System Context

The MAS Harness is a meta-system — a framework that orchestrates multi-agent development across projects. It manages the lifecycle of features from requirements through to merge via project registries that act as both Single Source of Truth (SSoT) and runtime harness.

Users: Software developers using Claude Code for multi-agent development.
External systems: GitHub (PRs, CI/CD), Obsidian (vault browsing), Claude Code (agent execution).

## 2. Core Components

The harness has two layers:

- **Protocol Layer** (current): Markdown conventions, file structures, agent role definitions, and OpenSpec workflows that guide agent behavior by convention.
- **Executable Layer** (planned — M1/M2): Hooks (Claude Code settings.json), Skills (formalized `/opsx` commands), CLI scripts (Python/TypeScript), and JSON inter-flow data passing.

### Component Breakdown

| Component | Layer | Status | Description |
|---|---|---|---|
| Project Registry | Protocol | Built | Obsidian vault per project — blueprint (static) + runtime (dynamic) |
| Agent Role Definitions | Protocol | Built | Markdown files defining each agent's role, triggers, inputs, outputs |
| Context Map | Protocol | Built | JSON config enforcing minimum-context injection per role |
| OpenSpec System | Protocol | Built | Per-feature spec folders with cascade: proposal → behavior → test → tasks |
| `/opsx` Workflows | Protocol | Built | Markdown-defined workflow commands (propose, apply, archive) |
| Hooks | Executable | Planned (M1) | Claude Code hooks for path validation, spec cascade enforcement, post-PR-wait |
| Skills | Executable | Planned (M1) | Formalized `/opsx` commands as executable skills |
| CLI Scripts | Executable | Planned (M2) | Python/TS scripts for deterministic state management, JSON data passing |
| Template Automation | Executable | Planned (M3) | CLI for creating registries from templates and initializing project repos |

## 3. Data Flow

```
User requirements
  → Sonders (design) → Negator (review) → Approved blueprint
  → Behavior Spec Writer → Test Spec Writer → SDET agents (tests)
  → Team Lead (task breakdown) → Workers (code in worktrees)
  → Regression Runner (full test suite) → Auditor (architectural review)
  → PR → post-pr-wait hook → CI/CD → Merge
  → Archive OpenSpec → Update runtime state
```

## 4. Key Architectural Decisions

- **No CLAUDE.md in registry** — prevents context pollution when subagents access registry files
- **Project ↔ Registry separation** — "how agents behave" (project repo) vs "what agents know" (registry vault)
- **Minimum context principle** — each agent gets only the docs it needs via `context_map.json`
- **Per-feature isolated runtime** — each OpenSpec folder is self-contained; no shared mutable sprint state for workers
