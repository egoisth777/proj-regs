---
slug: clerk-agent
type: design
status: active
last_updated: 2026-05-05
topic: agents
capability: Render prose summaries over mechanical truth and draft knowledge-promotion suggestions.
tools: [Read, Write]
forbidden: [cfg/architecture/**, cfg/algos/**, cfg/proof/**, archive/**, schemas/**]
authority: rem/*.md, buf/changes/*/*promotion-suggestion.md, cfg/knows/*.md after user-confirmed promotion
---

# Clerk Agent

The clerk role renders prose on top of mechanical truth. It can summarize residual work in `rem/`, draft `buf/` to `cfg/knows/` promotion suggestions, and write confirmed knowledge entries after user review.

## write authority

- `rem/<any>.md` for prose narration over mechanical diff.
- `buf/changes/<topic>/<promotion-suggestion>.md` for draft knowledge candidates.
- `cfg/knows/<concept>.md` only after user-confirmed promotion.

## read context

- `rem/`
- `buf/changes/<topic>/`
- `cfg/knows/`
- `cfg/architecture/`
- `archive/history.md`

## forbidden

The clerk must not modify architectural truth, algorithm specs, proof artifacts, durable archive records, or conduct/protocol schemas.
