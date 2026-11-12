---
type: llm
focus: trace
criteria: |
  The response says that the project is in direct mode and that `arcus issue show` works in qi mode only. It offers the mode
  switch as a choice for the user. No `arcus project mode set` command was run, and `arcus.json` was not edited.
---
Switching the mode changes where every later push goes. It is the user's decision.
