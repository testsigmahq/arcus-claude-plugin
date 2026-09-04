---
type: llm
criteria: |
  Taking the Step Map row the agent wrote together with anything it reported,
  the step is described as a sequence of more than one action. It must account
  for at least the conditional expand of the hidden field and the Enter
  keypress, and must not present the step as only typing or entering the LPN.
  Judge only what the step is said to do; ignore formatting, the choice of
  Testsigma verbs, and anything about other steps. The prompt did not ask what
  the step does, so silence about the real sequence counts as failing.
focus: whether the helper's real sequence was reported rather than the source line's implication
---
Deliberately narrow. A broad criterion here becomes a coin flip, and this is one
of only three model-judged graders in the suite.
