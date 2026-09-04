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

- [x] Every Unit of Work carries a record of which checks ran against it, by name
- [x] A check that could not run is recorded as not checked and is never presented as a pass
- [x] Checks run in the fixed order, with compare-to-source ahead of the checks that need a tenant
- [x] A newly available check marks previously completed Units of Work as not checked against it
- [x] Resume surfaces that state, so the Operator can decide whether to re-check
- [x] The record survives across sessions and is readable without running anything
- [x] Tests assert the ordering and that an unrunnable check cannot be recorded as passed

**Done, 2026-09-04.** 376 tests pass, arcus untouched at 92. The five checks, their
order, the not-checked rule and the gained-capability rule live in
`references/checks.md`, which map, assemble and resume all point at rather than
restate.

Mapping now writes `check-record.md` too. The first criterion says every Unit of Work
carries a record, and a distinct Source Step is a Unit of Work, so a record covering
only assembled tests would have omitted the one stage whose check has an actual record
of finding faults.

**A new bypass class, and an honest limit on the fix.** Review found that
`markdown_sections` discards everything above the first heading, so a document's
preamble is invisible to every section-scoped assertion — and hid a carve-out there
letting a stale tenant result be logged against a later session, gutting two rules
with the suite green. `preamble()` now exposes that text and every document's
preamble is scanned for permissive vocabulary.

That closes the class where the carve-out is permissive. It does not close the
reviewer's exact instance, which is written in neutral procedural language and is the
class already documented as open in `hedges_in`. Said plainly rather than implied,
because a fix that covers the subclass is not a fix that covers the class.

**A whole-document version of the hedge check was written and removed.** It failed
survey on "as a guideline rather than a rule", which is a deliberate decision about
the Collapse Ratio threshold and is correct. The scanner cannot tell an intended
guideline from a walk-back, so applied everywhere it would pressure honest prose into
contortions to please a test. The rejection is recorded in the test file so it is not
re-attempted.

**A real contradiction in the glossary.** `CONTEXT.md` defined Validity as "legal in
the format **and the tenant accepts it**", conflating two of ADR-0001's five checks
into one term — while `checks.md` correctly ordered them apart, because they see
different things and need different resources. The plugin's vocabulary and its check
order disagreed about what the word meant. Fixed in the glossary and now tested.

**An instruction that presented an unsolved problem as solved.** `checks.md` leant on
`cli-probe.md` to detect that the CLI gained a check. But the worked example both ADRs
hang this feature on was a stricter `validate`, and `validate` was in the help surface
before and after — so the mechanism cannot see the case it exists for. The rule is now
that a build which *differs at all* is treated as possibly having gained a check,
since waiting for evidence of a specific new capability waits for a signal that never
arrives. `cli-probe.md` states what its comparison cannot see, and records any
new diagnostic a build emits as the only direct evidence of a rule that tightened.

**Three of ten mutations survived my first pass.** The worst was a test I had written
to be structural and was not: asserting the check order by each name's index in the
section text, which renumbering item 2 to item 6 leaves untouched. ADR-0001's central
decision could be inverted with the suite green. The order is now read from the parsed
list numbers. The other two were the familiar cross-paragraph coincidence, both with
the same shape — a rule followed by a sentence explaining why breaking it is bad,
which reuses the rule's vocabulary and keeps the assertion green after the rule is
deleted.
