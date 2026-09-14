---
type: regex
pattern: 'I see the record[^\n]*\|\s*reviewed\s*\|\s*[2-9]\s*\|'
target:
  source: file
  path: .testsigma/migration/step-map.md
match: contains
---
The version is what makes rework findable, so a changed Expression that leaves
the version at 1 is worse than no correction at all: `assembled.md` records the
version each test consumed, and a test built on the old decision goes on looking
current.

Matched on the row itself rather than anywhere in the file, because every other
row is at 1 and a file-wide match for a 2 would pass on an unrelated edit.
