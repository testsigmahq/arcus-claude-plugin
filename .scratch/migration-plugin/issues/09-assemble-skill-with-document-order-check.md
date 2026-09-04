# 09 — Assemble skill with the document-order check

**What to build:** Tests assembled from reviewed Step Map rows, and each finished test
checked for document order and block nesting before it is called done.

The order check is the one fault class a person caught by looking at the application: a
conditional whose body was numbered outside its own block, drawn empty and run late. The
property is arithmetic over the step tree. For every step with a parent, the child's order
lies strictly between its parent's order and the parent's next sibling's order, or beyond
it where there is no next sibling. The plugin computes this itself so it holds regardless
of what the installed CLI checks, which is the concrete case behind the decision to probe
rather than pin.

This check belongs to a whole test rather than a single step, because it describes a fault
that only exists between steps.

**Blocked by:** 07, 08

**Status:** ready-for-agent

- [x] Only reviewed Step Map rows can reach an assembled test
- [x] Every assembled test is checked for document order and block nesting before completion
- [x] The order property is computed by the plugin from the step tree, not delegated to the CLI
- [x] The check runs at the level of a whole test
- [x] A test that fails the check is reported with the specific steps that are out of place
- [x] A test referencing an unresolved element is refused
- [x] Tests assert the assembly skill requires the order check as its own exit condition

**Done, 2026-09-04.** 330 tests pass, arcus untouched at 92. This ticket produced the
plugin's first executable code, `scripts/check_step_order.py`, which is justified on
the same grounds as survey's enumeration script: the property is exact by
construction. Everything else a Migration does is judgement.

**The design premise was wrong on the first attempt, and real data caught it.** I read
the `[id = N]` annotation as the step's order. Run against the real ordering probe it
immediately reported exactly the fault that probe was built to demonstrate — a body at
1725 outside its parent's window of (1721, 1722) — which was extremely convincing. It
then reported nonsense on the converted tests, including "order 1604 must be after
177", which forced the check. Ids are assigned at creation, so a step edited in later
carries a higher id while sitting earlier: a real top-level step at 1718 precedes one
at 1604. By that same logic 1725 is high because the body was authored last.

So a `.sigma` working copy cannot carry this fault at all. Its parentage is the
lexical nesting and its document order the lexical sequence, both correct by
construction. The fault lives in the order numbers the platform assigns on push, which
is why it reached a tenant and survived a round trip. The script now derives the
correct order from the working copy — the authority the Migration controls — and
checks platform-reported numbers against the property. On the real probe it derives
1725 to position 4, between its block and the next step, which is exactly the
numbering the probe's own description says the fix should produce. Review independently
confirmed the id-is-not-order claim against the same files.

The near-miss is the lesson worth keeping: a false positive that agrees with the fault
you are hunting is far more dangerous than one that does not, because it arrives as
confirmation. Testing only the probe file would have shipped it.

**Review found two real bugs after 21 of my own mutations were caught.**

The parser anchored the id pattern to end-of-line, so any step written
`... [id = 1584] as username` — `as <alias>` names a step's result, and the real
sign-in step group uses it — was dropped from the tree entirely. Not reported as a
fault and not reported as unchecked: silent. That is worse than the blind-check
failure ADR-0001 describes, and it was confirmed against the exact prior-art file.
Fixed by taking the last match on the line rather than anchoring, which also keeps the
case that motivated the anchor: an argument containing the token.

And a mutation skipping the sibling comparison for the first pair of children under
any parent stayed green, because every fixture I had put its swap somewhere that also
tripped a later pair or a parent bound. Closed with a fixture confining the fault to
that pair.

Also hardened on review's third point: a duplicate id, a second top-level step, or an
unclosed block now raise rather than silently yielding a tree that has lost a step.
A step missing from the tree is checked by nothing and reported by nothing.

**Two boundary mutations survived my first pass** — off-by-one at either bound.
"Strictly between" is the specification word and neither bound was tested at equality.

The whole real corpus now parses without error.
