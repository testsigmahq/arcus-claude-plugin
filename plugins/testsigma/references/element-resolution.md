# Resolving an element

Satisfying the element names a Step Map row references. The same procedure runs in
two places: inside mapping where the source carries locators, and as a Phase of
its own after mapping where it does not. Whether it is a Phase is a property of
the source, not of the Migration — the adapter's `carries-locators` decides, and
the skill that calls this says which case it is in.

Try three places, in this order, and stop at the first that answers:

**The source, first.** What you lifted in Step 3 resolves most elements without
anyone being asked anything. This is the whole reason the two questions share one
reading.

**The existing Testsigma project, by name.** Before creating any screen or
element, look for one already there whose name matches, and reuse it. The
Operator maintains those screens, and a Migration that duplicates them hands back
a project with two of everything and no way to tell which is live.

**Operator capture, last resort.** Ask only when neither the source nor the
existing project can supply the element. Their time is the last resort and not
the first: a capture asked for unnecessarily is time spent on what the code
already described.

When nothing resolves an element, record it in `residue.md` as an unresolved
element. That cause is distinct from an unexpressible step and the two are never
merged: one means the format has no spelling, the other that the thing to act on
cannot be found.

An unresolved element blocks assembly of every test that references it. Never
substitute a placeholder and never assemble around it. A test that looks finished
and cannot run is worse than a test that is visibly absent, because the absent
one is on a list and the placeholder is in a suite.

Record the block at the element's granularity, not the row's: the Residue entry
names the parameter value identifying the element, so what is blocked is the
occurrences referencing it. A row whose other elements resolved is not blocked by
one that did not.

**Count elements, not steps.** A generic step taking a control and a screen as
parameters occupies one row and still names as many things to find as it has
parameter values, orders of magnitude more. Estimate from the distinct parameter
values; the adapter's Locators section carries a measured example.

## Naming, and the workspace's single namespace

Element references are unqualified, so a workspace has one namespace for every
element in it. Two classes in the source can each declare a field of the same name
with genuinely different locators, and a Migration can need both.

So check every new name against everything already in the workspace, and where it
collides, disambiguate by the owning source class rather than by a number: a
number records that there were two, and the class records which is which.
`authoring.md` carries the measured case.
