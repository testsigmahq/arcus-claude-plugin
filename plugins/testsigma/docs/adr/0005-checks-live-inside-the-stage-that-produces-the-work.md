# Checks live inside the stage that produces the work

There is no separate verification skill. Comparing a converted step against the
source's implementation belongs inside the mapping skill, and the order-and-nesting
check belongs inside the assembly skill. A stage does not finish until its own checks
pass. Only the Check Record is separate, because it outlives any single stage.

## Considered Options

A dedicated verification skill is the obvious structure and it is the one that
already failed. On the first conversion, checking against the source was a separate
late activity rather than part of finishing a unit. It ran exactly once, retroactively,
about fifteen minutes long, and only because someone asked what was left. It found
five of the six faults on that single pass. The render check, also a separate late
activity, never ran at all.

The lesson is not that the checks were badly designed. It is that a check placed after
everything is a check that does not run. Making it the exit condition of a stage is
the only version that survives contact with a multi-day job.

## Consequences

Because the checks sit inside stages, the two granularities of ADR-0001 fall out
naturally rather than needing coordination: mapping checks a distinct Source Step
once and reuses the verdict, and assembly checks a whole test for document order.
Nothing has to remember to revisit either.

Operator questions follow the same rule for the same reason. Any skill may raise one
at the moment it arises, because that is when the information is missing. What needs
a home outside the stage is not the asking but the outstanding question: one file of
open questions, added to immediately and cleared only by an answer. The failure to
design for here is not a question that goes unasked, it is a question that is asked,
ignored, and then forgotten by everything in the system.
