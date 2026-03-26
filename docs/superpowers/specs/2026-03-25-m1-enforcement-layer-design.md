# M1: Enforcement Layer — Design Spec

**Date:** 2026-03-25
**Status:** Approved
**Subject:** Hooks, setup script, and shared utilities for the MAS Harness enforcement layer
**Parent spec:** `docs/superpowers/specs/2026-03-24-mas-harness-registry-design.md`

> **Scope:** This spec covers M1.0 — enforcement hooks and the setup script. Skills (`/opsx:propose`, `/opsx:apply`, `/opsx:archive`) are deferred to a follow-up M1.1 spec.
>
> **Note:** The setup script (`init_project.py`) is a deliberate scope pull-forward from M3 (Scaling). You cannot install hooks without a setup mechanism. M3 will handle the more advanced template automation and registry creation; M1's setup script covers only hook/skill installation.

---

## 1. Overview

M1 builds the executable enforcement layer for the MAS Harness. The goal is to stop agents from misbehaving by installing automated guardrails (hooks) that fire on Claude Code tool events.

Currently the harness is protocol-only — agents follow rules written in markdown. M1 adds executable enforcement:

- **Path validation hook** — blocks writes to unauthorized paths based on agent role
- **Spec cascade gate hook** — blocks code implementation until the full spec cascade is complete
- **Post-PR-wait hook** — blocks the agent after PR creation until CI + reviews complete
- **Setup script** — installs all of the above into a target project

## 2. Architecture

### Repo Structure

The executable layer lives in a sibling directory to the registry vault, keeping the Obsidian vault pure:

```
proj-regs/
├── mas-harness/              # Pure Obsidian vault (SSoT) — unchanged
├── harness-cli/              # NEW — executable layer
│   ├── pyproject.toml
│   ├── package.json
│   ├── tsconfig.json
│   │
│   ├── hooks/
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── branch_parser.py      # Git branch → role + feature
│   │   │   └── config_loader.py      # .harness.json + context_map.json loader
│   │   ├── path_validator.py          # PreToolUse hook: block unauthorized writes
│   │   ├── spec_cascade_gate.py       # PreToolUse hook: block code before spec cascade
│   │   └── post_pr_wait.ts           # PostToolUse hook: poll GitHub PR
│   │
│   ├── setup/
│   │   ├── init_project.py           # Setup script entry point
│   │   └── templates/
│   │       ├── CLAUDE.md.tpl         # Template for project's CLAUDE.md
│   │       └── AGENTS.md.tpl         # Template for project's AGENTS.md
│   │
│   └── tests/
│       ├── test_branch_parser.py
│       ├── test_config_loader.py
│       ├── test_path_validator.py
│       ├── test_spec_cascade_gate.py
│       ├── test_post_pr_wait.ts
│       └── test_init_project.py
│
└── reg-tpls/                 # Existing templates — unchanged
```

### Technology Split

| Language | Components | Rationale |
|---|---|---|
| Python | path_validator, spec_cascade_gate, setup script, shared utils | File validation, JSON parsing, synchronous checks — no build step |
| TypeScript | post_pr_wait, TS config loader | Async GitHub polling, complex flow control |

### How Hooks Integrate with Claude Code

Claude Code hooks are configured in the project's `.claude/settings.local.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "command": "python <harness-cli-path>/hooks/path_validator.py"
      },
      {
        "matcher": "Write|Edit",
        "command": "python <harness-cli-path>/hooks/spec_cascade_gate.py"
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "command": "node <harness-cli-path>/hooks/post_pr_wait.js"
      }
    ]
  }
}
```

Hooks receive tool use context via stdin (JSON) from Claude Code and return a decision via stdout.

> **Note on hook protocol:** The input/output JSON schemas shown in this spec are based on Claude Code's hook protocol. The implementer must verify these against the actual Claude Code hook documentation before implementation. Key fields: `tool_name`, `tool_input` (PreToolUse), and `tool_output` (PostToolUse — field name may differ). If the protocol differs, adapt the hook parsing accordingly.

## 3. Role Inference Convention

Hooks do not rely on environment variables set by the orchestrator. Instead, they infer the agent's role and current feature from the git branch name and project config.

### Branch Naming Convention

```
feat/<feature-name>/<role>[-<instance>]
```

Examples:
- `feat/path-validation/worker-1`
- `feat/path-validation/sdet-unit`
- `feat/path-validation/team-lead`
- `feat/path-validation/auditor`

### Inference Logic (shared utility: `branch_parser.py`)

1. Run `git branch --show-current` to get the current branch
2. Parse against pattern `feat/<feature>/<role>[-<instance>]`
3. Return `{ "feature": "<feature>", "role": "<role>" }`
4. **Fallback:** If the branch doesn't match the convention (e.g., on `main`), return `{ "feature": null, "role": "orchestrator" }` — orchestrator constraints apply (no direct writes). This is an intentional fail-safe: unknown context = most restrictive role.

**Feature folder resolution:** The branch `<feature-name>` may not exactly match the OpenSpec folder name (which uses `<YYYY-MM-DD-feature>` format with a date prefix). The config loader resolves this by scanning `runtime/openspec/changes/` for folders ending with `-<feature-name>`. For example, branch `feat/path-validation/worker-1` → feature `path-validation` → matches folder `2026-03-25-path-validation/`. If multiple folders match, use the most recent (by date prefix). If none match, the hook treats the feature as having no OpenSpec (spec cascade gate blocks, path validator uses orchestrator constraints).

**Path comparison:** All path comparisons are relative to the project root. The project root is determined by walking up from CWD to find `.harness.json`. Tool input paths (absolute) are converted to project-relative paths before matching against role-allowed patterns. Patterns are matched using `fnmatch` (Python) or equivalent glob matching.

### Config Loading (shared utility: `config_loader.py`)

1. Walk up from CWD to find `.harness.json` in the project root
2. Read `registry_path` from `.harness.json`
3. Load `context_map.json` from the registry
4. Load feature-specific OpenSpec files from `runtime/openspec/changes/<feature>/`

### `.harness.json` Schema

Created by the setup script in the project root:

```json
{
  "registry_path": "/absolute/path/to/mas-harness",
  "harness_cli_path": "/absolute/path/to/harness-cli",
  "version": "1.0.0"
}
```

## 4. Hook Specifications

### Hook 1: Path Validator (`path_validator.py`)

**Trigger:** Claude Code `PreToolUse` on `Write`, `Edit`

**Input:** Tool use context via stdin (JSON from Claude Code):
```json
{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/target/file.py"
  }
}
```

**Logic:**
1. Call `branch_parser.parse()` → get `role` and `feature`
2. Call `config_loader.load()` → get `context_map.json`
3. Determine allowed paths based on role:

| Role | Allowed Write Paths |
|---|---|
| orchestrator | **NONE** — pure delegator, no direct writes |
| sonders | `blueprint/design/*` only |
| negator | `blueprint/design/*` only (annotations) |
| behavior-spec-writer | `runtime/openspec/changes/<feature>/behavior_spec.md` only |
| test-spec-writer | `runtime/openspec/changes/<feature>/test_spec.md` only |
| team-lead | `runtime/openspec/changes/<feature>/tasks.md`, `runtime/openspec/changes/<feature>/status.md` |
| worker | Files declared in task's file scope (parsed from `tasks.md`) |
| sdet-unit | `tests/**/*` (test directories only) |
| sdet-integration | `tests/**/*` (test directories only) |
| sdet-e2e | `tests/**/*` (test directories only) |
| auditor | **NONE** — review only, no writes |
| regression-runner | **NONE** — test execution only, no writes |

4. Compare target file path against the role's allowed paths
5. **Output:**
   - If allowed: `{ "decision": "allow" }`
   - If blocked: `{ "decision": "block", "reason": "Role '<role>' is not allowed to write to '<path>'. Allowed paths: <list>" }`

**Worker file scope parsing:**

The worker's allowed paths are dynamic — parsed from the feature's `tasks.md`. The parsing algorithm:

1. Read `tasks.md` from the feature's OpenSpec folder
2. Split into task blocks (delimited by `### Task N:` headings)
3. For each task block, extract:
   - **File scope:** lines matching `- \`<path>\`` under the `**File scope:**` heading
   - **Assignee:** value after `**Assignee:**`
4. **Task-to-worker mapping:** The worker's branch instance suffix (e.g., `worker-1`) maps to the task number. `worker-1` → Task 1, `worker-2` → Task 2, etc. This is a simple positional convention — the Team Lead assigns tasks in order.
5. The worker is allowed to write ONLY to files listed in its assigned task's file scope.

Example: Given `tasks.md` with:
```markdown
### Task 1: Add auth handler
**File scope:**
- `src/auth/handler.py`
- `src/auth/utils.py`
**Assignee:** @Worker
```

A worker on branch `feat/my-feature/worker-1` is allowed to write to `src/auth/handler.py` and `src/auth/utils.py` only.

If `tasks.md` doesn't exist or the worker's task number exceeds the task count, block all worker writes.

**Edge cases:**
- The `tests/` path pattern for SDETs is configurable per-project (future: via `.harness.json`). Default: `tests/**/*`, `test/**/*`, `*_test.*`, `test_*.*`.
- If `.harness.json` is not found, the hook logs a warning and allows the write (non-breaking degradation).

### Hook 2: Spec Cascade Gate (`spec_cascade_gate.py`)

**Trigger:** Claude Code `PreToolUse` on `Write`, `Edit` for files matching project source patterns (not tests, not registry, not config)

**Input:** Same as path validator — tool use context via stdin.

**Logic:**
1. Determine if the target file is a "source file" by checking against an **exclusion list**. The file is NOT a source file (and the hook allows it) if it matches any of these patterns:
   - `tests/**/*`, `test/**/*`, `*_test.*`, `test_*.*` (test files — SDETs are exempt)
   - `*.md` (documentation and spec files)
   - `.harness.json`, `.gitignore`, `*.toml`, `*.json`, `*.yaml`, `*.yml` (config files)
   - `.claude/**/*`, `.agents/**/*`, `.github/**/*` (tooling config)
   - Any path inside the registry directory (resolved from `.harness.json`)

   If the file matches any exclusion, **allow**. Otherwise it's treated as a source file and the cascade check applies. This exclusion list can be extended per-project via a `source_excludes` field in `.harness.json` (future).
2. Call `branch_parser.parse()` → get `feature`
3. If no feature detected (e.g., on `main`), **allow** (this hook only applies during feature development)
4. Call `config_loader.load()` → locate the feature's OpenSpec folder
5. Check that ALL required spec cascade files exist and are non-empty:
   - `runtime/openspec/changes/<feature>/proposal.md` — must exist, >50 chars (not just template)
   - `runtime/openspec/changes/<feature>/behavior_spec.md` — must exist, >50 chars
   - `runtime/openspec/changes/<feature>/test_spec.md` — must exist, >50 chars
6. Check `runtime/openspec/changes/<feature>/status.md` — phase must be `execution` or later (valid phases that allow code: `execution`, `quality-gate`, `pr-review`). The intermediate `testing` phase (SDETs writing tests) correctly blocks source code writes — SDET writes are to test files, which are excluded in step 1.

**Phase transition responsibility:** Phase transitions in `status.md` are written by the Orchestrator (via dispatched subagents) at each workflow boundary:
   - `design` → `spec-cascade`: after Sonders/Negator approve design
   - `spec-cascade` → `testing`: after behavior_spec.md + test_spec.md are complete
   - `testing` → `execution`: after all SDET agents finish writing tests
   - `execution` → `quality-gate`: after Workers complete, before Regression Runner
   - `quality-gate` → `pr-review`: after PR is created
   - `pr-review` → `merged`: after PR merges
   - `merged` → `archived`: during `/opsx:archive`

7. **Output:**
   - If cascade complete: `{ "decision": "allow" }`
   - If incomplete: `{ "decision": "block", "reason": "Spec cascade incomplete for feature '<feature>'. Missing/empty: <list>. Current phase: <phase>. Code implementation requires phase 'execution' or later." }`

**Edge cases:**
- The 50-char minimum prevents template files from passing (templates have placeholder text shorter than real content)
- If the OpenSpec folder doesn't exist at all, block with "No OpenSpec found for feature '<feature>'"
- SDET agents writing tests are exempt — they run BEFORE code and their writes are to test files (caught by the "is it a source file?" check in step 1)

### Hook 3: Post-PR-Wait (`post_pr_wait.ts`)

**Trigger:** Claude Code `PostToolUse` on `Bash` when the command output contains a GitHub PR URL (pattern: `github.com/.*/pull/\d+`)

**Input:** Tool use result via stdin (JSON from Claude Code):
```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "gh pr create --fill --base main"
  },
  "tool_output": "https://github.com/owner/repo/pull/42\n"
}
```

**Logic (async TypeScript):**
1. Parse the PR URL from the tool output → extract `owner`, `repo`, `pr_number`
2. Enter polling loop (30-second intervals):
   a. Run `gh pr checks <pr_number> --json name,state,conclusion`
   b. If any check is `FAILURE` → return failure report immediately (no need to wait for reviews)
   c. If all checks are `SUCCESS` → exit loop, proceed to step 3
   d. If checks are still `PENDING` → wait 30 seconds, repeat
3. Fetch reviews: `gh api repos/{owner}/{repo}/pulls/{pr_number}/reviews`
4. Fetch comments: `gh api repos/{owner}/{repo}/pulls/{pr_number}/comments`
5. Aggregate feedback into a structured report
6. **Output:**
```json
{
  "decision": "allow",
  "feedback": {
    "checks_passed": true,
    "reviews": [...],
    "comments": [...],
    "summary": "All CI checks passed. 2 reviews received. 3 comments to address."
  }
}
```

**Timeout:** After 30 minutes of polling, return:
```json
{
  "decision": "allow",
  "feedback": {
    "timeout": true,
    "summary": "Polling timed out after 30 minutes. Manual review required."
  }
}
```

The hook allows (not blocks) on timeout to avoid permanently stalling the agent. The timeout message alerts the agent to escalate.

**Edge cases:**
- If `gh` CLI is not installed or not authenticated, log error and allow (non-breaking)
- If the Bash command is not `gh pr create` (just happens to output a PR URL), the hook still fires — this is acceptable since the feedback is informative, not destructive
- Multiple PRs in one session: hook fires per PR URL detected

## 5. Setup Script (`init_project.py`)

**Invocation:**
```bash
python harness-cli/setup/init_project.py \
  --project /path/to/target-project \
  --registry /path/to/mas-harness
```

**Steps:**

### Step 1: Validate inputs
- Verify `--project` exists and is a git repo
- Verify `--registry` exists and contains `context_map.json`
- Verify `harness-cli/` exists relative to the script

### Step 2: Create `.harness.json`
Write to project root:
```json
{
  "registry_path": "<absolute --registry path>",
  "harness_cli_path": "<absolute path to harness-cli/>",
  "version": "1.0.0"
}
```

### Step 3: Copy CLAUDE.md and AGENTS.md
Copy from `harness-cli/setup/templates/CLAUDE.md.tpl` and `AGENTS.md.tpl` to the project root, substituting:
- `{{REGISTRY_PATH}}` → absolute registry path
- `{{PROJECT_NAME}}` → project directory name

### Step 4: Symlink `.agents/`
```bash
ln -s <registry>/blueprint/orchestrate-members <project>/.agents
```
If `.agents/` already exists, warn and skip (don't overwrite).

### Step 5: Configure hooks in `.claude/settings.local.json`
Create or merge into the project's `.claude/settings.local.json`:
- `PreToolUse` hooks for path_validator and spec_cascade_gate
- `PostToolUse` hook for post_pr_wait
- All commands use absolute paths to `harness-cli/hooks/`

If the file already exists, merge hooks into existing config (don't overwrite other settings).

### Step 6: Add to .gitignore
Append to the project's `.gitignore` (if not already present):
```
CLAUDE.md
AGENTS.md
.claude/
.harness.json
```

### Step 7: Report
Print a summary of what was installed:
```
MAS Harness initialized for: /path/to/project
  Registry: /path/to/mas-harness
  CLAUDE.md: created
  AGENTS.md: created
  .agents/: symlinked → .../blueprint/orchestrate-members/
  Hooks: path_validator, spec_cascade_gate, post_pr_wait
  .gitignore: updated
```

## 6. CLAUDE.md Template Content

The CLAUDE.md installed into the target project must include:

1. **SSoT routing** — points agents to the registry at `{{REGISTRY_PATH}}`
2. **Role identification** — agents must identify as Main Agent (orchestrator) or Sub Agent (worker/sdet/etc.)
3. **Sprint definition** — "Sprint = one feature's lifecycle, NOT time-boxed"
4. **Core disciplines** — DOs and DON'Ts from the registry spec
5. **Orchestrator constraint** — "Main agent NEVER reads/writes files directly"
6. **Branch naming convention** — `feat/<feature>/<role>[-<instance>]`
7. **Spec cascade requirement** — "All code must have a completed spec cascade before implementation"

This is derived from the existing template's CLAUDE.md but updated to reflect the evolved design (no `blueprints/` plural, new agent roles, pure delegator orchestrator).

## 7. Testing Strategy

### Python (pytest)

**`test_branch_parser.py`:**
- `feat/path-validation/worker-1` → `{"feature": "path-validation", "role": "worker"}`
- `feat/my-feature/sdet-unit` → `{"feature": "my-feature", "role": "sdet-unit"}`
- `feat/my-feature/team-lead` → `{"feature": "my-feature", "role": "team-lead"}`
- `main` → `{"feature": null, "role": "orchestrator"}`
- `develop` → `{"feature": null, "role": "orchestrator"}`
- `feat/no-role` → `{"feature": "no-role", "role": "orchestrator"}` (missing role segment — fail-safe)
- `feat/my-feature/worker/extra` → `{"feature": "my-feature", "role": "worker"}` (extra segments ignored)
- `feat/fix-#123/worker-1` → `{"feature": "fix-#123", "role": "worker"}` (special characters in feature name)
- Detached HEAD (no branch) → `{"feature": null, "role": "orchestrator"}`

**`test_config_loader.py`:**
- Valid `.harness.json` → loads correctly
- Missing `.harness.json` → returns None with warning
- Valid `context_map.json` → all 12 roles present
- Missing `context_map.json` → raises clear error

**`test_path_validator.py`:**
- Worker writes to declared file scope (parsed from tasks.md, task matches worker instance) → allow
- Worker writes outside file scope → block
- Worker-1 writes to Task 2's file scope → block (wrong task assignment)
- Worker with no tasks.md → block
- Orchestrator writes anything → block
- Auditor writes anything → block
- Sonders writes to `blueprint/design/` → allow
- Sonders writes to `src/` → block
- SDET writes to `tests/` → allow
- SDET writes to `src/` → block
- No `.harness.json` found → allow (degraded mode)

**`test_spec_cascade_gate.py`:**
- All spec files present + phase=execution → allow
- Missing behavior_spec.md → block
- Empty test_spec.md (template only, <50 chars) → block
- Phase=design → block
- Phase=spec-cascade → block
- Phase=testing → block (SDETs write tests, but not source code)
- Phase=execution → allow
- Phase=quality-gate → allow
- Writing to test file → allow (exempt)
- On `main` branch (no feature) → allow

**`test_init_project.py` (integration):**
- Run against a temp directory → verify all files created
- Verify `.harness.json` content
- Verify `.claude/settings.local.json` hook entries
- Verify `.agents/` symlink points to correct target
- Verify `.gitignore` updated
- Run twice → second run doesn't duplicate entries

### TypeScript (vitest)

**`test_post_pr_wait.ts`:**
- Mock `gh pr checks` → all pass → returns feedback with checks_passed=true
- Mock `gh pr checks` → one fails → returns failure immediately
- Mock `gh pr checks` → pending then pass → polls and returns
- Mock timeout → returns timeout feedback
- No `gh` CLI → allows with warning
- Output doesn't contain PR URL → no-op

## 8. Delivery Order

Tasks should be implemented in this order:

```
1. Project scaffolding (pyproject.toml, package.json, tsconfig.json, directory structure)
2. Shared Python utilities (branch_parser.py, config_loader.py) + tests
3. Path validation hook + tests
4. Spec cascade gate hook + tests
5. Post-PR-wait hook (TypeScript) + tests
6. CLAUDE.md / AGENTS.md templates
7. Setup script (init_project.py) + integration test
8. Manual validation: run setup on a test project, verify hooks fire correctly
```

## 9. Key Design Decisions

| Decision | Rationale |
|---|---|
| Infer role from branch name, not env vars | More resilient — no reliance on orchestrator correctly setting vars. Uses data that already exists. |
| `.harness.json` in project root | Single file hooks read to find the registry. Avoids hardcoded paths. |
| Non-breaking degradation | If `.harness.json` missing or `gh` not installed, hooks warn and allow. Never crash the agent. |
| 50-char minimum for spec files | Prevents template placeholder text from passing the cascade gate. Real specs are always longer. |
| Post-PR-wait allows on timeout | Avoids permanently stalling the agent. Timeout message prompts human escalation. |
| `settings.local.json` not `settings.json` | Local settings aren't shared across machines. Each developer runs setup independently. |
| Skills deferred to M1.1 | Hooks and skills are independent concerns. Hooks provide enforcement regardless of whether agents use `/opsx`. |
| Python for sync hooks, TS for async | Python is simpler for file validation. TS is better for async GitHub polling. |
| Absolute paths in hook commands | Hooks work regardless of CWD. Setup script resolves paths at install time. |
