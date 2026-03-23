# {Project Name} - Project Memory

## Context Protocol
- This Registry acts as the Single Source of Truth (SSoT) for the external Project codebase. 
- ONLY Agent type of `architect / auditor` reads and modify `runtime` updates  
- To avoid polluting LLM context, agents must use `context_map.json` to link specific files or directories in the project repository to their corresponding design documents in this registry.

## SSoT Routing (Obsidian Vault)

### 🏛️ The Static Blueprint (Immutable during execution)
*These folders dictate HOW the system works and WHAT it is supposed to be. Agents treat these as read-only laws of physics during sprints.*
- **Architecture design**: [`blueprint/design/architecture_overview.md`](/Mounted/Project-Registries/Registry-Template/Template/blueprint/design/architecture_overview.md)
- **Design principles**: [`blueprint/design/design_principles.md`](/Mounted/Project-Registries/Registry-Template/Template/blueprint/design/design_principles.md)
- **API mapping**: [`blueprint/design/api_mapping.md`](blueprint/design/api_mapping.md)
- **Engineering workflow**: [`blueprint/engineering/dev_workflow.md`](/Mounted/Project-Registries/Registry-Template/Template/blueprint/engineering/dev_workflow.md)
- **Testing strategy**: [`blueprint/engineering/testing_strategy.md`](/Mounted/Project-Registries/Registry-Template/Template/blueprint/engineering/testing_strategy.md)
- **Context Protocol map**: [`context_map.json`](/Mounted/Project-Registries/Registry-Template/Template/context_map.json)
- **Phase roadmap**: [`blueprint/planning/roadmap.md`](/Mounted/Project-Registries/Registry-Template/Template/blueprint/planning/roadmap.md)

### ⚡ The Dynamic State (Constantly updating runtime)
*These folders track live execution, historical logs, bugs, and active context. Agents actively read and write here to sync progress.*
- **Active Sprint & OpenSpecs**: [`runtime/tracking/active_sprint.md`](/Mounted/Project-Registries/Registry-Template/Template/runtime/active_sprint.md), [`runtime/openspec/`](runtime/openspec/)
- **Backlog & Future Ideas**: [`runtime/tracking/backlog.md`](/Mounted/Project-Registries/Registry-Template/Template/runtime/backlog.md)
- **Live Milestones**: [`runtime/tracking/milestones.md`](/Mounted/Project-Registries/Registry-Template/Template/runtime/milestones.md)
- **Implementation Records (IRs)**: [`runtime/implementation/`](runtime/implementation/) -> Indexed in [`runtime/implementation/IR_INDEX.md`](/Mounted/Project-Registries/Registry-Template/Template/IR_INDEX.md)
- **Resolved bugs log**: [`runtime/testing/resolved_bugs.md`](runtime/testing/resolved_bugs.md)
- **Research (Scratchpad)**: [`runtime/research/`](runtime/research/)
- **Archive (Historical Memory)**: [`runtime/archive/index.md`](runtime/archive/index.md)





