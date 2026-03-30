---
description: Milestone checklist with completion criteria
tags:
  - tracking
---

# Milestones

> A milestone is a collection of completed sprints that achieve a larger goal. Blueprint may evolve between milestone completions.

## M1: Enforcement Layer
**Goal:** Stop agents from misbehaving
**Completion criteria:** All hooks and skills are executable and enforcing the spec cascade

- [ ] Hooks: Path validation
- [ ] Hooks: Spec cascade gate
- [ ] Hook: post-pr-wait (executable)
- [ ] Skills: /opsx:propose
- [ ] Skills: /opsx:apply
- [ ] Skills: /opsx:archive

## M2: Execution Engine
**Goal:** Deterministic automation
**Completion criteria:** All CLI scripts operational, JSON data passing working end-to-end

- [ ] CLI: State manager
- [ ] CLI: Context injector
- [ ] CLI: OpenSpec lifecycle
- [ ] JSON inter-flow data passing

## M3: Scaling
**Goal:** Project onboarding
**Completion criteria:** New projects can be initialized with a single CLI command

- [ ] Template automation
- [ ] Project initialization
- [ ] Template evolution (Approach C)
