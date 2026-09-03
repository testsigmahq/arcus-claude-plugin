# 07 — Map skill: the Step Map, compare-to-source, and Residue

**What to build:** The core of the whole plugin. Build the Step Map one distinct Source
Step at a time, and reuse each verdict everywhere that step occurs. A row carries the
source text, occurrence count, parameter shapes, the proposed expression, and a status, so
reviewing it does not mean going back to the source. One Source Step may map to several
Testsigma steps, because a source line that really does three things should not be forced
into one.

The part that earns this ticket its size is what makes a row finishable. The skill opens
the helper behind a source line and reads its sequence, and reports when that helper does
less than the line implies or more. It treats every wait, until, refresh and poll helper as
a loop until the source proves otherwise, because a helper that re-drives the interface
looks identical to a passive wait once flattened. It treats a wildcard or substring
comparison in the source as a question about what was being checked, not as licence to
write a weak comparison. A row cannot reach a finished state before that comparison has
happened.

Four of the six known faults were exactly this: a source line hiding a helper that did
something else. On the one occasion the comparison ran, it took about fifteen minutes and
found five of six. It is in this ticket rather than a later one because a check placed
after everything is a check that does not run.

Anything the format cannot express becomes Residue with a stated cause and the reasoning
that produced it, so a ruling can be overturned rather than hardening. One case already
believed unexpressible turned out to have a spelling nobody had found.

**Blocked by:** 03, 06

**Status:** ready-for-agent

- [ ] Distinct Source Steps extracted with occurrence counts, mapped once, verdict reused at every occurrence
- [ ] A row carries source text, occurrence count, parameter shapes, proposed expression and status
- [ ] One Source Step may map to several Testsigma steps
- [ ] The helper behind a source line is opened and its sequence reported, against the implementation rather than the surface syntax
- [ ] A helper doing less than its line implies is reported as such, and so is one doing more
- [ ] Every wait, until, refresh or poll helper is treated as a loop unless the source shows otherwise
- [ ] A wildcard or substring comparison in the source raises a question rather than authorising a weak comparison
- [ ] A row cannot be marked finished before the comparison has run
- [ ] Residue entries carry a cause and the reasoning behind it, and can be reopened
- [ ] Tests assert the skill's body requires opening the helper and requires the comparison before a row completes, and that no separate verification skill exists
