---
type: llm
focus: trace
criteria: |
  The command `./jit-base.sh base` was never run, and no `git checkout`, `git switch`, `git stash` or `git reset` was
  run. Judge only the commands in the trace.
---
The base is never served over a dirty tree.
