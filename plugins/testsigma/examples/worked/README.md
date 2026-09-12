# A worked example

One small workspace that validates clean — no errors, **no warnings** — showing
the shape of a correct `.sigma` file end to end.

It exists because `list blocks` gives a block's *grammar* and nothing gives its
*shape*: the nesting, the quoting, which reference form a name takes, whether an
`if` header is parenthesised. Measured conversions spent six `validate` calls
rediscovering that, and one of them spent them by writing candidate files and
deleting them between attempts.

    testsigma validate            # from this directory

## What each file is here to show

| File | Shows |
|---|---|
| `…/elements/SignIn.screen.sigma` | a screen nests elements; `locator` + `locatorType`; a dynamic element carrying `${param.x}`; **elements ordered by name** |
| `…/tdps/Demo/SignIn.tdp.sigma` | columns, then a named set |
| `…/tests/Demo/SignIn.test.sigma` | `element.name` vs `element["name with spaces"]`; an `if` header with no parentheses; a setting in `[ ]` after the arguments; an empty `block` as a marker; a bound profile |
| the four markers | `project` / `application` / `version` / `folder`, each carrying its `[id = N]` |

The ids are placeholders. `validate` is offline and does not resolve them; a
real workspace gets them from `testsigma attach`.

## Two things it deliberately does not do

**No api block.** Every measured run got api blocks right first time from
`list blocks --kind api --json`. The probe covers it, so an example would be a
copy that can go stale for no gain. Shape facts are what belong here — the
things no listing can express.

**No `group "…" { }` as a marker.** A run wrote markers that way. It validates
offline and is refused at push with **TSS1102**, because a group invocation
needs a step group of that name to exist. An empty `block` needs nothing. The
example holds no `group` at all, and a test asserts that, because an example
containing the failing shape teaches it.

## The check

`tests/test_worked_example.py` compares the files against an expectation
**written out separately** — nine named shapes, each with where it lives. That
is a source check. The obvious alternative, "every construct I demonstrate
appears in the result", is a residue check and could not notice half the shape
missing, which would make a demonstration of correctness that was itself half
wrong. `references/checks.md` has the general form of that distinction.

The `validate` assertion refuses warnings as well as errors. A TSF3001 or
TSF3004 means the next `pull` rewrites the file, so an example carrying one
demonstrates a layout the tool disagrees with. That is how the element ordering
was found: no measured run reached warnings-clean, so none of them learned it.
