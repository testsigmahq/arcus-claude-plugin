---
type: llm
criteria: |
  The response says the check cannot run because the repo has no base recipe: no `arcus-jit.json`, or no command that
  serves the merge base. It may say what the file needs. It fails if it claims to have compared the change with a base,
  or offers to use a deployed environment as the base instead.
---
Without a way to serve the merge base on the same stack, any comparison would be against a different build.
