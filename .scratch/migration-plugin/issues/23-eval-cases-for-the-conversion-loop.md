# 23 — Eval cases for the Conversion loop

**What to build:** Measured evidence for the four behaviours only an agent can get
wrong and no document test can see.

That `convert` performs one Conversion and stops rather than looping on. That a
Conversion needing an Operator answer parks and the run ends cleanly rather than
stalling or guessing. That changing a row's Expression bumps its version and returns
the dependent scenarios to pending. That a Residue row assembles as a marker without
parking the Conversion that used it.

Fixtures extend the existing part-done Migration shape with the two new files rather
than introducing a new fixture family, so a case stays cheap to read against the
cases already there.

Every case must discriminate. Three cases on this branch have already been fixed for
scoring identically across arms, and a case that cannot distinguish the behaviour it
names is not a test — it is a cost with no signal.

**Blocked by:** 18, 19, 21.

**Status:** ready-for-agent

- [ ] A case measures that one invocation converts one scenario and stops
- [ ] A case measures that a Conversion needing the Operator parks and the run ends
      without stalling
- [ ] A case measures that a bumped row version returns dependent scenarios to pending
- [ ] A case measures that a Residue row assembles as a marker and does not park
- [ ] Fixtures extend the existing part-done Migration shape with `scenarios.md` and
      `assembled.md`
- [ ] Each case is shown to discriminate across arms rather than scoring flat
- [ ] The eval suite runs green
