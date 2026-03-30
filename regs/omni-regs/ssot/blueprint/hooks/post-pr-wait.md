---
name: post-pr-wait
type: hook
status: protocol-instruction
planned_executable: M1
description: After local PR creation, polls remote GitHub PR until all CI checks and reviews complete.
---

# Hook: post-pr-wait

> **Current status:** Protocol instruction (agents follow this manually). Will be implemented as an executable Claude Code hook in `settings.json` during M1.

## Trigger
After local PR is created (`gh pr create`).

## Behavior
1. Poll remote GitHub PR status using `gh pr checks <pr-number>`
2. Wait for all CI checks to complete (status: pass or fail)
3. Wait for review bot feedback to arrive
4. Collect all review comments using `gh api repos/{owner}/{repo}/pulls/{pr}/comments`
5. Return collected feedback to the calling agent
6. The calling agent addresses all review issues before proceeding

## Blocking
The agent is **blocked** until all remote feedback is collected. This prevents premature merges and ensures all review comments are addressed.

## Error Handling
- If CI fails: return failure report immediately (do not wait for reviews)
- If polling exceeds 30 minutes: alert the Orchestrator for human escalation
