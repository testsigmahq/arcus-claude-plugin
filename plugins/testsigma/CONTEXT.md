# Testsigma Migration

Converting an existing automation suite into Testsigma `.sigma` format, over
many sessions and many days, driven by someone who knows Testsigma but does not
necessarily read code.

## Language

### People

**Operator**:
The person running a migration. Knows Testsigma; does not necessarily read code.
_Avoid_: user, developer, tester

### The work

**Migration**:
The multi-day conversion of one source suite into `.sigma`. A Migration is many
Conversions, taken one at a time.
_Avoid_: conversion (a Conversion is one scenario, not the whole job), port,
translation

**Migration Directory**:
The directory holding a migration's state, at `.testsigma/migration/` inside the
source suite's own folder. Living in the source tree means the source repository
versions it, so a migration's state travels with the code it describes rather
than depending on a directory nobody tracks.
_Avoid_: workspace, scratch directory

**Phase**:
A stage of a Migration that blocks the next. Survey is the only one: it blocks
every Conversion, because nothing can be converted before the adapter is chosen,
the snapshot pinned and the vocabulary enumerated. Mapping, element resolution
and assembly are not Phases — they are the steps inside a Conversion, and they
run once per Conversion rather than once per Migration.

A skill calling its own work a *stage* means the step it performs inside a
Conversion, which is why the word survives where the term does not. What makes
something a Phase is blocking the rest of the Migration, and only survey does.

**Conversion**:
The end-to-end work on one source scenario: mapping the Source Steps it reaches,
resolving the elements those steps name, assembling the test, checking it and
committing it. The unit a Migration delivers in, and the unit `convert` performs
exactly one of. A Conversion maps only the Source Steps its own scenario
reaches, so the Step Map fills as Conversions are taken rather than before any
of them are.
_Avoid_: slice, increment, chunk, batch, iteration

**Parked**:
A Conversion set aside because something it needs can only come from the
Operator — an unanswered question, or an element that the source does not carry
and the target project does not already hold. The loop takes the next Conversion
rather than stopping, and a parked one is revisited when the thing it waited on
clears. Parking is what keeps one unanswered question from stalling a Migration.
Residue never parks a Conversion; it assembles as a marker.
_Avoid_: blocked, deferred, skipped

### The material

**Source Step**:
The recurring unit of intent in a source suite, however that suite spells it —
a Gherkin phrasing, an ALM design step, a Tosca module, a page-object method.
_Avoid_: phrasing, action, keyword

**Composite Step**:
A Source Step whose surface implies a different number of actions than it
performs, whether fewer or more. The sequence hides either behind a helper that
the source line names, or inside a value written in a small language of its own.
The defining property is that the source line alone cannot tell you which.
_Avoid_: macro, compound step, wrapper

**Variable Pool**:
The project-scoped set of every variable key the project holds, pulled as
`variables.sigma`. An environment can only put a value over a key the pool
already holds, so the pool is the registry of keys and an environment file is a
list of overrides rather than a short dictionary.
_Avoid_: defaults, globals, the variables

**Mask**:
What a read shows where an encrypted value is: a run of bullet characters, never
the value and never its ciphertext. Any run is a mask — the rule carries no
count — and a mask is handled as the credential it stands for.
_Avoid_: redacted value, placeholder, dots

**Source Adapter**:
The document that tells an agent how to read one source format into Source
Steps. One per format, and the only part of a migration that knows the format.
Prose an agent reads and applies, not a parser: recovering what a source really
does takes judgement that no schema carries. Each one declares three properties
of its format up front — whether the real sequence hides behind a helper layer,
whether the source carries locators, and whether values carry a language of
their own.
_Avoid_: parser, reader, importer

**Collapse Ratio**:
Total source steps ÷ distinct Source Steps. Reported before a migration starts;
a ratio near 1.0 means there is no vocabulary to map.

**Step Map**:
The reviewed mapping from every Source Step to its `.sigma` expression. Built
progressively, one Conversion's worth at a time, and shared by every Conversion
that follows. A row carries the source text,
occurrence count, parameter shapes, the proposed expression, and a status. One
Source Step may map to several `.sigma` steps.

**Element Resolution**:
The act of satisfying the element names a Step Map references — from the target
project, from the source, or by Operator capture. It happens inside a
Conversion, never as a stage of its own. Where the source carries locators they
sit in the files that carry sequence, so resolution and mapping are one reading.
Operator capture is the last resort: a Conversion reaches them only where
neither of the other two can answer, and parks when it does. Which of those two
is consulted first, and which wins where they disagree, are fixed by the
procedure (ADR-0013).

**Residue**:
The Source Steps a migration could not express, each with a stated cause.
An unexpressible step and an unresolved element are distinct causes. No entry is
final: a cause is overturned when the format gains a spelling, or when one is
found that nobody had used, so an entry records the reasoning that produced it
and is revisited rather than treated as closed.
Each entry also carries a **Standing**, which is a gap or a refusal — a
capability the format does not have yet, against a construct declined on
purpose. Both stop a row and only one is temporary, so they are not revisited by
the same thing: a build change can close a gap and can never close a refusal.
It moves in the other direction too: a build that withdraws a spelling a
converted row relied on opens a new entry, a gap where the capability may return
and a refusal where it will not.
_Avoid_: gaps, failures, unsupported

### Verification

**Validity**:
The property that a working copy is legal in the format. Machine-decidable, and
decidable offline. Tenant acceptance is a separate check rather than part of
this one: ADR-0001 orders the five checks by what each can see, and these two
see different things and need different resources. See `references/checks.md`.
_Avoid_: verification, correctness

**Equivalence**:
The property that a converted test does what the source test did. Not
machine-decidable, and not observable by running the test.
_Avoid_: verification, fidelity, faithfulness, correctness, parity

**Divergence**:
A converted step that is valid but not equivalent. Distinct from Residue: a
Divergence was expressed and reported as done, wrongly.
_Avoid_: bug, mistranslation, regression

**Concession**:
A divergence chosen deliberately, because the format has no closer spelling, and
recorded with the platform limit that forced it. The third state between Residue
and Divergence, and in practice the commonest: Residue is work declined, a
Divergence is work whose difference nobody noticed, and a Concession is work
whose difference is known and written down. An unrecorded Concession is a
Divergence; that is the only thing separating them.
_Avoid_: workaround, compromise, approximation

**Target Project**:
The Testsigma project a Migration delivers into — the one the working copy is
attached to, which is the folder its new tests are written in. A Migration has
exactly one, and never asks which it is, because `attach` already bound the files
to it. A second project sometimes stands beside it, read-only, holding
hand-written work to adopt from; that one is never delivered into and is not the
Target Project.
_Avoid_: destination, tenant, the project

**Delivery**:
Sending a Migration's committed working copy to the Target Project. It is a
separate act the Operator triggers, never part of a Conversion, so a Migration
that has converted everything has still delivered nothing until a person says so.
The reason is that one kind of write — a new version of an existing upload —
reaches beyond the Target Project's version, and a consequence that wide has to
be attributable to a moment someone chose.

`push` is the command that performs it and keeps its name. What the term replaces
is *push* as the name of the act, which said what was typed rather than what
happened.
_Avoid_: publish, sync, ship, the push

**Adoption**:
Binding a Step Map row to an entity the target project already held, instead of
authoring a second one. What makes it adoption rather than a guess is that the
existing entity was verified against the same source the row names, by the same
call-chain comparison that guards a row the Migration wrote. An unverified
binding is not an Adoption; it is a row nobody checked, wearing a status that
says someone did.
_Avoid_: reuse, import, linking

**Unit of Work**:
What a check runs against: a distinct Source Step while mapping, an assembled
test while assembling. The two differ because the faults they can carry differ —
a step can mean the wrong thing, a test can hold the right steps in the wrong
order.

**Check Record**:
The record, per unit of work, of which checks ran against it. When a check gains
a capability it did not have, the units checked before it leaves them marked as
not checked against that capability, rather than inheriting a pass they never
earned.
_Avoid_: results, log, audit trail

### What a migration learns

**Platform Fact**:
Something true of Testsigma's own authoring surface that no reading of a source
could reveal. A migration can settle one itself, by probing.

**Value Kind**:
Where a value in a step comes from: typed in, a column of a test data profile, a
value an earlier step stored, an environment variable, a generator, an upload
path. Each slot declares the kinds it will hold, so a kind is what makes an
expression legal in a given slot rather than a property of the value on its own.
_Avoid_: data type, variable, test data

**Verb**:
One step a Catalogue declares: the sentence a tester reads, the slots it takes,
and whether it is deprecated. What a working copy names when it expresses a step,
and the unit the plugin asks the build about rather than writing down.
_Avoid_: template, step template, NLP, action

**Catalogue**:
The set of steps Testsigma can express for one kind of application. Each platform
has its own and they do not overlap, so a suite driving an application whose
platform this build has no catalogue for is refused rather than partly converted.
The refusal is what happens today and not the Standing of it: the missing
catalogues are tracked as work, so as Residue such a stop is a gap and closes
when a catalogue lands. Which catalogues exist is a Platform Fact, established by
probing, and it grows.
_Avoid_: verb list, step library, schema

**Addon**:
A unit that extends a Catalogue past what the installed build ships. A **step
addon** adds a Verb; a **data generator addon** adds a generator behind the
`function` Value Kind. Which of the two a stopped row needs is the whole
difference between two pieces of work, owned by different people and shipped on
different schedules, so a Residue cause reading only "cannot express it" routes
nowhere. A missing Verb and a missing generator look identical from inside a
half-written step and are not the same request.
_Avoid_: plugin, extension, custom step, custom function

**Application Fact**:
Something true of the application under test. Only a person who knows that
application can answer one, so it stays open until answered.
_Avoid_: assumption, unknown, question
