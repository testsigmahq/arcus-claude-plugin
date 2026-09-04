---
type: llm
criteria: |
  Taking the Step Map row the agent wrote together with anything it reported,
  the step is said to send text only, without submitting or confirming the
  reason code. Saying the submit control exists but is never clicked counts.
  Presenting the step as committing, saving, applying or submitting a choice
  fails, and so does an expression that adds a submit or confirm action the
  source never performs. Judge only what the step is said to do; ignore
  formatting and the choice of Testsigma verbs.
focus: whether the helper was reported as doing less than its line implies
---
The inverse of the does-more fault, and the one that invents a step the source
never performed.
