# Behavior Spec: manual/ Documentation

### Behavior: Documentation index exists

**Given** a user navigating to the manual/ directory
**When** they open README.md
**Then** they see a system overview and table of contents linking to all documentation files

### Behavior: All subsystems documented

**Given** the omni system's major subsystems (registries, templates, eval, evolution loop, orchestrator, agents, spec cascade)
**When** a user reads the corresponding documentation file
**Then** each file accurately describes the subsystem's purpose, structure, and usage

### Behavior: Cross-references are valid

**Given** documentation files reference other manual pages
**When** a user follows a relative link
**Then** the link resolves to the correct documentation file
