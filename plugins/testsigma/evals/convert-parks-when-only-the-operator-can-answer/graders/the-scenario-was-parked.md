---
type: regex
pattern: 'Receive a single record[^\n]*parked'
target:
  source: file
  path: .testsigma/migration/scenarios.md
match: contains
---
The park itself, in the record that holds the queue. No row in the fixture starts
`parked`, so this matches only if the agent set one.

It is a row rather than a sentence in the reply because the queue is what the
next session reads. A Conversion held up by a question the Operator never sees is
the failure parking exists to prevent, and a park announced only in a transcript
is that failure wearing the fix's clothes.
