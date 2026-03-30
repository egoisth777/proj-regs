# Implementation Decision Records (IR) Index

This document indexes all `IR-xxx` records within the project. It serves as a single lookup table for agents to understand complex implementation details without scanning the entire `implementation/` directory.

| IR Code  | Short Description                             | Corresponds To (File/Module) | Date Added |
| :------- | :-------------------------------------------- | :--------------------------- | :--------- |
| `IR-001` | *Example: Custom auth token validation logic* | `src/auth/validator.ts`      | 2024-05-20 |
|          |                                               |                              |            |

## How to use this index

1. **Recorder Agent:** When generating an `IR-xxx.md` file due to a `COMPLEXITY: HIGH` tag in a PR, append a new row to this table.
2. **Executor/Reviewer Agents:** Before modifying complex code marked with `// [IR-xxx]`, look up the IR code here and read the corresponding `implementation/IR-xxx.md` file to understand the underlying architecture and constraints. 
