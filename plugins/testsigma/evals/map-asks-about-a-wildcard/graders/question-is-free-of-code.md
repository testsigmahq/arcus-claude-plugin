---
type: llm
criteria: |
  The question put to the Operator contains no source code, no method or class
  name, no file path or bare filename, no stack trace, and no diagnostic code.
  Naming a screen, a field, or a value the application shows is allowed and
  expected. Judge only the text of the question put to the Operator; ignore the
  rest of the response, including anything written into the Migration Directory,
  where these details belong.
focus: whether the question is answerable by someone with the application open and no code checked out
---
The admissibility test from references/asking.md, which is the one rule that
decides whether a question can be answered by the only person who can answer it.
