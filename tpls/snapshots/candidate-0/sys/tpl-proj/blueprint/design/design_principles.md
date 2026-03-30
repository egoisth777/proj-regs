# Design Principles

These are the guiding principles for all design and implementation decisions in the MAS Harness system.

## 1. Specification Cascade

All changes must pass through a formalization chain before any code is written:

```
Requirements → Behaviors → Behavior Specs (Given/When/Then) → Test Specs → Tests → Code
```

Each step formalizes the previous one, reducing ambiguity at every layer. Behaviors are observable and testable — they are the bridge between vague requirements and precise implementation.

## 2. Minimum Context

Each agent receives only the minimum context needed to complete its work without breaking the system. Context is injected via `context_map.json`, not by agents browsing the registry.

- Workers get: blueprint (static) + their feature's OpenSpec. Nothing else.
- Orchestrator sees the full picture. No other agent does.

## 3. Blueprint Immutability During Sprints

The static blueprint is frozen during sprint execution. Architecture may only evolve between milestone completions, through the Sonders/Negator review process.

## 4. Simplicity Over Cleverness

Avoid over-engineering. Write code that is easy to read and maintain. Three similar lines of code is better than a premature abstraction.

## 5. Traceability

All complex decisions must be documented via Implementation Decision Records (`IR-xxx.md`). Code marked with `// [IR-xxx]` has a corresponding explanation in `runtime/implementation/`.

## 6. Separation of Concerns

Keep components and modules isolated to their specific responsibilities. The Auditor reviews architecture — it does not run tests. The Regression Runner runs tests — it does not review architecture.

## 7. Testability

If it's hard to test, it's designed wrong. Every feature produces tests through the spec cascade before any implementation begins (TDD).
