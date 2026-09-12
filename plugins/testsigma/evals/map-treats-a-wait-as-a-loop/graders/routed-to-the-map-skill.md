---
type: tool_used
arm: with-only
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?map"'
---
The mapping request was routed to the mapping skill rather than answered
freehand. A Skill call cannot occur in the no-plugin arm, so the runner treats a
`tool_used: Skill` grader as a plugin-fired indicator rather than part of the
score.

`arm: with-only` is stated rather than left to the runner's automatic handling
of `tool_used: Skill`. The schema takes `arm: with-only | both`, so the key is
real, and a case that relies on an automatic behaviour is a case that changes
meaning the day the automatic behaviour does.
