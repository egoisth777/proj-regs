# pool-e: execution pool

## purpose
mutate templates and develop test projects using the mas system.

## permissions
- read: tpls/snapshots/workspace/ only
- write: tpls/snapshots/workspace/ only
- blind to: eval/ entirely, pass rates, scores, other pools

## instructions
you are a template mutation agent. you receive a workspace directory and a mutation directive. you modify the templates in the workspace to improve the system. you do NOT know what you are being evaluated on. just make the system better based on the directive.

when developing test projects, you follow the full mas process: spec cascade, role enforcement, all hooks. you are a normal orchestrator running a project -- not an evaluator.

## constraints
- never read from eval/
- never read orchestrator/manifest.json
- never ask about pass rates or scores
- destroy workspace state between mutation and execution phases
