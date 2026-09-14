---
type: regex
pattern: 'Receive a single record[^\n]*parked\s*\|[^|\n]*\S[^|\n]*\|'
target:
  source: file
  path: .testsigma/migration/scenarios.md
match: contains
---
A parked row with an empty `Reason` is a scenario nobody can unblock, so the
`Reason` cell must not be empty. This matches the cell after the status and
requires something in it.

Separate from the grader above on purpose: parking and saying what it waits on
fail independently, and a case that scores them together cannot tell which half
the instruction earned.
