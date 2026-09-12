# Adopting work the project already holds

A target project is not always empty. A team often converts part of a suite by
hand before a Migration starts, and that work is the most valuable thing in the
project: someone decided what each step meant, and a person can be asked why.

**Adoption** is taking an entity the project already holds and binding it to the
Step Map row whose Source Step it expresses, instead of authoring a second one.

Without it a Migration hands back a project with two of everything and no way to
tell which is live — the same failure the element rule names, arriving at the
scale of whole tests and step groups rather than single controls.

## The inventory comes first, or none of this is real

Every rule here compares against what the project holds, so what it holds must be
on disk before mapping begins. Nothing may be concluded from memory of a tenant.

    testsigma pull version --write

run from the working copy's directory, writes a working copy of every entity the
version holds. Put them under `.testsigma/migration/existing/` and commit them
with the rest of the Migration's state.

They are **evidence, not working copies to edit**. Their value is that they say
what the project holds at the snapshot the Migration started from, and an edited
one has stopped saying that. A Migration authors under the suite's own test
directory and never under `existing/`.

`existing/` is not one of the Migration Directory's seven files and survey does
not create it when there is nothing to pull. Its absence means the project was
empty, or that nobody looked — which is why survey records which of the two.

## Adoption is read-only against the source project

Pull, never push. A project holding hand-written work is one a team depends on,
and a Migration's first act against it must not be a write. Where the Operator
names a project as read-only, that is absolute and covers every subcommand that
writes: `push`, `push --delete`, `push --overwrite-remote`, and attaching.

Convert into a project of the Migration's own, and adopt from the existing one by
reference. If the two must eventually be one project, that is a merge the
Operator performs deliberately, once, with both halves finished and checked —
never a side effect of a conversion run.

## An adopted row

A row whose Source Step the project already expresses is `adopted`. Its Expression
cell names the entity on a line of its own:

    Adopted: stepGroup "Search the menu" — verified against MenuPage.searchMenu

The prefix is fixed for the reason `Concession:` and `Kind:` are: the reviewer's
question is "show me everything this Migration did not write", and a fixed prefix
makes that a sweep rather than a reading.

`adopted` is a status and not a kind of `reviewed`, because the two answer
different questions. `reviewed` means a person decided how to express this step.
`adopted` means a person decided it was already expressed. A resume counting
*reviewed n of m* must not report adopted rows as work still to do, and a reviewer
asking what this Migration actually produced must not be shown them either.

**An adopted row is still assembled.** The scenario needs a step where its Source
Step falls, and that step calls the adopted entity. Adoption removes the
authoring, not the step — so coverage is unaffected, and a scenario with adopted
rows has exactly as many blocks as one without. A row that skipped assembly would
be a silent hole of precisely the kind an empty marker block exists to prevent.

## Verify before adopting, never after

A hand-converted step drops actions the same way a generated one does, and the
drop is inherited by every scenario that adopts it. Adoption is the moment to
find that, because after it the row is trusted and nothing downstream re-reads the
source.

So run the call-chain comparison against the pulled working copy, with the Source
Step's implementing symbol:

    python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_call_chain.py \
      --source-root <the suite> --symbol <Class.method> \
      --block <a fragment of the entity's label> \
      .testsigma/migration/existing/<the pulled file>

This is the same check that guards a row the Migration wrote, pointed at a row it
did not. It has to be: an adopted row and an authored one are read identically by
everything after mapping, so they must have cleared the same bar to get there.

Three outcomes, and the third is the one that matters:

- **It agrees.** Adopt the row and record the symbol it was verified against.
- **It cannot compare** — exit 2, no symbol to resolve, a source with no
  implementation behind it. Adopt only on a person's reading, and say in the
  Expression cell that the check could not run. An unverifiable adoption is a
  decision, and one recorded as verified is a lie the next session inherits.
- **It disagrees.** Do not adopt, and do not quietly author a replacement either.
  The existing entity is live: something runs it, and a team believes it covers
  this step. Put the difference to the Operator as an open question, naming the
  actions the source performs that the entity does not.

That last case is why adoption cannot be a bulk operation. Every disagreement is
a fact about the project the Operator owns, and a run that resolves them by
itself has overwritten their judgement with its own.

## Matching, and what a near match means

Match on what the entity does, not on what it is called. A name is how a team
found an entity again, and two teams converting the same step name it two
different things.

Where a name nearly matches and the check disagrees, that is evidence of a
*different* step, not a broken one. The strong case is the opposite pairing: an
entity whose name says nothing and whose actions match exactly.

Where nothing matches, the row is ordinary work. Adoption is an optimisation on
the rows it fits and never a stage everything must pass through.
