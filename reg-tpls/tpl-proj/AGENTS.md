# Project Memory
## MAS Agent Configuration (Root)

1. This repository is managed by a **Multi-Agent System (MAS)**. 
2. You are an executive AGENT with **0-state Memory**
3. . **All context, planning, tracking, and design docs live EXCLUSIVELY in the [Project Registry](link-to-project-registry).**
  
## SSoT Routing
You MUST first _read_ the **Project Registry** as **SSoT**:  [Project Registry-Entry](link-to-project-registry-entry).
- `/`
    - `/blueprints/`- Blueprint design documentation (static)
	    - `/blueprints/design/`
	        - `/blueprints/design/architecture_overview.md`
            - `/blueprints/design/design_principles.md` - Design principles
            - `/blueprints/design/api_mapping.md` - API mapping
		- `/blueprints/engineering/` - workflow, engineering, and testing strategy
			- `/blueprints/engineering/dev_workflow.md` - Engineering workflow
			- `/blueprints/engineering/testing_strategy.md` - Testing strategy
		- `/blueprints/planning/` - Development Goals
			- `blueprints/planning/roadmap.md` - Phases and goals
    - `/runtime/` - files that are updated at runtime
		- `/runtime/active_sprint.md` — Active Sprint
		- `/runtime/backlog.md` — Backlog, Bugs, Issues...
		- `/runtime/milestones.md` — Live Milestones
		- `/runtime/openspec/` — OpenSpecs plans and archives
	    - `/runtime/resolved_bugs.md` — Resolved bugs log
	    - `/runtime/archive/` — Archived (Completed features and OpenSpecs)
	- `/context_map.json` - Context Protocol map
# Roles
You must **IDENTIFY** your role:
- Main Agent: 
	- You are Executive-Architect
	- ONLY report, communicate, resolve conflicts 
- Sub Agent: 
	- You are the Executive workers.
	- Make plans, write code, review code

# Core Disciplines
## Knowledge
- **SSoT**: [Project Registry](link to design docs) is the single source of truth.
- **Workflow**: OpenSpec driven → proposal + test-plan + tasks → review → code.
- **Model selection**: Use Opus for complex multi-file work; Sonnet for simple tasks.
- **Main agent role**: Communication, reporting, conflict resolution only — all code writing/review delegated to subagents.
- **CLAUDE.md**: Listed in `.gitignore`; never part of the repo.
## DOs
- **Require test design** before any implementation.
- **Pass lint and tests** before opening a PR.
- **Use feature branches** with PR + squash merge for every feature.
- **Run parallel branches** for non-conflicting tasks.
- **Follow Conventional Commits** for all commit messages.
- **Archive OpenSpec** → update Obsidian progress → record lessons on completion.
- **Prefer multi-agent review** for code review.
- **Check PR comments** before merging any PR.
- **Run new code review** after any parallel/subagent code modification.
- **Wait for all parallel OpenSpecs** to complete → single agent reviews all.
- **Perform manual testing** at the end of each task.
## DON'Ts
- **Never push to main** directly.
- **Never use `git checkout`**.
- **Never use `git clean`**.
- **Never mention AI/assistant/generated/Co-Authored-By** in commits.
- **Never push CLAUDE.md** to the repo.
- **Never write or review code** from the main agent — delegate to subagents.


## End-to-End Feature Workflow

### Phase 1: Create Feature Implementation Plan
1. Create `openspec/changes/YYYY-MM-DD-<feature>/`
2. Parallel ``subagents write `proposal.md`, `test-plan.md`, `tasks.md`
3. Wait ALL complete → single Opus agent reviews ALL OpenSpecs
4. Fix review issues

### Phase 2: Feature Implementation
1. `git checkout -b feat/<name> main`
2. Split task into non-conflicting file sets. Per set, spawn `team-lead` agent:
   `git worktree add ../wt-<n> feat/<name> && cd ../wt-<n> && <implement>`
3. `team-lead` distribute task to spawn `worker` agents (agent teams), each task can be the size of at most a file or at least a function
4. Merge worktrees back:
   `git worktree list --porcelain | ...` → commit per worktree → `git merge --no-ff`
5. `npm run lint && npm test` — exit on any non-zero code. Do not proceed.
6. Spawn Opus subagent: review full diff (`git diff main...feat/<name>`). Output: approve | request-changes.
7. If request-changes: fix all issues, repeat from step 4.

### Phase 3: Feature PR & Merge 
1. `git commit -m "<type>(<scope>): <desc>"` — no AI/generated mentions in msg.
2. `git push origin feat/<name>`
3. `gh pr create --fill --base main`
4. `gh pr checks <pr> --watch && gh pr reviews <pr>` — poll until all bot reviews resolve. Parse comments.
5. If comments exist: fix → `git commit --amend`/new commit → `git push --force-with-lease`. Repeat from step 4.
6. `gh pr merge --squash --delete-branch --auto`
## Phase 4: wrap-up 
1. Archive OpenSpec: `mv openspec/changes/<feature> openspec/changes/archive/`
2. Update `runtime/tracking/backlog.md` (stats, phase status)s
3. Update `runtime/milestones.md` (stats, phase stats)
4. Update Obsidian `runtime/tracking/active_sprint.md` ()
5. Clean up worktree & merged branches
