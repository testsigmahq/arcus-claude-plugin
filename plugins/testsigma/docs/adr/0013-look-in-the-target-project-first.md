# Look in the target project first, and let the source win

Element Resolution consults three places. They are consulted in one order — the
**target project, then the source, then Operator capture** — and where the
project and the source both hold an element under one name, the **source's
locator is what gets written**. Looking first and winning are two different
rules, and neither implies the other.

Operator capture stays the last resort in both readings, and that is the only
part of the ordering the glossary states.

## Considered Options

The obvious order is the source first: it is where the element came from, it
costs nothing to read, and it answers most elements outright for any source that
carries locators. That is what `CONTEXT.md` said, and what issue 20 restated.

It was rejected because the two cases fail differently and the failure is
invisible. Where the source carries locators it answers every single time, so a
project consulted second is a project never consulted. The Operator maintains
those screens; a Migration that does not look hands back a project with two of
everything and no way to tell which is live. Nothing downstream catches that —
both elements resolve, every check passes, and the duplication is found by a
person months later.

Reversing the rule the other way — letting the project's locator win where the
names collide — was also rejected. The source is the record of what the test
actually drove, and a converted test pointed at a control the source never used
is wrong in the way that survives review: it runs, it passes, and it tests
something else.

A third option was to keep one ordering statement and accept that it is
approximate. Rejected: it had already produced a glossary entry, a reference and
an issue that disagreed, and a skill could not state "the order" without
silently picking one of them.

## Consequences

**The glossary stops ordering the first two places.** `CONTEXT.md` names the
three places and says only that Operator capture is the last resort. Which of
the other two is consulted first, and which wins where they disagree, belong to
`references/element-resolution.md`, which owns the procedure. The glossary is a
glossary, and an entry that duplicates a procedure is an entry that contradicts
it later.

**A skill states only what it owns.** `convert` says the target project is
consulted before the Operator is asked for anything, because parking on an
element is the Conversion's own decision. It does not restate the lookup order.

**The listing costs one call against an empty project.** Where the Operator
maintains no inventory, looking first answers nothing. That is the price of
noticing a duplicate in the case where there is one to notice, and it is paid
once per Conversion rather than per element.

ADR-0012 is unaffected: this fixes how the three places are ordered inside a
Conversion, not that resolution happens inside one.
