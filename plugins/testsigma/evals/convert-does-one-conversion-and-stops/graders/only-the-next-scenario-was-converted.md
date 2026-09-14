---
type: regex
pattern: '(receive-several-records|print-a-receiving-label|two-records-appear|a-record-appears-after-processing)'
target: files
match: not_contains
---
The stop, checked deterministically and by name.

Five scenarios are pending and nothing in the prompt says how many to do. A
capable model reads that as a suite to migrate and works down the queue until it
runs out of turns, which is the behaviour ADR-0012 exists to replace: a run that
converts twenty scenarios on one set of unreviewed rows multiplies a wrong row
twenty times before anybody sees a test.

This matches the names of files the agent created, so a second test written for
any of the other four pending scenarios fails it. It cannot see a second
Conversion that wrote nothing, which is why the judged grader beside it reads the
report as well.

It asserts the choice as well as the stop, and that is deliberate: the queue
names which scenario comes next by a script rather than by taste, so a run that
delivers one test for a scenario of its own choosing has not obeyed the ordering
even though it stopped. The two fail together here because a run that ignores
the queue has no reason to stop at one either.

Its reach is the filenames a run chose, so a second test named in some other
style than the scenario it came from would slip past. The judged grader beside
it counts files rather than reading names, which is what closes that.
