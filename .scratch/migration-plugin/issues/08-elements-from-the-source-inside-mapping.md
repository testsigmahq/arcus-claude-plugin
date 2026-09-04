# 08 — Elements from the source, inside mapping

**What to build:** For a source that carries locators, satisfying the element names a Step
Map references happens in the same reading that recovers sequence. The same files hold
both, so they are opened once and asked both questions together.

This is not an optimisation. On the first conversion all forty-six locators came out of the
Java page objects, and those same files were the ones that had to be opened for sequence.
They were opened for locators, the question of what the code actually did was never asked,
and that is how four of the six faults got through. Separating the two readings is the bug.

Where the source cannot supply an element, existing Testsigma screens and elements are
reused by name so a Migration does not duplicate screens the Operator already maintains.
Operator capture is the last resort, not the first. An element that nothing resolves blocks
assembly of every test referencing it, rather than producing a test that looks finished and
cannot run.

**Blocked by:** 07

**Status:** ready-for-agent

- [x] Locators are taken from the source's own layer in the same pass that reads sequence, not in a separate pass
- [x] Existing screens and elements are matched and reused by name before anything new is created
- [x] The Operator is asked to capture an element only when neither the source nor the existing project can supply it
- [x] An unresolved element becomes Residue with that specific cause, distinct from an unexpressible step
- [x] A test referencing an unresolved element is blocked rather than assembled with a placeholder
- [x] Tests assert that the mapping skill requires locator reading and sequence reading to happen together

**Done, 2026-09-04.** 269 tests pass. The locator question is asked inside Step 3, in
the same reading that recovers sequence, because separating the two readings is the
fault rather than an inefficiency. Step 4 is disposition — which of three places
supplies the element, and what happens when none does — and it reuses what Step 3
lifted rather than reopening anything. Review confirmed the two readings are not
re-separated.

The three places are bold-led items in order, so the ordering is a property of the
document structure rather than of its phrasing.

**Review found a real design defect, not a wording problem.** The blocking rule was
stated absolutely — an unresolved element blocks assembly of every test referencing
it — and `residue.md` was keyed by Source Step alone. One generic step can carry far
more parameter values than rows, so the only way to record a single unresolved
element was to mark the whole row, blocking every occurrence that had resolved
perfectly well. The rule had no data model able to express it, and ticket 9 would
have had nothing to enforce at the right granularity. `residue.md` is now keyed by
Source Step and element, the element column carries the parameter value that
identifies it, and an unexpressible step leaves it empty. Assembly reads that column.

**A format-specific measurement had leaked into the generic skill.** The 108
control-and-screen pairs are a Cucumber measurement, and the adapter is the only part
of a Migration that knows the format. Two copies with nothing comparing them is drift
waiting to happen; the skill now points at the adapter's own Locators section. A test
fails the skill if the figure reappears in it.

**The frontmatter promised element resolution unconditionally** while the body
correctly gated itself on `carries-locators`. The description is always in context, so
that inconsistency was the more visible half. Fixed.

Ticket 11's seam is clean: the conditional means a Tosca adapter with
`carries-locators: no` gets its own resolve-elements skill without editing this one.

**Four surviving mutations, three of them cross-paragraph coincidence.** The worst
demoted the source from the first place tried to "one option among three" and passed,
because an unrelated sentence three paragraphs down says "their time is the last
resort and not the first" and mentions the source. Two unrelated words satisfied a
test about ordering. Fixed with `_bold_leads`, which asserts the order structurally —
the first genuinely structural assertion in this suite rather than a better-scoped
string search.

The fourth was a neutral-language walk-back — capture first where it would be quicker
than searching the project. Second demonstration of the class documented in
`hedges_in`, not materially different from the first, and no word list added.
