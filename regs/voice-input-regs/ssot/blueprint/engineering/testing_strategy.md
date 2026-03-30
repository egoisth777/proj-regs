# Testing Strategy

This document outlines the testing approach and requirements for the MAS Harness project.

## 1. Behavior-Driven + Test-Driven Development

The spec cascade ensures tests are designed before implementation:

1. **Behavior Specs** (Given/When/Then) define expected behaviors
2. **Test Specs** formalize those into testable assertions
3. **SDET agents** write actual test code before Workers write implementation

Tests must fail initially — they serve as the benchmark for Worker success.

## 2. Specialized SDET Agents

| Agent | Test Type | Input | Scope |
|---|---|---|---|
| SDET:Unit | Unit tests | `test_spec.md` | Isolated functions and logic |
| SDET:Integration | Integration tests | `test_spec.md` + `architecture_overview.md` | Component boundaries and system interactions |
| SDET:E2E | End-to-end tests | `behavior_spec.md` | Crucial user/agent workflows |

Each SDET type has different inputs because each test type validates at a different level of abstraction.

## 3. Pre-Merge Quality Gate

Before any PR merges, ALL of the following must pass:

1. **Feature tests** — unit + integration + E2E written by SDET agents for this feature
2. **Regression suite** — ALL existing tests across the entire codebase
3. **Linter** — code style and quality checks
4. **Architectural review** — Auditor verifies alignment with blueprint + OpenSpec

The Regression Runner (test execution) and Auditor (architectural review) are separate agents to isolate concerns.

## 4. Parallel Feature Merge

When multiple features complete around the same time:
- Each opens its own PR
- Each must independently pass the full test suite (not just its own feature tests)
- First-merged wins; subsequent features must rebase onto the updated main and re-run the entire quality gate
- No merge until all gates clear

## 5. CI/CD Requirements

- Tests must be run on every PR
- PRs cannot be merged without 100% test pass rate
- Post-PR hook polls remote CI and review bot feedback before allowing merge
