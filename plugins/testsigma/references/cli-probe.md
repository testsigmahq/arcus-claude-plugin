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
| `attach`, `pull`, `push`, `validate`, `run`, `url`, `list` | The workspace CLI this plugin needs | Yes |
| `test`, `sprints`, `projects`, `modules` | The other Testsigma CLI, which authors individual tests | **No** |

Those seven are the whole dispatch, and the first four are only the ones the
Migration's stages drive directly. Telling the two programs apart needs any one
of the seven, but do not read the four as the surface: `list` is how the platform
gate below reads what a project holds, and a probe that never looked for it
concluded the command did not exist.

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

## Fifth: notice when it changes

Compare the recorded build against what is installed now. If they differ, say so
before doing any work, and mark every Unit of Work checked under the old build as
not checked against any capability the new build has gained.

This is not theoretical. A fault class that a person caught by eye became an
automatic refusal in the CLI inside about a day. Work converted before that change
had never been checked for it, and nothing would have said so.
