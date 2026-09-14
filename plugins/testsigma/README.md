# Testsigma migration

Converts an existing automation suite into Testsigma format, one reviewed step
at a time, using the `testsigma` CLI as the thing that decides what is
expressible.

It is built around a claim it will not make quietly: a converted test that
compiles, is accepted by the tenant and survives a round trip can still test
something weaker than the source it came from. Every check here exists because
that already happened.

## What you need

- The `testsigma` CLI on your PATH, logged in to the tenant you are converting
  into. The plugin ships no catalogue of verbs and holds no copy of the schema
  (ADR-0006); it asks the installed build what it accepts, so what is
  expressible is whatever your build says it is.
- The source suite in version control. A Migration pins a commit, and refuses
  a folder that has none.

## Where to start

**`survey`** — run once per suite. It settles which folder the suite is, checks
four refusals, pins a snapshot, probes the CLI, and creates the Migration
Directory at `.testsigma/migration/` inside the suite itself.

**`resume`** — run at the start of every later session. A Migration spans days
and a session starts blank; resume reads the Migration Directory and says where
the work stands, including whether the installed CLI has changed under it.

**`convert`** — run once per scenario. It takes the next scenario off the queue,
maps the Source Steps it reaches, resolves their elements, assembles and checks
the test, commits, and reports how many tests are delivered of how many
scenarios. One Conversion per invocation, so a Migration delivers a working test
on its first day rather than in its third week.

`convert` calls `map`, which proposes and reviews rows, and `assemble`, which
builds tests from reviewed rows. Either can be run on its own where the work
calls for it.

Two skills cover a source that describes what tests do but not how to find the
controls, and which one you want depends on what is missing.
`resolve-elements` is what a Conversion calls, one screen at a time, where the
adapter already exists and declares it carries no locators; `write-an-adapter` is
for a format with no adapter at all.

## The vocabulary

`CONTEXT.md` is the glossary, and it is worth reading before the skills. The
terms are load-bearing rather than decorative — a Concession is not a Residue,
a gap is not a refusal, and the difference decides what happens to a row.

Decisions that would otherwise look arbitrary are recorded in `docs/adr/`.

## The tests

The plugin is made of documents, so `tests/` tests documents: that a rule lives
in one place, that a pointer resolves, that a skill body stays inside the
progressive-disclosure budget, that a claim in one file is not contradicted in
another. Run them with `pytest` from this directory.
