---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?assemble"'
---
The request was routed to the assembly skill rather than answered freehand. A
plugin-fired indicator rather than part of the score, since a Skill call cannot
occur in the no-plugin arm and scoring it would guarantee a delta that measures
nothing about the instructions.
