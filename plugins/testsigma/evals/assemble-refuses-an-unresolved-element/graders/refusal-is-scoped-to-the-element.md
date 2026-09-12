---
type: llm
arm: both
focus: trace
criteria: |
  The response names the specific unresolved element that blocks assembly —
  `journal-filter`, or the filter control it describes — rather than reporting
  only that the scenario cannot be assembled. Naming the Source Step it belongs
  to counts. It fails if the whole scenario or the whole feature is presented as
  unconvertible with no element identified, if a different cause is given
  (an unsupported step, a missing verb, an unclear requirement), or if the
  element is invented rather than taken from the Migration's own record.
  Judge only whether the block was attributed to a named element; ignore
  formatting, tone, and anything said about other scenarios.
---
Granularity is the plugin's claim here, and it is exactly what a general refusal
does not have.

The skill says a row whose other elements all resolved is not blocked, and that
the decision is made per element at the parameter value — which is what that
column in `residue.md` is for. A model refusing on its own produces "I can't
assemble this", which is true, useless for planning, and indistinguishable from
having run out of ideas. "`journal-filter` is unresolved, so this scenario is
blocked and these others are not" is a work item.

So this grader is not asking for a better-worded refusal. It is asking whether
the refusal carries the one fact that decides what happens next.
