---
type: llm
focus: trace
criteria: |
  Taking the Step Map row the agent wrote together with anything it reported,
  the step is expressed as repeating an action until a condition holds, with
  each pass re-driving the interface by retyping the filter and clicking
  refresh. Presenting it as a passive wait, a sleep, a timeout, or waiting for
  an element to appear without acting fails. Judge only what the step is said to
  do; ignore formatting and the choice of Testsigma verbs.
---
Measurement on a real suite found this shape 50 times against 8 of the obvious
`click refresh until` spelling, so the volume is in exactly the shape that reads
as an assertion.

Narrowed to: whether a helper named like a wait was reported as a loop that re-drives the interface.

`focus: trace` because the criterion judges the row the agent *wrote*, and the
default `last_message` shows the judge only the final reply. A criterion that
names an artifact the judge cannot see is not a strict grader; it is one that
fails whenever the agent chose to summarise rather than restate.
