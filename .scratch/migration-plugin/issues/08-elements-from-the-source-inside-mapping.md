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

- [ ] Locators are taken from the source's own layer in the same pass that reads sequence, not in a separate pass
- [ ] Existing screens and elements are matched and reused by name before anything new is created
- [ ] The Operator is asked to capture an element only when neither the source nor the existing project can supply it
- [ ] An unresolved element becomes Residue with that specific cause, distinct from an unexpressible step
- [ ] A test referencing an unresolved element is blocked rather than assembled with a placeholder
- [ ] Tests assert that the mapping skill requires locator reading and sequence reading to happen together
