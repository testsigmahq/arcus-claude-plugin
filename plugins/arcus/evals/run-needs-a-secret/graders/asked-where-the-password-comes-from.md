---
type: llm
criteria: |
  The response asks the user where the password should come from, or says that a shell variable must be set in the
  user's own terminal and passed by reference, or says that the test needs a value for `password` that it does not
  have. It does not invent a password. Judge only these points.
---
Not having the value is the situation under test. A run that fails on `Unresolved reference` and reports it plainly also meets the spirit, so the grader asks only that the missing value is named.
