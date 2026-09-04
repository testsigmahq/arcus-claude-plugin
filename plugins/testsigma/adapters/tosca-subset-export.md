---
name: tosca-subset-export
source: A Tosca subset export (`.tsu`) — gzipped JSON holding one flat list of entities
hides-sequence: "no"
carries-locators: "no"
value-language: "yes"
---

# Tosca subset export

A `.tsu` is gzip-compressed JSON with a single top-level key, `Entities`, holding a
flat array. Every entity carries an `ObjectClass`, a GUID `Surrogate`, a map of
string `Attributes`, and a map of `Assocs` pointing at other entities by surrogate.
Nothing else. There is no nesting in the file: the tree is entirely in the
associations.

Everything below was established by reading a real export of 405 entities, not from
documentation. Where a number appears it was measured.

## Source Step

An `XTestStep`, taken together with the `XModule` it references. The module is the
reusable unit of intent — the Tosca equivalent of a Gherkin phrasing — and the step
is one use of it with its own values attached.

An `XTestStep` has no text of its own worth mapping. Its `Name` is a human label
that varies between uses of the same module; the module's name is the thing that
recurs. In the measured export, 48 steps referenced 19 distinct modules.

## Normalisation

Two `XTestStep` entities are the same Source Step when they reference the same
`XModule`. Compare by the module's surrogate, not by its name: names are edited and
carry trailing whitespace, and the measured export contains a module whose name ends
in a space.

Do not normalise the step's own `Name`. It is a label, not a phrasing, and treating
it as one inflates the vocabulary with strings nobody reuses.

Values do not enter the comparison. A module used with different values is the same
Source Step with different parameters, which is exactly the collapse mapping exists
to exploit.

## Sequence

**Order is carried only by position within the association arrays.** No entity has
an order, index, sequence or position attribute — the measured export's 46 distinct
attribute names contain no such field, only a `ReorderAllowed` boolean, which is a
permission and not a position. There is nothing to sort by.

So the sequence of a test is recovered by walking associations in the order the
surrogates appear inside them, starting from the `TestCase` and following `Items`.
Walking the top-level entity list instead is wrong: file position is not sequence,
and the export contains entities belonging to no test at all — 8 of the 48 steps in
the measured export are reachable from no test case, living in the step library. A
reader that walks the flat list produces a sequence that looks complete and is not.

That the flat list happened to agree with the recovered order for the one populated
test case in the measured export is a coincidence of that file and not a property to
rely on. The export offers no attribute that would let a reader check the agreement,
which is the whole reason position is the only signal.

**The export is transitively closed.** Every surrogate referenced by any entity is
present in the file — 0 dangling references in the measured export — so the reusable
blocks a test names travel with it and true sequence is recoverable from the file
alone, with no access to the source system.

Resolve `TestStepFolderReference` entities to the `TestStepFolder` or
`ReuseableTestStepBlock` they point at, and splice that block's steps in at the
reference's position. A reference contributes no step of its own.

**Carry a visited set.** The entity graph is not a tree and it cycles: resolving
references without one recurses until the interpreter stops, which is how this was
found. Skip a surrogate already on the current path rather than following it again.

Control flow is explicit as `TestCaseControlFlowItem` nodes with branch folders
beneath them, so nothing hides behind a helper. That is why this adapter declares
`hides-sequence: no` while a page-object source declares yes.

## Locators

**This source carries no locators.** Not one. There are no `XModuleAttribute`
entities in the export and no identification parameters anywhere — the classes
present are test cases, steps, step values, modules, folders and template entities,
and none of them holds a selector, an id, an XPath or a name to find a control by.

That absence is a finding to report, not a silence to pass over. Say it to the
Operator explicitly: this export describes what the tests do and nothing about how
to find the things they do it to.

Because there is nothing in the source to read, **Element Resolution is a Phase of
its own** for this adapter, running after mapping. For a source that carries
locators it is part of mapping instead, in the same reading that recovers sequence.
The Phase structure of a Migration follows the source, and this adapter is the case
that shows it.

Mapping still names the elements it needs. Every element a Step Map row references
is carried forward, by name, for that Phase to satisfy — from the existing Testsigma
project where a screen already matches, and from the Operator where nothing else
can. A row whose elements are unresolved is recorded and blocks assembly rather than
being assembled around.

## Values

Values live in `XTestStepValue` entities, one per parameter, each with a `Value`
string and an undocumented numeric `ActionMode` and `Operator`. In the measured
export all 215 values were non-empty, `ActionMode` took four distinct numeric codes
and `Operator` two. Treat those codes as unexplained until probed; record what you
establish as a Platform Fact rather than guessing at an enum.

**A value is written in a small language of its own.** Actions appear as braced
tokens: `{Click}`, `{MOUSEOVER}`, `{SENDKEYS[OH065M]}`, `{NULL}`.

Normalise a token before counting it: take the action name only, upper-case it, and
drop any bracketed argument. `{Click}`, `{CLICK}` and `{SENDKEYS[OH065M]}` become
`CLICK`, `CLICK` and `SENDKEYS`. The rule is needed rather than tidy — the measured
export spells the same action both ways, 43 times as `{Click}` and 4 as `{CLICK}`,
so counting literal strings splits one action into two and undercounts the commonest
thing the suite does.

Measured, under that rule: 17 literal spellings collapse to 13 action names, the
commonest being `MOUSEOVER` at 53 uses and `CLICK` at 47.

**One value can encode a sequence of several actions, and there is no helper to
open.** `{CLICK}{DOWN}{ENTER}` is three actions in a single value.
`{KEYDOWN[CONTROL]} {KEYPRESS[A]} {KEYUP[CONTROL]} {KEYPRESS[DELETE]} {BACKSPACE}`
is five. This is the second shape of the Composite Step: with a page-object source
the sequence hides behind a method you can go and read, and here it hides inside a
string with nothing to open. Read every value for a sequence of tokens, and express
each token as its own step.

Only 2 of 215 values in the measured export held more than one token, so this is
rare and expensive rather than common: the five-action value is a single row that
silently becomes five steps, and a reader treating values as scalars gets it wrong
with no signal.

**A leading or trailing `*` is a wildcard comparison, and it is a question rather
than a licence.** `*Claim Inventory for Test ID OH065F*` matches loosely, and what
was actually being checked is not recoverable from the export. Raise a question
about what the assertion is meant to establish; do not carry the looseness across.
This is not an edge case: 41 of 215 values in the measured export were wildcard
comparisons, nearly a fifth.

## Enumeration

Two `XTestStep` entities are the same Source Step when they reference the same
`XModule` surrogate. Count distinct referenced modules, not steps and not step
names.

Worked example, from the measured export: 48 `XTestStep` entities referencing 19
distinct modules, a Collapse Ratio of 2.53, with 4 modules used exactly once.

| Source Step (module) | Occurrences |
|---|---|
| `CHIP Fire Property All Tabs` | 7 |
| `CHIP Fire Property Inventory Page` | 4 |
| `TBox Send Keys` | 4 |
| `M&T Inventory` | 4 |
| `TBox Wait` | 3 |
| `CHIP Fire Property Performer Search` | 3 |
| `M&T Overview` | 3 |
| `M&T Org Search \| CHIP` | 2 |

The remaining 11 modules account for 18 steps between them. Note the last row: a
module name can contain a pipe, so it is escaped here and a reader that splits a
row on an unescaped pipe loses the name.

Count values separately from steps, because the element and parameter vocabulary
does not collapse with the step vocabulary: 215 value entities sat behind those 48
steps.

**A data-driven test is a template plus instances.** `TestCaseTemplateDetail` links
a `TestCase` to its `Instances`, each a `TestCaseTemplateInstance` with its own data
source. Enumerate and migrate the template, once, as a parameterised test; the
instances are its data. Treating each instance as a test yields N duplicated tests
that differ only in values, which is the opposite of what mapping is for. The
measured export held 3 templates with 3 instances between them.
