# Spec Cascade

The spec cascade is the mandatory workflow that every feature must follow before any code is written. It enforces a strict ordering from design through implementation, ensuring that each step is grounded in the previous one.

## Why It Exists

The cascade exists for three reasons:

1. **Traceability** -- Every line of code can be traced back through tests, test specs, behavior specs, and the original proposal.
2. **Quality enforcement** -- Tests are written before code (TDD), so implementation is driven by specifications rather than ad-hoc decisions.
3. **Role isolation** -- Each step is handled by a different specialized agent, preventing any single agent from controlling the full pipeline.

## The Five Steps

```
proposal -> behavior_spec -> test_spec -> tests -> code
```

### Step 1: Proposal

**Produced by**: Sonders (Creative Architect), reviewed by Negator (Critical Architect)

**What it contains**: The architectural design for a feature -- what it does, how it fits into the system, and what constraints it must respect.

**Location**: `runtime/openspec/changes/<feature>/proposal.md`

**Gate**: The proposal must be approved by both Sonders and Negator (with the human as tie-breaker) before proceeding.

### Step 2: Behavior Spec

**Produced by**: Behavior Spec Writer

**What it contains**: Formal Given/When/Then specifications for every observable behavior of the feature, including error cases and edge cases.

**Format**:
```
### Behavior: <short description>

**Given** <precondition>
**When** <action>
**Then** <expected outcome>
```

**Location**: `runtime/openspec/changes/<feature>/behavior_spec.md`

**Gate**: The behavior spec must cover ALL behaviors described in the approved design with no gaps.

### Step 3: Test Spec

**Produced by**: Test Spec Writer

**What it contains**: Test specifications derived from the behavior spec. Each test spec defines the test type (unit, integration, E2E), which behavior it covers, what assertions it makes, required fixtures/mocks, and which SDET agent is responsible.

**Format**:
```
### Test: <behavior reference>

**Type:** Unit | Integration | E2E
**Covers behavior:** <link to behavior in behavior_spec.md>
**Setup:** <test data, fixtures, mocks>
**Assert:** <specific assertion>
**Teardown:** <cleanup if needed>
```

**Location**: `runtime/openspec/changes/<feature>/test_spec.md`

**Gate**: Every behavior in `behavior_spec.md` must have at least one corresponding test spec.

### Step 4: Tests

**Produced by**: SDET agents (SDET:Unit, SDET:Integration, SDET:E2E)

**What they produce**: Actual test code implementing the test specs. Tests are written BEFORE implementation code (TDD). They should fail initially -- passing tests serve as the benchmark for worker success.

**Location**: Test files in the project codebase (paths determined by the project's testing strategy).

**Gate**: All test specs must be implemented. The test-spec-writer assigns each test to a specific SDET agent type.

### Step 5: Code

**Produced by**: Workers (dispatched by Team Lead)

**What they produce**: Implementation code that makes the failing tests pass. Workers execute in isolated git worktrees with declared file scopes.

**Location**: Source files in the project codebase.

**Gate**: All tests must pass. Workers must not touch files outside their declared scope. The regression runner verifies the full test suite, then the auditor reviews architectural compliance.

## Evaluation Criteria

The evaluation framework checks the spec cascade through the p1 category questions:

| Question | What It Checks | Tier |
|---|---|---|
| p1.1 | Did every feature have a proposal before any other spec? | seed |
| p1.2 | Did behavior_spec exist before test_spec was written? | tier-2 |
| p1.3 | Did test_spec exist before any test files were written? | seed |
| p1.4 | Did test files exist before implementation code was written? | tier-2 |
| p1.5 | Are all spec documents non-trivial (>50 lines or substantive content)? | tier-3 |
| p1.6 | Did every feature complete the full cascade (no skipped stages)? | seed |

These checks use git commit timestamps and file modification times to verify ordering. See [Evaluation Framework](eval-framework.md) for details.

## OpenSpec Lifecycle

Each feature lives in `runtime/openspec/changes/<feature>/` during development. The folder contains:

- `proposal.md` -- Approved design
- `behavior_spec.md` -- Behavioral specifications
- `test_spec.md` -- Test specifications
- `tasks.md` -- Task breakdown with file-scope declarations
- `status.md` -- Feature status tracking

After the feature is merged, the entire folder is moved to `runtime/openspec/archive/` and the OpenSpec index is updated.
