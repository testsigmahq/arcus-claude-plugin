# The five checks, and what a check record means

A Migration checks converted work five ways: it is legal in the format, it
matches the source's implementation, the tenant accepts it, it survives a round
trip unchanged, and it looks right in the application.

This document is the single definition of the order those run in, of what a
check that could not run is recorded as, and of what happens when the installed
CLI grows a check it did not have. The file that holds the record is defined in
[migration-directory.md](migration-directory.md).

## The order

Fixed by ADR-0001, and not negotiable per Migration:

1. **Validity** — the working copy is legal in the format. Machine-decidable,
   needs nothing but the working copy.
2. **Compare-to-source** — the converted step does what the source's
   implementation does, read against the implementation rather than the surface
   syntax. This is the exit condition of mapping.
3. **Tenant acceptance** — the tenant accepts the work.
4. **Round trip** — the work survives a push and pull unchanged.
5. **Render check** — it looks right in the application, judged by a person.

Not every check runs against every Unit of Work. Compare-to-source runs against
a distinct Source Step, in mapping. The other four run against an assembled
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

**Compare-to-source needs no tenant and no network.** Neither does Validity. So
cheapest-first was not even buying what it appeared to buy, while it did reliably
push the one check with a record of finding faults to the end of the queue, where
it did not run.

Checks 3 and 4 are the only ones that need a tenant. Survey, mapping, element
resolution from a source, and assembly all run without one.

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
