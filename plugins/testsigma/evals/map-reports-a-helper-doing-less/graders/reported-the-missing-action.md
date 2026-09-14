---
type: llm
focus: trace
criteria: |
  Taking the Step Map row the agent wrote together with anything it reported,
  the step is said to send text only, without submitting or confirming the
  reason code. Saying the submit control exists but is never clicked counts.
  Presenting the step as committing, saving, applying or submitting a choice
  fails, and so does an expression that adds a submit or confirm action the
  source never performs. Judge only what the step is said to do; ignore
  formatting and the choice of Testsigma verbs.
---
The inverse of the does-more fault, and the one that invents a step the source
never performed.

Narrowed to: whether the helper was reported as doing less than its line implies.

`focus: trace` because the criterion judges the row the agent *wrote*, and the
default `last_message` shows the judge only the final reply. A criterion that
names an artifact the judge cannot see is not a strict grader; it is one that
fails whenever the agent chose to summarise rather than restate.

What the no-plugin arm does instead: it writes the action the step line names —
selecting and committing a reason code — because nothing in the phrasing
suggests the helper stops short. A model has no reason to suspect a step of
doing less than it says.
