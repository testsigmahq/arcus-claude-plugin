---
name: write-an-adapter
description: Use when a Migration's source format has no Source Adapter yet — a Robot Framework suite, an ALM design-step export, a Katalon or UFT project, any format the shipped adapters do not cover — or when someone asks to add support for a new source format. Walks through establishing the three properties from a real export, finding where the true action sequence lives, and stating a normalisation rule precise enough that two people counting independently agree.
---

# Write a Source Adapter

A Source Adapter is the only part of a Migration that knows a source format. Adding
support for a new one means writing a document, not shipping code (ADR-0004), which
is why this is a skill an Operator's own team can run without us.

The format the document must satisfy — the frontmatter, the three properties, the six
required sections and the worked example — is defined in
[../../adapters/README.md](../../adapters/README.md). Read it first and follow it
there rather than from anything restated here, so there is one definition of the
contract.

**An adapter is finished when the adapter suite passes against it**, not when it
reads well. Run `python3 -m pytest tests/test_adapters.py` from the plugin root; the
suite parses the document, insists on all three properties and all six sections, and
checks the stated worked example against the fixture using the document's own
normalisation rule. A document whose rule and counts disagree fails.

**Who you are talking to.** Whoever is writing an adapter may be a developer, but a
question that reaches the Operator still follows
[../../references/asking.md](../../references/asking.md). Do not put source code or a
diagnostic in front of them.

## Before anything: distrust the documentation

**Published documentation about a source format may be wrong, and has been.** Open a
real export from the format and read it before writing a word of the document.

The Tosca adapter is the case. The public claims were wrong twice over. The export
was described as an opaque binary needing the vendor's tooling to read, and it is
gzip-compressed JSON that `gzip.open` and `json.load` read in two lines. And
identification was described as living on module attribute entities, while the real
export contains no `XModuleAttribute` entity at all — not one, which is the fact that
forces Element Resolution into a Phase of its own for that source.

Had either claim been taken on trust, the adapter would have been wrong about
whether the format is readable and wrong about its Phase structure. Both are
decisions everything else depends on.

So: get a real export, of a real suite, from the team whose suite it is. Read it
directly. Where you cannot get one, stop and say so rather than writing from a
specification — an adapter written from documentation is a guess with a table in it.

## Step 1: Establish the three properties

Answer all three, from the export, with an explicit value each. None may be left
unstated: each decides something structural, and an absent value is not a neutral
default but a decision made silently.

- `hides-sequence` decides whether every source line must be read through to its
  implementation, which sets the cost of the whole mapping stage.
- `carries-locators` decides whether elements are resolved inside mapping or in a
  Phase of its own after it.
- `value-language` decides whether a single value can hide a sequence of actions.

What each property means is defined in the contract. Do not restate the definitions
in the new document; answer them.

**Quote every value.** Unquoted `yes` and `no` are booleans in YAML, and the whole
point of these fields is that a person stated a value deliberately rather than a
parser inferring one.

**The three are independent.** No value can be inferred from another: every format
met so far differs on them, and the two shipped adapters differ on all three. Answer
each from the export separately.

Use `"sometimes"` only where the answer genuinely varies inside one format, and then
say in the body how to tell which case you are in. `"sometimes"` with no way to tell
is worse than a wrong answer, because it looks considered.

## Step 2: Find where the true sequence lives

Say where the real action sequence is recovered from, and how. This section is
required whatever the answer.

**Say it even when nothing is hidden.** "Control flow is explicit and no line hides
a helper" is a finding and belongs in the document. A Sequence section that is silent
because there was nothing to report is indistinguishable from one where nobody asked,
and the question not being asked is how four of six faults reached a converted suite.

Where anything is hidden, the section must say plainly that the helper is opened for
**sequence** and not only for locators. That is the specific mistake that has already
happened: the files were opened, they were read for locators, and what the code
actually did was never asked.

Look for all four shapes while you are in there: a helper that does less than its
line implies, one that does more, one named like a wait that is a loop, and one that
delegates so the real sequence is the flattened sequence of the leaves.

## Step 3: State the normalisation rule

The rule decides when two source lines are the **same Source Step**, and it is what
makes a Collapse Ratio mean anything.

**It must be precise enough that two people applying it independently get the same
count.** Write it as numbered steps applied in order, each one mechanical. Prose like
"ignore incidental differences" is not a rule; it is an intention.

**The order of the steps changes the answer, so state it as an order and check it.**
The Cucumber rule had exactly this bug: it stripped trailing punctuation after
replacing numbers, and because the number pattern refuses digits touching a full
stop, `I see 5.` and `I see 5` normalised differently. The rule was faithfully
implemented and the rule itself was wrong. Reordering two steps fixed it.

Decide explicitly what is a parameter and what is part of the phrasing. Then apply
the rule to a real sample by hand, on paper, before writing it down — a rule that has
never been run is a rule with a bug in it.

## Step 4: Build the fixture and the worked example

The `## Enumeration` section ends in a table of the distinct Source Steps with their
occurrence counts, one row per step, measured against a fixture. This is what turns
"precise enough that two people agree" into a checked property rather than a claim:
the suite applies the document's own rule to the fixture and compares.

List every row. A partial table cannot be checked against the rule that produced it,
which is a mistake the Tosca adapter made before review caught it.

Keep the fixture small and make it carry the format's traps rather than its typical
case. The shipped fixtures each hold deliberate ones — a helper that does less than
its line says, a name ending in a space, a value spelling one action two ways — and
each was a real shape found in a real suite, not an invented edge case.

Where the fixture is a real customer export, do not commit it. Build a synthetic one
carrying the same shapes, and keep the checks against the real file conditional on
its presence.

## Step 5: Read the two shipped adapters as examples

Read both before writing, and read the one that least resembles your source as well
as the one that most does. They are useful as examples precisely because they sit at
opposite corners of all three properties:

| Adapter | `hides-sequence` | `carries-locators` | `value-language` |
|---|---|---|---|
| `cucumber-java.md` | yes | yes | no |
| `tosca-subset-export.md` | no | no | yes |

Cucumber hides its sequence behind a page-object layer, carries its locators in those
same files, and has no value language. Tosca is the inverse on all three: its control
flow is explicit, it carries no locators at all, and a single value can encode several
actions. Between them every property is demonstrated in both directions, so whatever
your format does, one of the two has met it.

Where your format sits between them, say so and say why, rather than rounding to
whichever example you read first.

## Step 6: Finish

Run the adapter suite. Then report which three values were established and what
evidence settled each, so a wrong reading can be corrected before a Migration depends
on it.

Anything you could not settle from the export goes into the Migration Directory
rather than into a guess in the document: a question for the Operator, or a Platform
Fact if probing would answer it. Its files are defined in
[../../references/migration-directory.md](../../references/migration-directory.md).
