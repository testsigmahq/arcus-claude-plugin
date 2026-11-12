---
type: llm
criteria: |
  The response says the test failed on the title check, says the page's title is "Welcome" while the test expects
  "Welcome back", and says who owns the difference: it either asks which side is right (the test or the page), or
  names the test or the app as the cause with the evidence. It fails if it only repeats the engine's message, or
  if it claims the test now passes. Judge only these points.
---
The skill's rule: name the owner, with the evidence, and ask when the evidence does not decide. Here it does not decide: the page is the app, and nothing says which text is right.
