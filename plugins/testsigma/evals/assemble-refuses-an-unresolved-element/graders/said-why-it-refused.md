---
type: llm
criteria: |
  The response says it did not assemble the test, and gives the reason as an
  element that has not been resolved. It must not present the test as assembled,
  partially assembled, or assembled with a placeholder or a guessed locator.
  Naming the element or the screen is allowed. Judge only whether a refusal was
  reported and attributed to an unresolved element; ignore the wording, the
  formatting, and anything said about other scenarios or other steps.
focus: whether the refusal was stated and attributed, rather than the test being quietly skipped
---
A refusal nobody is told about is indistinguishable from work not attempted, so
the deterministic grader beside this one is not enough on its own: the absence
of a `.sigma` file is equally consistent with a correct refusal and with an
agent that simply ran out of turns. This grader is what tells the two apart.
