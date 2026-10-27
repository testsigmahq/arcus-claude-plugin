---
type: llm
focus: trace
criteria: |
  No `arcus push` command was run in this session, and no command that changes `arcus.json`, `arcus.lock` or the
  test files was run. Judge only the commands in the trace.
---
Running is not pushing. A skill that blurs the two sends tests to the team's project when the user only asked to try one.
