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
The multi-day conversion of one source suite into `.sigma`.
_Avoid_: conversion, port, translation

**Migration Directory**:
The directory holding a migration's state, at `.testsigma/migration/` inside the
source suite's own folder. Living in the source tree means the source repository
versions it, so a migration's state travels with the code it describes rather
than depending on a directory nobody tracks.
_Avoid_: workspace, scratch directory

**Phase**:
A stage of a migration that blocks the next: extraction, mapping, assembly.
Element Resolution is a Phase of its own only where the source carries no
locators; where it carries them, resolution is part of mapping.

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
once per migration; scenarios assemble from it. A row carries the source text,
occurrence count, parameter shapes, the proposed expression, and a status. One
Source Step may map to several `.sigma` steps.

**Element Resolution**:
The act of satisfying the element names a Step Map references — from source
page objects, from the tenant, or by operator capture. Whether it is a Phase of
its own is a property of the source, not of the migration: a page-object or
object-repository layer carries locators in the same files that carry sequence,
so resolution and mapping are one reading; an export that carries no locators
leaves nothing to read and forces a separate phase after mapping.

**Residue**:
The Source Steps a migration could not express, each with a stated cause.
An unexpressible step and an unresolved element are distinct causes. No entry is
final: a cause is overturned when the format gains a spelling, or when one is
found that nobody had used, so an entry records the reasoning that produced it
and is revisited rather than treated as closed.
_Avoid_: gaps, failures, unsupported

### Verification

**Validity**:
The property that a working copy is legal in the format and the tenant accepts
it. Machine-decidable.
_Avoid_: verification, correctness

**Equivalence**:
The property that a converted test does what the source test did. Not
machine-decidable, and not observable by running the test.
_Avoid_: verification, fidelity, faithfulness, correctness, parity

**Divergence**:
A converted step that is valid but not equivalent. Distinct from Residue: a
Divergence was expressed and reported as done, wrongly.
_Avoid_: bug, mistranslation, regression

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

**Application Fact**:
Something true of the application under test. Only a person who knows that
application can answer one, so it stays open until answered.
_Avoid_: assumption, unknown, question
