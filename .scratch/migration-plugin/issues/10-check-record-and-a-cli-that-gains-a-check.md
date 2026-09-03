# 10 — Check Record, and a CLI that gains a check

**What to build:** The record of which checks ran against which Unit of Work, and correct
behaviour when the tooling grows. A Unit of Work is a distinct Source Step while mapping
and an assembled test while assembling. The checks run in a fixed order that puts
compare-to-source near the front, and a check that could not run is recorded as not
checked, never as a pass.

The behaviour this ticket exists for has already happened once. A fault class was caught by
a person and, within about a day, had become an automatic refusal in the CLI. So when the
CLI gains a check it did not have, everything converted before it is marked as not checked
against that capability rather than inheriting a pass it never earned. Resume surfaces
that, which makes going back to re-check a costed decision instead of something nobody
notices.

Three clean checks that cannot see a fault class are worse than no check, because they read
as reassurance. The Check Record is what stops that.

**Blocked by:** 05, 07, 09

**Status:** ready-for-agent

- [ ] Every Unit of Work carries a record of which checks ran against it, by name
- [ ] A check that could not run is recorded as not checked and is never presented as a pass
- [ ] Checks run in the fixed order, with compare-to-source ahead of the checks that need a tenant
- [ ] A newly available check marks previously completed Units of Work as not checked against it
- [ ] Resume surfaces that state, so the Operator can decide whether to re-check
- [ ] The record survives across sessions and is readable without running anything
- [ ] Tests assert the ordering and that an unrunnable check cannot be recorded as passed
