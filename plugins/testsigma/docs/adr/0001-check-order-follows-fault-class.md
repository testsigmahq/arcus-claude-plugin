# Checks run in order of what they can see, not what they cost

A migration checks a converted test five ways: it compiles, it matches the source's
implementation, the tenant accepts it, it survives a round trip unchanged, and it
looks right in the app. We run them in that order, which deliberately puts the
expensive source comparison second rather than last, and a unit is not done until
that comparison has happened.

## Considered Options

Cheapest-first is the obvious ordering and is what we did on the first conversion.
It is wrong here. One scenario was converted, passed compile, tenant preflight and a
full round trip cleanly on the first attempt, and was still wrong in six ways. Every
fault produced a test that ran and passed while testing something weaker or different,
which is the defining property of the class: executing it cannot find them.

Of the six, five were caught by one retroactive pass of source comparison lasting
about fifteen minutes, and it only ran because someone asked what was left. The
remaining fault was caught by a person looking at the app. The three automated checks
caught none. The round trip is structurally incapable of catching them, because it
rebuilds the step tree from parentage and so cannot see document order, a weakened
assertion, or a missing step.

Source comparison also needs no tenant and no network, so cheapest-first was not even
buying what it appeared to buy.

## Consequences

A check that cannot run is recorded as not checked. It is never allowed to read as a
pass, because three clean checks that cannot see the fault class are worse than no
check at all: they read as reassurance.
