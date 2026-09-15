# Coverage is a check, and it runs first

ADR-0001 fixes five checks and their order, chosen by what each can see. A sixth
is added ahead of them: whether the assembled test accounts for every step of
its source scenario.

## Why the five did not cover it

Each of the five asks whether the work in hand is right. None asks whether the
work is all there.

- **Validity** reads the working copy. A file holding nine steps of fifty-five is
  a legal file.
- **Compare-to-source** runs against a distinct Source Step, in mapping. A step
  nobody mapped is not a Unit of Work, so there is nothing for it to run against.
- **Tenant acceptance** and **round trip** both operate on what was sent. A
  partial test pushes cleanly and pulls back identical, because it is internally
  consistent.
- **Render check** shows a person a test that looks finished, because it is
  finished — it is the wrong extent, and extent is not visible without the source
  beside it.

The measured instance: a run converted the nine API steps at the head of a
fifty-five step scenario, stopped, and reported "all 7 steps (pure API, no UI)".
It compiled, pushed, round-tripped with no difference, and left `residue.md`
empty. Five checks and every artifact agreed the work was done.

## Where it goes in the order

First. ADR-0001 orders by what each check can see, and this one sees the whole
scenario while the others see a file. Running it last would mean spending four
checks on a test whose extent was never in question, and the cheapest refusal is
the one that happens before the expensive comparison.

It runs against an assembled test, like checks 3 to 5, and it needs the source,
like check 2. That combination is what makes it a sixth rather than a variant of
either.

## Consequences

**A converted scenario is assembled one block per source step — ADR-0015 later
widened this to let one block claim several, where a construct performs several**, labelled with
that step's text. The comparison needs a name shared by both sides, and the
source step's own words are the only one that survives the conversion. Bare
statements are not refused for being bare; they are refused because a test
written that way cannot be compared with anything, so its extent is unanswerable
and therefore goes unasked.

**A step is accounted for by a block that claims it**, whether that block holds
the conversion or stands empty as a marker. Residue and conversion both count;
silence does not.

**Coverage is reported as *n of m* always, not only when it is wrong.** A number
printed only on failure is one nobody learns to read, and this failure's whole
character was that every visible signal looked normal.

**The arithmetic is in `scripts/check_coverage.py`, and it does not read the
source.** ADR-0004 keeps source formats in documents rather than parsers; a
Gherkin reader in this script would be the first parser and would be the wrong
one, since the steps have already been read during mapping. The caller passes
them in.
