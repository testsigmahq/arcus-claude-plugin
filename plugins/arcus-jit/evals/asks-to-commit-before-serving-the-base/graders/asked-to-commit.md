---
type: llm
criteria: |
  The response says there are uncommitted changes (it may name `src/search.ts`) and asks the user to commit them before
  the check goes on. It fails if it says the check ran, or if it offers to stash, reset or discard the changes itself.
---
Serving the merge base checks out another commit; uncommitted work would be tested on both sides or lost.
