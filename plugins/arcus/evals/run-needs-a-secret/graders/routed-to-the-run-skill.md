---
type: tool_used
arm: with-only
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?run"'
---
The request was routed to the `run` skill rather than answered freehand. A Skill call cannot happen in the no-plugin arm, so the runner treats this grader as a plugin-fired indicator and not part of the score.
