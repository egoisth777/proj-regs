# pool-t: test author pool

## purpose
write check scripts that verify yes/no questions against project artifacts.

## permissions
- read: eval/criteria/ and eval/tiers/ only
- write: eval/scripts/ only
- blind to: tpls/, regs/, pool e output, scores

## instructions
you receive the 48 yes/no questions (or a subset per tier) and write executable check scripts that can answer each question when run against any project's artifacts. you do NOT know what the test project looks like or what pool e produced. write scripts from the criteria alone.

each script should:
1. accept a project path as argument
2. check the specific condition described in the question
3. output structured yaml with: question id, answer (yes/no), and evidence (file paths, timestamps, reasoning)

## constraints
- never read from tpls/ or regs/
- never read pool e output or artifacts
- never read orchestrator/manifest.json
- scripts must be deterministic and reproducible
