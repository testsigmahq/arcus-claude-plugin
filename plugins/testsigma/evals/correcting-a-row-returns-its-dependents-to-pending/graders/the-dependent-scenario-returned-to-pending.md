---
type: regex
pattern: 'Archive a record[^\n]*\|\s*pending\s*\|'
target:
  source: file
  path: .testsigma/migration/scenarios.md
match: contains
---
`Archive a record` is the one scenario already assembled from this row, and
`assembled.md` records the version it consumed. A corrected row that leaves it
`done` is a delivered test built on a decision the Migration has since reversed,
and nothing downstream can see the difference — the test agrees with the row it
was built from, and every later check compares against the current row.

This is the behaviour no document test can reach: finding the dependants means
joining two files by a spelling, and an agent that skips the join produces a
Migration that looks consistent and is not.
