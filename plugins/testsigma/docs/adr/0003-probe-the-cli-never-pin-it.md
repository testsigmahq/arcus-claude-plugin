# Probe what the CLI checks; never pin a version

The plugin pins no CLI version and assumes no CLI behaviour. Every check that leans
on the CLI names the specific diagnostic code it relies on, asks the installed build
whether that code exists, and records the build in the Migration Directory when a
migration starts. A named code that is absent downgrades its check to not checked.

## Considered Options

Pinning a version is the obvious alternative and would make behaviour reproducible.
It fails against how the tooling actually moves. One fault class, conditional bodies
numbered outside their block, was caught by a person, and within about a day the CLI
had gained a pre-order numbering pass that refuses it as `TSS1140`. So what the
tooling checks for you grows underneath a migration that lasts weeks.

The dangerous direction is not a missing feature but a false pass: a plugin that
assumes a check is present will report that it ran when the CLI no longer performs
it, and will spend Operator attention re-verifying what the tool now refuses.

## Consequences

Where the plugin can compute a property itself, it should, rather than delegating.
The document-order property is the worked example: for every step with a parent, the
child's order lies strictly between its parent's order and the parent's next
sibling's. That is three lines of arithmetic over the server's own step list, owned
by the plugin, and it holds whether or not the installed CLI checks it.

A Check Record therefore names the checks that ran against each unit of work. When
the CLI gains a check it did not have, the units converted before it are marked as
not checked against that capability rather than inheriting a pass they never earned.
Going back to re-check is then a visible decision with a known cost. Silently
inheriting the pass is the obvious alternative and is how a migration accumulates
work that nobody ever verified.
