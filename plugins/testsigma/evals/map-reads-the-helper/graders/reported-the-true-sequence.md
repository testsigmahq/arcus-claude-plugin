---
type: llm
focus: trace
criteria: |
  Taking the Step Map row the agent wrote together with anything it reported,
  the step is described as a sequence of more than one action. It must account
  for at least the conditional expand of the hidden field and the Enter
  keypress, and must not present the step as only typing or entering the record.
  Judge only what the step is said to do; ignore formatting, the choice of
  Testsigma verbs, and anything about other steps. The prompt did not ask what
  the step does, so silence about the real sequence counts as failing.
---
Deliberately narrow. A broad criterion here becomes a coin flip, and this is one
of only three model-judged graders in the suite.

Narrowed to: whether the helper's real sequence was reported rather than the source line's implication.

`focus: trace` because the criterion judges the row the agent *wrote*, and the
default `last_message` shows the judge only the final reply. A criterion that
names an artifact the judge cannot see is not a strict grader; it is one that
fails whenever the agent chose to summarise rather than restate.
