# Probing the CLI

Every stage of a Migration leans on the `testsigma` CLI, and what that CLI checks
grows over time. ADR-0003 says probe it and never pin a version. This is how.

Do this once at survey, record the result in `migration.md`, and re-check it at the
start of every later session, because the answer has a date on it.

## First: is this even the right tool?

Two different programs are called `testsigma`, and only one of them can run a
Migration. Confusing them is not a hypothetical: on the machine this plugin was
built on, the binary first on `PATH` was the wrong one.

Run the CLI's help and look at the command list.

| The help lists | What it is | Can it run a Migration? |
|---|---|---|
| `attach`, `pull`, `push`, `validate`, `run`, `url`, `list` | The workspace CLI, by its whole dispatch | Yes |
| `test`, `sprints`, `projects`, `modules` | The other Testsigma CLI, which authors individual tests | **No** |

Those seven are the whole dispatch, and the first four are only the ones the
Migration's stages drive directly. Telling the two programs apart needs any one
of the seven, but do not read the four as the surface: `list` is how the platform
gate below reads what a project holds, and a probe that never looked for it
concluded the command did not exist. `url` fetches the bytes an upload holds —
`${CLAUDE_PLUGIN_ROOT}/references/adoption.md` describes it.

**`run` is here to identify the program, and for nothing else.** A Migration
converts and delivers and **never executes** a test. Running one needs a tenant,
agents and test data that a Migration does not arrange, and a converted test that
has never run is still the deliverable. It is named here because the dispatch is
how the two programs are told apart, not because a stage reaches for it. A
Migration that ran its own tests would also be arranging state in the Target
Project outside a Delivery, which ADR-0014 gives to **the Operator**.

**One exception, and it is not `run`.** A delivered test gets one Copilot Run
(ADR-0016): `test debug` executes it on the execution agent on the Operator's
machine, with the Operator watching and deciding every edit. No Conversion
executes anything, and `run` stays out of scope. Only `copilot` drives
`test debug` and `agents list`, and it says how; a build whose help lists no
`test debug` has no live run, and the delivered tests are recorded as not
covered by one.

`attach` is the one command whose effects are felt everywhere later, and
`${CLAUDE_PLUGIN_ROOT}/references/authoring.md` describes what it establishes.

**Do not answer this by writing down the surface.** A command or a flag earns a
line here where a flow is wrong or weaker without it, and the line belongs in
that flow's own document rather than in a table. Everything else is the tool's
help, which is always current. A table of the whole surface is a second copy of
`--help` that goes stale the way this reference's own block count did — and a
stale line beside a correct one is what makes the wrong one read as checked. So
several flags this plugin never mentions are omitted deliberately: no flow needs
them, and one that later does will name it then.

If the help shows the second surface, stop. Tell the Operator that the Testsigma
command-line tool installed here is the one for writing individual tests, not the
one that converts a suite, and that the right one has to be installed before a
Migration can start. Do not proceed with the wrong tool: it will accept some
commands and mean different things by them.

Where both exist, the Operator may have to point at the right one explicitly.
Record which program was used, not just that one was found.

## Second: record the build

**The workspace CLI has no `--version`.** Asking for one returns an error, and its
package version reads `0.0.0`, so a version string is not an identity. Record
instead:

- the resolved path of the program that was run
- if it is a local build from a checkout, the commit that checkout is at
- the date of the probe

That combination is the build's identity. A Migration that says "version 0.0.0" has
recorded nothing.

## Third: record what this build checks

There is no command that lists diagnostics, so the capability signal is the help
surface itself. Record the commands and flags the help lists, verbatim, in
`migration.md`.

Read specific flags as evidence of specific checks:

| Seen in help | What it means is available |
|---|---|
| `push … --dry-run` | Preflight can run without writing anything |
| `push … --overwrite-remote` | A content-baseline check exists, and can be overridden |
| `push … --discard-healing` | The build can tell that an element was healed on the server |
| `pull … --adopt-id` | Identity bindings can be adopted without rewriting a file |
| `validate` | Working copies can be compiled and checked offline |

**The help surface cannot show a new rule inside an existing command.** A check
often arrives that way rather than as a new flag — the fault class below became a
stricter `validate`, and `validate` was in the help before and after. Recording
the help verbatim lets a later session diff it, which catches a new command or
flag and nothing else. So the identity of the build, not its help surface, is
what says a check may have been gained: if the build differs, treat every
capability as possibly new and mark earlier work as not checked against it.
Record any diagnostic a build emits that was not seen before, in
`platform-facts.md`, since that is the only direct evidence of a rule that
tightened.

**A flag that is absent means the check is absent.** A stage that relies on it
records that check as **not covered** rather than as passing. This is the whole
point of probing: the dangerous failure is not a missing feature, it is a report
that a check passed when nothing ran.

## Fourth: record which platforms this build can write

A working copy is written against one catalogue, and the marker's
`applicationType` says which. This build has two — `WebApplication` and
`Unified` — and the rest of the server's `ApplicationType` enum is absent on
purpose rather than defaulted to Web, because each platform's steps occupy a
template-id block of its own and the blocks do not overlap. An application on an
absent platform is refused at `attach` with **TSS1609**, and mapping it to the
Web catalogue instead would attach and then fail every pull with TSS1410,
reading as a hole in the Web catalogue rather than as the wrong platform.

So the set matters at survey, before any row is converted, and it is a property
of the build rather than of this plugin. Establish it, in this order, and record
the answer in `platform-facts.md` with how it was established:

- run `testsigma list applications` for the target project. It prints each
  application with its type, which is what says whether the one the Operator
  named is convertible at all.
- where the project is not reachable yet, the refusal text is the next best
  evidence: `attach` names the type it was given and the types it writes.
- failing both, record the two above as the set *this reference last measured*,
  with the build identity beside it, and never as a fact about the installed
  build.

**The two catalogues barely overlap, so which one answered is not a detail.**
Roughly seven of every eight verb names in the larger catalogue are absent from
the smaller one, and the verb a reader reaches for first is among them. Recording
that web and unified are both writable and stopping there reads as though the
choice were administrative. It decides most of the vocabulary.

The figures behind that, as **this reference last measured them**, against
`testsigma-cli` at commit `2477ab0`: web 315 verbs in 27 categories, unified 110
in 20, 42 names in both, and `click(` web-only. They are here to give the
paragraph above a size, not to be relied on — a build that adds a verb makes them
wrong, and the rule this section opened with applies to them as much as to the
platform set. Establish your own and record them in `platform-facts.md`.

Which catalogue answers is chosen by a flag and never inferred. `list verbs` and
`list blocks` read Web unless told otherwise, even inside an attached Unified
version, because the grammar kinds answer from the catalogue compiled into the
build and never open the marker. So enumerate a Unified application with
`--dialect unified`, and record beside the counts which dialect produced them: a
count with no dialect beside it is a number nobody can re-establish.

Enumerating the wrong one is not caught at enumeration. It is caught at
`validate`, once the steps are written —
`${CLAUDE_PLUGIN_ROOT}/references/authoring.md` says what that costs.

The flag belongs to the grammar kinds — `verbs`, `generators`, `blocks` and
`layout` — though `layout` answers identically for both today. A tenant read such
as `list applications` parses it and then ignores it, which is worth knowing
precisely because nothing complains. A value other than `web` or `unified` prints
the accepted set and **exits 0**, so read the line rather than the exit code.

A platform absent from the set is a **gap** in the Residue sense and not a
refusal: the format's owners track the three missing catalogues as work still to
do, so a build change can close one, and recording it as permanent would tell a
later session never to look again. What is permanent is only that no file can be
written for a platform whose catalogue does not exist yet. Treat it the way a
missing check is treated — recorded, not assumed — and re-establish it when the
build changes, because a catalogue arriving is exactly the kind of growth
ADR-0003 exists for.
The code belongs here and in the Migration Directory; the Operator hears which
platforms can be converted, never a diagnostic.

## Fifth: ask the build what it can say

Two commands enumerate the format. Run them before composing anything, and
record in `platform-facts.md` that this build answers them.

    testsigma list verbs                     every category, with counts
    testsigma list verbs --category <name>   the verbs in one
    testsigma list verbs --all

    testsigma list layout                    where each entity kind's file lives
    testsigma list layout --json             a `path` per kind

    testsigma list blocks                    every block kind, and what it contains
    testsigma list blocks --kind <name>      its attributes, sub-blocks and calls
    testsigma list blocks --kind <name> --json

`list verbs` covers steps a web test speaks. It does **not** cover a block's
interior: a test's calls are the catalogue, so an api step's body hangs off the
step-body table rather than off any entity kind, and `list verbs --category api`
is refused because no such category exists. That refusal is not evidence that
api steps are unexpressible. It is the wrong question, and `list blocks` is the
right one.

Prefer `--json` when building a step. It returns the subtree recursively with
each call's arguments inlined, so one invocation answers what the text form
takes several to cover.

**Enumerate first, then compile to confirm.** A compile answers whether one
spelling is legal; these answer which spellings exist. Composing a candidate and
running `validate` to find out whether it was right is only sound once the list
has been read — before that it is guessing, and guessing against a validator is
slow, looks like progress, and is how a conversion spends hundreds of calls
producing nothing. ADR-0009 records the measurement.

A build that does not answer these is still workable: fall back to ADR-0006's
one-question-at-a-time interrogation, and record that the probe was absent rather
than that the format lacks the capability. Absence of a probe is absence of
evidence.

## Sixth: notice when it changes

Compare the recorded build against what is installed now. If they differ, say so
before doing any work, and mark every Unit of Work checked under the old build as
not checked against any capability the new build has gained.

This is not theoretical. A fault class that a person caught by eye became an
automatic refusal in the CLI inside about a day. Work converted before that change
had never been checked for it, and nothing would have said so.

**A differing build may also have withdrawn something**, and that direction is
the one that costs work: a verb removed or a slot that stops accepting a kind it
used to turns a converted row into a row the build will reject.

**What this comparison cannot see is what changed.** It reports that the
identity differs and nothing more: there is no command that enumerates what a
build declares, so the Catalogues, Verbs and accepted Value Kinds of the old
build and the new one cannot be set side by side. ADR-0008 is the decision not
to try, and its reason is that the response is the same whichever direction the
build moved.

**So the recorded Platform Facts go stale rather than void.** Do not delete them
and do not trust them: each one is re-probed at the moment it is
next relied on, and the answer replaces the recorded one. Voiding the lot is the
obvious alternative and is wrong, because a fact here is settled one question at
a time — there is no bulk re-establish to run — so wholesale voiding throws away
answers that are probably still true and cannot be recovered in one pass. Mark
the recorded build beside them as superseded so a later reader knows which
answers are awaiting confirmation.
