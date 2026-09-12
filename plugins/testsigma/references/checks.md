# The six checks, and what a check record means

A Migration checks converted work six ways: it accounts for every step of its
source, it is legal in the format, it matches the source's implementation, the
tenant accepts it, it survives a round trip unchanged, and it looks right in the
application.

This document is the single definition of the order those run in, of what a
check that could not run is recorded as, and of what happens when the installed
CLI grows a check it did not have. The file that holds the record is defined in
[migration-directory.md](migration-directory.md).

## The order

Fixed by ADR-0001 and extended by ADR-0010, and not negotiable per Migration:

1. **Coverage** — the assembled test accounts for every step of its source
   scenario, each one either converted or standing as a marker. Machine-decidable
   against the source's step list, and the only check that can see a conversion
   that stopped early. See ADR-0010 for why the other five cannot.
2. **Validity** — the working copy is legal in the format. Machine-decidable,
   needs nothing but the working copy.
3. **Compare-to-source** — the converted step does what the source's
   implementation does, read against the implementation rather than the surface
   syntax. This is the exit condition of mapping. Partly machine-assisted:
   `scripts/check_call_chain.py` counts the actions the source performs against
   the actions the block performs, given the row's `Source` symbol:

       python3 scripts/check_call_chain.py \
         --source-root <the suite's source> --symbol Class.method \
         --block "<a fragment of the block's label>" <the assembled test>

   It names both lists and reports rather than refuses. A matching count is not
   proof — it cannot see an action converted into the *wrong* action, only one
   converted into nothing. It is not a substitute for reading the
   implementation; it is the thing that catches the reading that went wrong, and
   it caught both dropped submits found by hand.

   Mapping asked for this walk in prose before the script existed, and a row was
   still written recording four of its source method's five actions. It was
   marked `reviewed` and reused across every scenario that followed. An
   instruction a reader believes they followed is not a check.
4. **Tenant acceptance** — the tenant accepts the work.
5. **Round trip** — the work survives a push and pull unchanged.
6. **Render check** — it looks right in the application, judged by a person.

Not every check runs against every Unit of Work. Compare-to-source runs against
a distinct Source Step, in mapping. The other five run against an assembled
test, in assembly, because a single step cannot carry a fault that only exists
between steps. The order is one order over both stages, not two.

The order follows what each check can see, not what it costs. That deliberately
puts the expensive source comparison second rather than last, and a Unit of Work
is not done until it has happened.

The evidence for that ordering is specific. One scenario was converted, passed
compile, tenant preflight and a full round trip cleanly on the first attempt, and
was still wrong in six ways. Every fault produced a test that ran and passed
while testing something weaker or different, which is the defining property of
the class: executing it cannot find them. One retroactive pass of source
comparison found five of the six in about fifteen minutes, and it only ran
because someone asked what was left. The three automated checks found none.

**Validity needs a workspace, and a workspace needs no tenant.** It is worth
saying because the first half sounds like it contradicts the second: `validate`
reads a working copy inside a workspace, and a workspace is three marker files
carrying coordinates. Those markers can be written by hand offline, which is what
`authoring.md` does to ask the build a question, so Validity genuinely needs
nothing but the working copy.

**Compare-to-source needs no tenant and no network.** Neither does Validity. So
cheapest-first was not even buying what it appeared to buy, while it did reliably
push the one check with a record of finding faults to the end of the queue, where
it did not run.

Checks 3 and 4 are the only ones that need a tenant. Survey, mapping, element
resolution from a source, and assembly all run without one.

## A check built on residue can only find what leaves residue

The element sweep detects a dropped step by the element it orphaned. So it finds
a drop that left an element behind, and cannot find one that took its element
with it. That is not a weakness to tighten — it is the shape of the method, and
every check built the same way inherits it.

Measured. A conversion dropped the submit click at the end of a composite: the
source's quantity helper is clear, click, type, **click Go**, and the converted
block had the first three. The button's locator was never lifted, so there was
no orphan to notice. The file validated, covered 55 of 55 source steps, pushed,
and pulled back identical.

Coverage did not catch it either, and for a reason worth separating: coverage
asks *is every source step present*, not *is every source step complete*. A block
existed and held statements, so the step was accounted for. Presence and
completeness are different questions and one number cannot answer both.

The rule that falls out: **a check that asks what the output contains can only
find faults the output still shows. A check that asks what the source required
can find the rest.** When adding one, say which kind it is. The five before this
section are output checks except compare-to-source, which is the one that reads
the source — and which is the only one that could have caught this, run by a
person, in mapping.

## A stage's checks are run by whoever performs the stage

ADR-0005 puts each check inside the stage that produces the work. The corollary
is about delegation: hand an entire stage to an agent whose work cannot be
inspected, and its check record becomes a claim rather than a record.

Breadth may be delegated — which files exist, which phrasings recur. A whole
stage may not, because what comes back is a report, and a report is exactly what
these checks exist to distrust. One measured run handed a conversion to an agent
and reported "all 7 steps" for a scenario of fifty-five; another handed off the
whole pipeline, promised to report back when it finished, and ended having
written nothing. In both the parent had no way to tell, because in both the only
evidence was prose.

Write into `check-record.md` what ran, against what, under which build — not
what was reported to have run.

## A check that could not run is not checked

A check that could not run is recorded as not checked. It is never recorded as a
pass, never left blank, and never inferred from a check that did run.

This is the dangerous direction. A missing feature announces itself; a false pass
does not. Three clean checks that cannot see a fault class are worse than no
check at all, because they read as reassurance and spend the Operator's attention
somewhere else.

A check can fail to run for reasons that are nobody's fault — no tenant is
reachable, the installed build does not perform it, a person has not looked at
the application yet. The record says which, so the gap is a known gap rather than
an absence of information.

## When the CLI gains a check

Compare the installed build against the one recorded in `migration.md` at the
start of every session; `cli-probe.md` says how, and says what that comparison
can and cannot see. When the build has gained a check it did not have, every
Unit of Work completed before it is marked as not checked against that
capability.

**A changed build is the signal, not a changed help surface.** A new check often
arrives as a new rule inside a command that already existed, which the help
surface cannot show: the worked example below was a stricter `validate`, and
`validate` was listed before and after. So a build that differs at all is
treated as a build that may have gained a check, and the Units converted under
the old one are marked as not checked against it. Waiting for evidence of a
specific new capability is waiting for a signal that does not arrive.

They do not inherit a pass they never earned. Silently inheriting it is the
obvious alternative and is how a Migration accumulates work nobody ever verified,
under a record that says otherwise.

**A build can also withdraw a capability, and that is the case that costs
work.** A verb removed, a slot that narrows which kinds it will hold, a value
kind renamed: each turns work that was expressible into work that is not, and
none of it announces itself. Per ADR-0008 this plugin does not support the old
spelling alongside the new one — the Operator rewrites the affected rows against
the installed build — so a losing change has to be visible as a change rather
than surface later as a converted test the build no longer accepts. Treat any
differing build as capable of having withdrawn something as well as gained
something, and re-check rather than assume the direction.

This has already happened once rather than being imagined. A fault class that a
person caught by eye became an automatic refusal in the CLI inside about a day.
Work converted before that change had never been checked for it, and nothing in
the system would have said so.

Going back to re-check is then the Operator's decision, with a known cost in
Units of Work, rather than an oversight nobody notices. `resume` surfaces the
count at the start of every session, which is what makes the decision a decision.

## What the record holds

The Check Record names which checks ran against which Unit of Work, by name, and
the CLI build each ran under. A recorded pass with no build attached is a pass
whose meaning cannot be recovered once the tool changes.

A **Unit of Work** is what a check runs against, and it differs by stage. While
mapping it is a distinct Source Step, checked once and reused at every
occurrence. While assembling it is a whole assembled test, because document order
describes a fault that only exists between steps.

The record is read, not reconstructed: it is a file in the Migration Directory,
readable without running anything and without a tenant. That is the point of
writing it down rather than inferring the state of verification from what exists
on disk.
