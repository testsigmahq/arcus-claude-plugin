---
type: llm
focus: trace
criteria: |
  `arcus status` was run, and the answer says the project works in direct mode with no call to a server. No `arcus pull`,
  `arcus push` or `arcus project mode set` command was run. Judge only the trace and the answer.
---
In a direct project `pull` is a qi command and stops with exit 3. A skill that runs it, or switches the mode to get a result, did not read the mode first.
