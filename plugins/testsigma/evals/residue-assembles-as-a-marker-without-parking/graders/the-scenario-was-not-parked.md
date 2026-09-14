---
type: regex
pattern: 'Print a receiving label[^\n]*\|\s*done\s*\|'
target:
  source: file
  path: .testsigma/migration/scenarios.md
match: contains
---
Residue waits on nobody, because somebody has already ruled. Parking waits on the
Operator and names what for. A Conversion parked on a step that was declined
weeks ago puts a question in front of the Operator that nobody can answer, and
the scenario sits in the queue until someone reads the Residue entry and works
out that the park was a mistake.

Stated positively — the scenario finishes `done` — rather than as "not parked".
A grader that only forbids `parked` passes every run that never opened the queue
at all, which is what a run without the plugin does, so it would have scored
identically in both arms and measured nothing.

The two outcomes are told apart by who is owed something, which is exactly the
distinction a model without the plugin has no reason to draw.
