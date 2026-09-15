# 33 — An empty block must name a Cause

**What to build:** Issue 31 made a block claim every source step it performs, so an
empty block means Residue and nothing else. One route still fakes it: an **empty block
can claim five steps and pass**. Coverage reads labels and never reads bodies, so a
claim naming five steps over a block that performs none accounts for all five.

That is the shape 31 exists to prevent, reachable by writing it directly.

**The discriminator is the Cause, not the emptiness and not the count.** A marker
already names what was needed and a Cause from the fixed set in
`migration-directory.md` — `step addon`, `data generator addon`, `unresolved element`,
`no catalogue`, `declined`. A block performing work names no Cause. So:

> **An empty block must name a Cause. A block naming a Cause may be empty.**

| Block | Body | Cause | |
|---|---|---|---|
| Residue marker | empty | yes | legitimate |
| The fake | empty | **no** | **refused** |
| Absorbing block | non-empty | no | legitimate |
| One marker over a run of declined steps | empty | yes | legitimate |

**Why the count cannot be the test.** The obvious rule — an empty block claims at most
one step — is wrong. Five consecutive declined steps are honestly one marker, so a count
test refuses a legitimate shape while a one-step fake still passes. The Cause is what
separates them, and it separates them however many steps are claimed.

**The Cause gets a fixed prefix.** Today it rides in free prose inside the bracketed
qualifier, so checking it means hunting five strings in arbitrary text. `Adopted:`,
`Concession:` and `Kind:` are already fixed prefixes elsewhere for exactly this reason —
a reviewer's question becomes a sweep rather than a reading. A marker's qualifier
becomes:

    block "Validate list of UI values (Residue: step addon — check all 10 values)" {
    }

The claim is the step text, unchanged, so coverage is unaffected. `Residue:` then a
Cause from the fixed set then the need, which is what a person can act on.

**This is candidate 2 from the original three, in its proper role.** A fixed prefix was
rejected as *the fix* for the empty-block collision, because it would have left 79 blocks
still lying about their shape. As a machine-checkable discriminator on top of claims —
with six markers left rather than eighty-five — the readability objection no longer
applies.

**Blocked by:** 31.

**Status:** ready-for-agent

- [ ] A marker's qualifier begins `Residue:` and names a Cause from the fixed set
- [ ] `authoring.md` gives the form, and says the claim is still the step text
- [ ] The coverage check refuses an empty block whose label names no Cause
- [ ] It accepts an empty block that names one, however many steps it claims
- [ ] It does not refuse a non-empty block for lacking a Cause
- [ ] A Cause outside the fixed set is refused rather than treated as prose
- [ ] The refusal says what is wrong: work claimed by a block that performs none
- [ ] `assemble` writes the prefixed form where it stands a marker
- [ ] A block naming a Cause and carrying a body is reported — the two disagree
- [ ] The existing marker guidance is amended, not duplicated
