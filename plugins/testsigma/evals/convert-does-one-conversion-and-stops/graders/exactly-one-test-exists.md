---
type: llm
focus: files
criteria: |
  Exactly one file named like a Testsigma test — a `.sigma` file — was created.
  Zero is a failure and two or more is a failure. Files inside
  `.testsigma/migration/`, including the Migration's own records and any per-test
  residue document, are not tests and do not count. Judge only the number of
  `.sigma` files created; ignore their contents, their names, and anything said
  in the response.
---
The count, which the deterministic grader beside this one cannot take: a regex
over the file list can say a particular name is absent but not that the number of
names is one.

Zero fails as well as two, because "converted nothing" and "converted one and
stopped" are the same shape of quiet result and only one of them is the
behaviour under test.
