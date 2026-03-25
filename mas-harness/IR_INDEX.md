# Implementation Decision Records (IR) Index

This document indexes all `IR-xxx` records within the project. It serves as a single lookup table for agents to understand complex implementation details without scanning the entire `implementation/` directory.

| IR Code  | Short Description | Corresponds To (File/Module) | Date Added |
| :------- | :---------------- | :--------------------------- | :--------- |
|          |                   |                              |            |

## How to use this index

1. **Recorder Agent:** When generating an `IR-xxx.md` file due to a `COMPLEXITY: HIGH` tag in a PR, append a new row to this table.
2. **Executor/Reviewer Agents:** Before modifying complex code marked with `// [IR-xxx]`, look up the IR code here and read the corresponding `runtime/implementation/IR-xxx.md` file to understand the underlying architecture and constraints.
