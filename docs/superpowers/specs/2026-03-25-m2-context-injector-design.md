# M2: Context Injector — Design Spec

**Date:** 2026-03-25
**Status:** Approved
**Subject:** CLI tool that assembles minimum-context prompts for subagents based on `context_map.json`
**Parent spec:** `docs/superpowers/specs/2026-03-24-mas-harness-registry-design.md`

> **Scope:** This spec covers the context injector — the core deliverable of M2. The other M2 roadmap items (OpenSpec lifecycle, state manager) are already handled by the forked OpenSpec CLI and M1 hooks respectively.

---

## 1. Overview

The context injector is a Python CLI that the orchestrator calls when dispatching a subagent. It reads `context_map.json`, resolves the role's required documents, reads their content from the registry, and outputs an assembled context blob ready to inject into the subagent's prompt.

This is the executable form of the "minimum context principle" — each agent gets only the docs it needs, assembled automatically.

## 2. CLI Interface

**Invocation:**
```bash
python harness-cli/context/inject.py \
  --role <role-name> \
  --feature <feature-name> \
  --project <path-to-project> \
  [--format json|text]
```

**Arguments:**

| Arg | Required | Description |
|---|---|---|
| `--role` | Yes | Agent role name (must exist in `context_map.json`) |
| `--feature` | No | Feature name (required for roles with `<feature>` placeholders) |
| `--project` | No | Path to the project (defaults to CWD, used to find `.harness.json`) |
| `--format` | No | Output format: `json` (default) or `text` |

**JSON output (`--format json`):**
```json
{
  "role": "worker",
  "feature": "voice-capture",
  "role_definition": "---\nname: Worker\n...\n# Role: Worker\n...",
  "docs": [
    {
      "path": "blueprint/engineering/dev_workflow.md",
      "content": "# Development Workflow\n..."
    },
    {
      "path": "runtime/openspec/changes/2026-03-25-voice-capture/tasks.md",
      "content": "### Task 1: Create voice capture module\n..."
    }
  ],
  "prompt_prefix": "You are a Worker agent dispatched for feature 'voice-capture'.\n\n## Your Role\n---\nname: Worker\n...\n\n## Context Documents\n\n### blueprint/engineering/dev_workflow.md\n# Development Workflow\n...\n\n---\n\n### runtime/openspec/changes/2026-03-25-voice-capture/tasks.md\n### Task 1: ...\n"
}
```

**Text output (`--format text`):**
Outputs just the `prompt_prefix` as plain text — ready to paste directly into a subagent prompt.

**Error output:**
```json
{
  "error": "Role 'foo' not found in context_map.json"
}
```

## 3. Architecture

### New Files

```
harness-cli/
├── context/
│   ├── __init__.py
│   └── inject.py          # CLI entry point + core logic
└── tests/
    └── test_inject.py     # Unit + integration tests
```

### Reused Utilities (from M1)

| Utility | Used for |
|---|---|
| `config_loader.find_project_root()` | Locate `.harness.json` from project path |
| `config_loader.load_harness_config()` | Read registry_path from `.harness.json` |
| `config_loader.load_context_map()` | Load `context_map.json` |
| `config_loader.resolve_feature_folder()` | Resolve `<feature>` to actual OpenSpec folder |

No new utilities needed — M1's config_loader handles all the resolution logic.

**Import path:** `from hooks.utils.config_loader import find_project_root, load_harness_config, load_context_map, resolve_feature_folder`

> **Note:** `resolve_feature_folder()` returns an **absolute path**. The injector must convert it to a registry-relative path using `os.path.relpath(resolved, registry_path)` before substituting `<feature>` placeholders.

> **Out of scope:** `path_based_rules` in `context_map.json` will not be processed by the context injector. This field is present but empty; support will be added in a future milestone.

## 4. Core Logic

### `assemble_context(role, feature, registry_path) -> dict`

1. **Load context map:** `load_context_map(registry_path)` → get `agent_role_context`
2. **Validate role:** Check `role` exists in `agent_role_context`. If not, return error.
3. **Get required docs:** `agent_role_context[role]["required_docs"]` → list of paths
4. **Resolve `<feature>` placeholders:**
   - For each path containing `<feature>`, call `resolve_feature_folder(registry_path, feature)` to get the actual folder
   - Replace `<feature>` with the resolved path relative to registry root
   - If `<feature>` placeholder exists but `--feature` was not provided, return error
5. **Read role definition:** Load `blueprint/orchestrate-members/<role>.md` from registry. If role name contains hyphens (e.g., `sdet-unit`), the file is `sdet-unit.md`.
6. **Read each doc:** For each resolved path, read the file from the registry. If file doesn't exist, include `{"path": "...", "content": null, "error": "File not found"}`.
7. **Assemble prompt_prefix:**

   If `--feature` is provided:
   ```
   You are a <Role Name> agent dispatched for feature '<feature>'.

   ## Your Role
   <content of role definition file>

   ## Context Documents

   ### <doc1 path>
   <doc1 content>

   ---

   ### <doc2 path>
   <doc2 content>
   ```

   If `--feature` is NOT provided (roles like orchestrator, regression-runner):
   ```
   You are a <Role Name> agent.

   ## Your Role
   <content of role definition file>

   ## Context Documents

   ### <doc1 path>
   <doc1 content>
   ```

   Note: `--feature` is silently ignored if the role has no `<feature>` placeholders in its `required_docs`. All `<feature>` tokens in a role's doc list resolve to the same single feature folder.
8. **Return:** `{"role": ..., "feature": ..., "role_definition": ..., "docs": [...], "prompt_prefix": ...}`

### `main()`

1. Parse CLI args
2. Find project root from `--project` (or CWD)
3. Load harness config → get `registry_path`
4. Call `assemble_context(role, feature, registry_path)`
5. Output as JSON or text based on `--format`

## 5. Feature Resolution

When `context_map.json` lists docs with `<feature>` placeholders:

```json
"worker": {
  "required_docs": [
    "blueprint/engineering/dev_workflow.md",
    "<feature>/tasks.md"
  ]
}
```

The injector:
1. Calls `resolve_feature_folder(registry_path, feature_name)` — scans `runtime/openspec/changes/` for folders ending with `-<feature_name>`
2. Replaces `<feature>` with the resolved relative path, e.g., `runtime/openspec/changes/2026-03-25-voice-capture`
3. The full resolved path becomes `runtime/openspec/changes/2026-03-25-voice-capture/tasks.md`

Roles that don't have `<feature>` placeholders (e.g., `regression-runner`) don't need `--feature`.

## 6. Edge Cases

| Scenario | Behavior |
|---|---|
| Unknown role | Return `{"error": "Role 'foo' not found in context_map.json"}`, exit code 1 |
| `<feature>` placeholder but no `--feature` arg | Return `{"error": "Role 'worker' requires --feature but none provided"}`, exit code 1 |
| Feature not found in registry | Return `{"error": "No OpenSpec folder found for feature 'xyz'"}`, exit code 1 |
| Doc file missing | Include in docs array with `"content": null, "error": "File not found"`. Do NOT crash. |
| Role definition file missing | Set `role_definition` to `null`. Include warning in output. |
| No `.harness.json` | Return `{"error": "No .harness.json found. Run init_project.py first."}`, exit code 1 |
| Empty `required_docs` list | Valid — some roles may have no required docs. Return empty docs array. |

## 7. Testing Strategy

### Unit Tests (`test_inject.py`)

**Role resolution:**
- All 12 roles from `context_map.json` resolve to correct doc lists
- Unknown role returns error
- Role with `<feature>` placeholder + valid feature → correct path resolution
- Role with `<feature>` placeholder + missing `--feature` → error
- Role without `<feature>` placeholder + no `--feature` → works fine

**Doc reading:**
- Existing doc file → content returned
- Missing doc file → `content: null, error: "File not found"`
- Role definition file exists → included in output
- Role definition file missing → `role_definition: null`

**Prompt assembly:**
- `prompt_prefix` contains role name
- `prompt_prefix` contains role definition content
- `prompt_prefix` contains all doc contents separated by `---`
- `prompt_prefix` contains feature name when applicable

**Format:**
- `--format json` → valid JSON to stdout
- `--format text` → plain text prompt_prefix only

**CLI contract:**
- Error exits with code 1 (unknown role, missing feature, no .harness.json)
- Success exits with code 0
- `--project` defaults to CWD when omitted
- `--feature` silently ignored for roles without `<feature>` placeholders
- Resolved doc paths in output are relative to registry root (not absolute)

**Integration test (against real registry):**
- Run against `voice-input-to-markdown` registry with `--role worker --feature voice-capture`
- Verify output contains real content from `dev_workflow.md` and `tasks.md`
- Run all 12 roles and verify none crash

## 8. Delivery Order

```
1. Create context/ directory + __init__.py
2. Write tests (TDD)
3. Implement inject.py
4. Integration test against real registry
5. Commit
```

## 9. Key Design Decisions

| Decision | Rationale |
|---|---|
| Reuse M1 config_loader | All resolution logic already exists. No duplication. |
| Non-fatal missing docs | A missing doc shouldn't block subagent dispatch. The orchestrator can decide what to do. |
| `--format text` option | Enables simple paste-into-prompt workflow without JSON parsing. |
| No caching | Docs are read fresh each time. Registry files change during sprints. Caching would risk stale context. |
| Role definition auto-included | The subagent needs to know its role. Including the role .md file automatically saves the orchestrator a step. |
| Exit code 1 on errors | Lets the orchestrator detect failures programmatically. |
