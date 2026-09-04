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
| `attach`, `pull`, `push`, `validate` | The workspace CLI this plugin needs | Yes |
| `test`, `sprints`, `projects`, `modules` | The other Testsigma CLI, which authors individual tests | **No** |

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

**A flag that is absent means the check is absent.** A stage that relies on it
records that check as **not covered** rather than as passing. This is the whole
point of probing: the dangerous failure is not a missing feature, it is a report
that a check passed when nothing ran.

## Fourth: notice when it changes

Compare the recorded build against what is installed now. If they differ, say so
before doing any work, and mark every Unit of Work checked under the old build as
not checked against any capability the new build has gained.

This is not theoretical. A fault class that a person caught by eye became an
automatic refusal in the CLI inside about a day. Work converted before that change
had never been checked for it, and nothing would have said so.
