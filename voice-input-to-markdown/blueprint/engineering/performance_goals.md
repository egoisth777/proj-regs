# Performance Goals

Performance targets for the MAS Harness system.

> **Status:** Performance goals will be defined as the executable layer (M1/M2) is built. The protocol layer (current) has no runtime performance characteristics to measure.

## Planned Metrics (M2+)

- **Hook execution time:** < 5s for path validation and spec cascade checks
- **Context injection latency:** < 2s for resolving `context_map.json` and assembling subagent context
- **Post-PR-wait polling interval:** 30s between GitHub API checks
- **OpenSpec archival:** < 3s for moving completed feature to archive and updating index
