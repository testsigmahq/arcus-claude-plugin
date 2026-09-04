---
name: map
description: Use when mapping a surveyed suite's Source Steps into Testsigma expressions — building or continuing the Step Map, deciding how a Gherkin phrasing or Tosca module should be expressed, or working through unreviewed rows. Opens the helper behind each source line to recover what it really does, compares every proposed expression against that implementation before a row can be called reviewed, and records anything the format cannot express as Residue with its cause.
---

# Map: build the Step Map

Mapping decides, once per distinct Source Step, how that step is expressed in
Testsigma. Every occurrence of that step then reuses the decision, which is why
the cost of a Migration scales with a suite's vocabulary rather than its line
count.

This stage owns the check that matters most. Four of the six known faults in the
conversion that produced this plugin were a source line hiding a helper that did
something else, and comparing against the implementation is the only thing that
found them. By ADR-0005 that check has no skill of its own: it is the exit
condition of this one.

**Who you are talking to.** The person running a Migration is the Operator.
They know Testsigma and do not necessarily read code, so nothing you put in
front of them carries code, a file path, a stack trace or a diagnostic code.
Those go in the Migration Directory.
[../../references/asking.md](../../references/asking.md) is the rule for what a
question may contain; this does not restate it. See `CONTEXT.md` for the
vocabulary this plugin uses with them.

The files this reads and writes are defined in
[../../references/migration-directory.md](../../references/migration-directory.md).

## Before anything: there must be a Migration to map into

If `.testsigma/migration/` is absent, survey has not run. Stop. There is no
adapter chosen, no snapshot pinned and no Step Map to write rows into, and
mapping without those produces rows nobody can trace back to a source.

If it is present, read it before working. `migration.md` names the adapter and
the pinned snapshot; `step-map.md` holds the rows already decided. Run the resume
command if you need the state in full.

## Step 1: Take one distinct Source Step at a time

Work the distinct Source Steps from the enumeration, not the suite's lines. Each
distinct step is one Unit of Work, carries its occurrence count from survey, and
is decided once.

Reuse the verdict at every occurrence. A step decided here is not revisited when
it appears again, in another feature file or another scenario; that reuse is the
entire economics of mapping, and re-deciding a step per occurrence would cost
what rewriting the suite by hand costs.

Order by occurrence count, highest first, because an early wrong verdict on a
frequent step is the most expensive mistake available. Then deal with the steps
that genuinely vary, which carry most of the judgement. The singletons amortise
nothing and can wait, but they set the floor cost and none can be skipped.

## Step 2: What a row carries

A row records the source text, its occurrence count, its parameter shapes, the
proposed expression, and a status. Those five exist so that reviewing a row does
not mean going back to the source, which is the difference between a review that
happens and one that is deferred.

One Source Step may map to several Testsigma steps. A source line that really
performs three actions is expressed as three, and forcing it into one is how a
Composite Step becomes a converted test. The row holds the whole sequence.

A status is `unreviewed`, `reviewed` or `residue`, as defined in the Migration
Directory reference. A row is `unreviewed` from the moment it is written.

## Step 3: Open the helper behind the line and read its sequence

The source line does not tell you what the step does. Open the helper it names,
every time, for every distinct Source Step, and read it for sequence. Work
against the implementation rather than the surface syntax: the surface is what
was already trusted on the conversion that produced this plugin, and it was
wrong four times out of six.

The adapter's own Sequence section states where the sequence lives for this
format and which traps recur in it. Follow it. Four shapes recur across every
source format met so far, and all four produce a test that runs and passes:

**A helper that does less than its line implies.** The line reads as a choice
being committed; the method only sends text, and no caller ever clicks the submit
control. Converting the implied action invents a step the source never performed.

**A helper that does more than its line implies.** The line reads as one action;
the method tests visibility, clicks an expand control conditionally, clears,
types and presses a key. None of that is visible from the source line.

**A helper named like a wait that is a loop.** Treat every helper whose name
contains `wait`, `until`, `refresh` or `poll` as a loop until the source shows
otherwise. Include the shape that reads as an assertion, which is where the
volume actually is rather than in the obvious spellings. These re-drive the
interface on each pass, so flattening one into a passive wait produces a test
that looks right and does something else.

**A helper that delegates.** When a method calls another method, follow it: the
sequence is the flattened sequence of the leaves. Stopping at the first method
the source names is the most natural way to get this wrong, because that method
looks complete.

Report what the helper actually does, in the Operator's terms, whenever it
differs from what the line implies. A difference found and not said is a
difference that reaches the converted suite.

## Step 4: Compare the expression against the source before finishing

The comparison is the exit condition of this stage. A row cannot be marked
reviewed before its proposed expression has been compared against the helper's
implementation — not when the count is large, not when the step looks obvious,
and not when the session is ending. A row that has not been compared stays
`unreviewed`, which is what the status is for.

This is second in the check order by ADR-0001 rather than last, and it is not
replaceable by running anything. Every fault in this class produces a test that
runs and passes while testing something weaker or different. Compile, tenant
preflight and a round trip caught none of the six; this comparison caught five in
about fifteen minutes.

Compare on three points: whether the expression performs the same actions in the
same order, whether it asserts the same thing, and whether anything the helper
does is missing from it or invented in it.

**A wildcard or substring comparison in the source is a question, not a
licence.** When the source matches loosely, what was being checked is unclear,
and writing an equally loose comparison in Testsigma propagates a weakness that
may never have been intended. Raise a question about what the assertion is meant
to establish, record it, and leave the row `unreviewed` until it is answered.

## Step 5: Residue, for what the format cannot express

When a Source Step cannot be expressed, record it in `residue.md` with a stated
cause and the reasoning that produced the ruling. An unexpressible step and an
unresolved element are distinct causes and are never merged.

No entry is final. The reasoning is recorded so a ruling can be overturned rather
than hardening into a fact: an entry is revisited when the format gains a
spelling, or when someone finds one nobody had used. One case already believed
unexpressible turned out to have a spelling that existed all along.

Residue is not Divergence. Residue is work declined, visibly, with a reason. A
Divergence is work expressed and reported as done that is not equivalent to the
source. Residue is the honest outcome; a Divergence is the one this stage exists
to prevent.

## Step 6: Record and commit

Write each decided row into `step-map.md` as you finish it, not in a batch at the
end. Rows already written survive a session that ends early; rows held in a
session do not.

Commit the Migration Directory as rows accumulate, scoped to that directory. Put
anything unresolved where it belongs before finishing: a question for the
Operator into `open-questions.md`, something learned about Testsigma into
`platform-facts.md`, something only they can answer about their application into
`application-facts.md`.

Then report progress in rows: how many distinct Source Steps are decided, how
many remain, and what the comparison found. Occurrence-weighted coverage is the
number that means something to the Operator, since decided rows carry their
occurrence counts with them.
