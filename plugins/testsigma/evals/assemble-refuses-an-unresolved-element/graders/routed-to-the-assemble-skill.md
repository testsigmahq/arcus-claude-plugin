---
type: tool_used
arm: with-only
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?assemble"'
---
The request was routed to the assembly skill rather than answered freehand. A
plugin-fired indicator rather than part of the score, since a Skill call cannot
occur in the no-plugin arm and scoring it would guarantee a delta that measures
nothing about the instructions.

`arm: with-only` is stated rather than left to the runner's automatic handling
of `tool_used: Skill`. The schema takes `arm: with-only | both`, so the key is
real, and a case that relies on an automatic behaviour is a case that changes
meaning the day the automatic behaviour does.
