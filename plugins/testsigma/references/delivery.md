# Delivering into the Target Project

A Migration produces a working copy and commits it. That is where every
Conversion stops, and it is not where the work ends: the tests have to reach the
project they were written for. **Delivery** is that send, and it is a separate
act from converting.

## The target is the folder, and it is not named twice

The Target Project is the project the working copy is attached to — the folder
the new tests are written in. `attach` already bound the files to it — see *What
`attach` establishes* in `${CLAUDE_PLUGIN_ROOT}/references/authoring.md` — so a
Migration never asks which project it is delivering into. A Migration that asked
again could be told a different answer than the one its files carry, and the
files would win.

## No Conversion pushes

A Conversion ends at the Migration Directory and the assembled working copy,
committed. It does not send anything. Delivery is triggered by the Operator, at a
moment the Operator picks (ADR-0014).

The reason is one write in particular. Pushing a new version of an existing
upload makes the server repoint every referencing step at it, across every
version of the application — not only the version being delivered into. A
consequence that wide has to be **attributable** to a moment a person chose,
because nobody can connect a test that changed in some other version to an
unattended run that happened to be going at the time.

So Delivery is deliberate, infrequent, and watched. Everything below assumes a
person is present.

### A Copilot Run delivers one test

A debug run executes the saved server test, never the local file, so `copilot`
pushes the one test it runs, and every edit it makes during the run (ADR-0016).
That is a Delivery of one test, and nothing in it is exempt from this document:
the dry run, no flags, dependency order, per-upload consent. It fits ADR-0014
because the Operator is present for the whole of it — they start the run and
agree to each push — so every write is attributable to a moment they chose.

## Which project these rules govern

Usually a Migration has exactly **one** Testsigma project: the Target Project it
delivers into. Every rule here is about that one.

A second project sometimes stands beside it — a **read-only source project**
holding hand-written work to adopt from. It is never delivered into.
`${CLAUDE_PLUGIN_ROOT}/references/adoption.md` governs that project, and its
"Pull, never push" is a rule about *it*, not about the target. Where a Migration
has no such project, that rule has nothing to govern.

The two worlds are named every time because their absence is what misleads. A
rule scoped to one project, standing alone with nothing beside it, reads as a
rule about all of them.

## A binding from the wrong tenant

Entity ids are per **tenant**. So a file pulled from the read-only source project
and never re-pulled from the target carries ids that mean something else in the
target, or nothing at all.

`validate` cannot see this. It runs **offline**, against the working copies on
disk: `TSF2023` and `TSF2063` ask whether this workspace declares the thing, never
whether the target holds it. A file in this state validates clean.

The live preflight catches it, which is why Delivery needs no inventory step
beforehand:

- The id is absent from the target application — `TSS1101`, refused.
- The id resolves to a **different** entity — `TSS1201`, refused. A pulled file
  carries a content baseline, and the target entity does not hash to it. For an
  upload this is terminal and no flag is offered, because every upload write
  appends a version.

### The name is not the guard

A name mismatch between the file and the server is `TSS1109`, a **notice**, exit
0. Nothing stops.

For a test or a step group `TSS1109` is worse than harmless: the push
**renames** the server's entity to the file's name and writes the file's steps
over it, because the binding resolves the entity and the name does not.

So the name comparison is the thing that looks like protection and is not. The
content baseline is what refuses a binding from the wrong tenant, one step
earlier.

## How an id enters a file

Every rule in this section and the next is about the Target Project.

Never by hand. An `[id = N]` written by a person carries no content baseline, and
a file with no baseline gets `TSS1111` — a notice, not a refusal — after which
**no comparison runs at all** and binding proceeds on the id alone. That is the
one state where the guard above is absent, and it is reached only by authoring
it.

An id enters a file three ways: a `pull`, a completed push's write-back, or
`pull --adopt-id`.

`--adopt-id` writes the binding and nothing else — no hash. So an adopted file
also carries no baseline, and its next push also meets `TSS1111`. What it cannot
do is bind a foreign id: it runs only where the local file matched an entity in
the **target** by name, and the id it writes was resolved live from the target in
that same command. Adoption is safe from the wrong-tenant trap by construction,
and exposed only to the entity drifting server-side afterwards, until a baseline
exists. A baseline appears on the next `pull --write` of that file, or when a
push completes.

No `pull --write` is required after adopting. The drift it would guard against is
what the dry run below surfaces, at the moment it matters.

## Uploads, the one send that escapes the Target Project

Everything else Delivery sends lands in the version the working copy is attached
to. Uploads do not. They are application-scoped: the working copy sits under the
application directory, no route takes a version, and when a new upload version
lands the server repoints **every referencing step** at it — including steps in
the application's *other* versions. A step somewhere else that pinned that upload
now resolves to bytes this Migration sent.

So the two cases are not one case:

**A new upload is free.** Nothing references it yet, so nothing can be repointed.
Create one and the blast radius is empty by construction.

**A new version of an existing upload is not.** It is the write above, and it
reaches past the Target Project.

### An id-less upload line is always a new upload

An `upload` line with no `[id = N]` is a create, every time. There is no filename
matching, no name matching and no heuristic behind it: if the application already
holds an upload of that name, you get a second one beside it. With `[id = N]` it
is a PUT, and each id-less `version` block under it mints a new version of that
upload.

So the way to bind to an upload the target already holds is to read it, not to
guess at it: `pull uploads --write` against the target application writes a bound
reference file per upload, and the new `version` block goes in the file that came
back. Authoring an upload file by hand and hoping the name matches is how a
Migration leaves a twin behind — the same failure adoption exists to prevent,
arriving at the scale of a file the tests depend on.

### What cannot be listed, and what is said instead

The steps a new upload version would repoint **cannot be listed**. Nothing maps an
upload to the steps that reference it: the build's usages mechanism covers step
groups, test data profiles and elements, and uploads are absent from it.

The one list that *can* be assembled is worse than none. The workspace holds the
tests of the version the Operator is attached to, and those are the steps **not at
risk** — the damage lands in the application's other versions, which no query
reaches. A list drawn from the workspace would read as a survey of the blast
radius while containing none of it.

So the plugin names none of them, and says that is what it is doing. It asks the
Operator for a new version of an existing upload knowing it cannot tell them what
would be repointed, and the Operator decides on that footing. **The consent is per
upload**: agreeing to the Delivery is not that consent, and neither is agreeing to
one upload's version standing for the next.

### The refusals

`TSS1157` — the block is bound and carries a path. A version's bytes cannot be
replaced; put the path in a new id-less block instead.

`TSS1156` — the block is id-less and carries no path. Nothing mints an empty
version.

`TSS1117` — two id-less blocks of one name. A step pins a version by name, and two
of one name resolves to neither.

`TSS1201` — the baseline does not match. For an upload this is terminal: every
upload write appends a version, so a flag could only append while claiming it had
overwritten, and none is offered.

Two more can refuse an upload push, and both are described above rather than here:
`TSS1101`, where the `[id = N]` names no upload in this application — the
wrong-tenant case, and the deleted-upload one — and `TSS1138`, which arrives only
under `--dry-run` and means run it once for real.

### When there is nothing to send

A pushed upload file is the canonical pulled form: the minted id is bound and
`localFilePath` is gone in the same write, so nothing in it offers bytes any more.
Pushing it again sends nothing, and says so — *every version in this file is one
the server already holds, so there is nothing to send*.

Read the sentence rather than the code. The notice code that carries it also
carries three other meanings, one of which is "used by N other tests" — which
never fires for an upload at all. An Operator who looked the number up would find
the wrong one of the four.

## Which kinds a Delivery never sends

The variable pool (`variables.sigma`) and the environment files
(`*.env.sigma`) are **pull-only**. `push` refuses them at
the kind with `TSS1301`, before any credential is read, so this is a property of
the kind and not an outcome of a permission. It is reached two ways — by the
file's declared kind, and by its path, since a project-scoped file sits under no
application marker — so a Delivery that walks paths meets the same refusal as one
that reads models.

The reason is worth carrying, because a reader told only "pull-only" can still go
and build a way to send them back. The server holds these values encrypted and has no
way to recognise ciphertext it has already written. Sending a pulled value back
would encrypt it **a second time** and destroy the secret, with nothing on either
side able to say that had happened.

Which kinds are pull-only is a live judgement made **per kind**, not a property of
being project-scoped or of hanging above the version: uploads were in this set and
left it. So the rule covers these two and generalises in neither direction — a new
kind is established by probing the build, never by reasoning from these.

`${CLAUDE_PLUGIN_ROOT}/references/adoption.md` says what the two files mean and
how they are pulled.

## The flags

Preserve server review before sending local changes. Pull the bound entity,
read the server review, merge it with the local fix, and run `--dry-run` on the
merged file. Never use `--overwrite-remote` to skip this reconciliation.

Deliver shared changes in dependency order: push each dependency before its
callers. A shared step-group change can alter every test that calls it, so run
`--dry-run` for every affected caller before pushing those callers, even where
the caller file itself did not change.

**`--dry-run` runs before every push.** Not where there is reason to doubt the
bindings — before every push. The trap above is precisely the one that supplies no
reason to doubt: the file validates clean, the names look right, and nothing on
disk records which tenant an id came from. It runs the whole preflight against
the Target Project, writes nothing, and renders the exact ledger rows a real run
would write, so the Operator sees what this workspace would send before any
bytes move.

Those rows are what is sent, not what is reached. Where they include a new
version of an existing upload, what that reaches is not among them — see
**Uploads** below, which owns that rule.

It is not a perfect rehearsal. A step whose visual check compares against a local
golden refuses under it with `TSS1138`, because the upload mints the id the
request carries and a dry run mints nothing. Read that as "run it once for real",
not as a fault.

**`--overwrite-remote` is never passed.** It means "the server moved since this
file was reconciled, send anyway". On work a Migration authored, a moved server
means someone edited it in the app, and the answer is to read `pull` first. It is
also what would force a `TSS1201` past the one guard that catches a foreign id.
For uploads it does not exist.

**`--discard-healing` is never routine.** It reverts a server-side heal of an
element, which is a thing to do deliberately and for a named element.

**`--delete` is never passed.** It removes the bound entity *and* the local
file, and a Migration delivers work rather than removing it — a deletion in the
Target Project is the Operator's own act, on an entity they named. It excludes
uploads. Removing a version block from a file deletes nothing either: the block
returns on the next `pull`.

The minimal correct Delivery is `testsigma push <file>` with no flags, after a
dry run of the same.
