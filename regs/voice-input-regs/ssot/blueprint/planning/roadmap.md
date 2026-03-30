# Roadmap

This document outlines the milestones and sprints for the MAS Harness project.

> **Reminder:** A "sprint" here means one feature's complete lifecycle through the spec cascade (proposal → merge). A "milestone" is a collection of completed sprints that achieve a larger goal.

## Milestone 1: Enforcement Layer
**Goal:** Stop agents from misbehaving. Establish hooks and skills that enforce the specification cascade and prevent ad-hoc changes.

### Sprints (Features)
- [ ] **Hooks: Path validation** — Hook that validates agents write only to allowed paths based on their role
- [ ] **Hooks: Spec cascade gate** — Hook that blocks code implementation until the full spec cascade is complete
- [ ] **Hook: post-pr-wait** — Implement the post-PR-wait hook as an executable Claude Code hook
- [ ] **Skills: /opsx:propose** — Formalize as a real executable skill
- [ ] **Skills: /opsx:apply** — Formalize as a real executable skill
- [ ] **Skills: /opsx:archive** — Formalize as a real executable skill

## Milestone 2: Execution Engine
**Goal:** Deterministic automation. Replace manual agent coordination with scripted flows.

### Sprints (Features)
- [ ] **CLI: State manager** — Python/TS script for reading/writing runtime state (JSON in/out)
- [ ] **CLI: Context injector** — Script that reads `context_map.json` and assembles subagent prompts
- [ ] **CLI: OpenSpec lifecycle** — Script for creating, locking, and archiving OpenSpec folders
- [ ] **JSON inter-flow data passing** — Define and implement all hook/skill data contracts

## Milestone 3: Scaling
**Goal:** Project onboarding. Make it easy to create new registries and initialize projects.

### Sprints (Features)
- [ ] **Template automation** — CLI command to create a new registry from `tpl-proj/`
- [ ] **Project initialization** — CLI command to set up a project repo (create CLAUDE.md, AGENTS.md, symlink .agents/)
- [ ] **Template evolution** — Backport `mas-harness` improvements to `tpl-proj/` template (Approach C)
