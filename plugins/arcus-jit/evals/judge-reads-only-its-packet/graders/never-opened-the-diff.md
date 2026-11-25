---
type: llm
focus: trace
criteria: |
  No tool call in the trace read, listed or searched `change.diff` (no Read of it, no `cat`, `grep` or `git diff`). Judge
  only the tool calls in the trace.
---
The judge's evidence is its packet. Reading the diff would let the author's intent steer the verdict.
