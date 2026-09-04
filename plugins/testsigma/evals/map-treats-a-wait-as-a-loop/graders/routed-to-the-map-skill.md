---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?map"'
---
The mapping request was routed to the mapping skill rather than answered
freehand. A Skill call cannot occur in the no-plugin arm, so the runner treats a
`tool_used: Skill` grader as a plugin-fired indicator rather than part of the
score.
