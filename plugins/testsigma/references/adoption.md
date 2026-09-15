# Adopting work the project already holds

A target project is not always empty. A team often converts part of a suite by
hand before a Migration starts, and that work is the most valuable thing in the
project: someone decided what each step meant, and a person can be asked why.

**Adoption** is taking an entity the project already holds and binding it to the
Step Map row whose Source Step it expresses, instead of authoring a second one.

Without it a Migration hands back a project with two of everything and no way to
tell which is live — the same failure the element rule names, arriving at the
scale of whole tests and step groups rather than single controls.

## The inventory comes first, or none of this is real

Every rule here compares against what the project holds, so what it holds must be
on disk before mapping begins. Nothing may be concluded from memory of a tenant.

    testsigma pull version --write
    testsigma pull uploads --write
    testsigma pull variables --write
    testsigma pull env <name-or-id> --write        # once per environment

run from the working copy's directory, write a working copy of what the project
holds. `pull version` is not the whole inventory: it writes every entity the
*version* holds, and three kinds hang off coordinates above it. Uploads are
application-scoped (`Upload.applicationId` is their only scoping column, so one
upload serves every version); environments and the variable pool are
project-scoped. There is no `list environments`, so the Operator names the
environments — an inventory missing the pool and the envs leaves every
environment reference resolving to nothing (TSF2022) and makes the project look
emptier than it is, which is the second-copy failure this section exists to
prevent. Put them under `.testsigma/migration/existing/` and commit them
with the rest of the Migration's state.

`pull version` has a `--prune`, and a Migration has no reason to run it. It
deletes a *working copy* whose entity the version did not return — never anything
under `existing/`, which sits outside the workspace root it walks. The hazard is
narrower and worse than that: a **soft-deleted** entity reads from here exactly
as a removed one does, and the command cannot tell them apart. So it deletes the working copy of something that
may still exist in the application, on evidence that cannot tell the two apart.
Where one is ever run, `--prune` **without `--write`** lists what it would delete
and deletes nothing, and every row wants reading before the second run.

They are **evidence, not working copies to edit**. Their value is that they say
what the project holds at the snapshot the Migration started from, and an edited
one has stopped saying that. A Migration authors under the suite's own test
directory and never under `existing/`.

## The pool is the key registry, and an environment only overrides

`variables.sigma` and the `*.env.sigma` files do not say the same kind of thing.
The server resolves one reference by taking the environment's value where it has
one and the pool's otherwise, over a join that starts from the pool. An
environment **cannot add a key the pool does not already hold**, and cannot take
one away. So `variables.sigma` lists **every key** the project has, and an
environment file lists **only** what that environment overrides.

Read an environment file as a short list, then, rather than as an incomplete one,
and **never complete an environment file from the pool**. Filling each one out
into a whole dictionary spells one server state as several files, every one of
them stale the moment a key is added to the pool — the same second copy this
reference exists to prevent, arriving in the one place it was not looking.

Pull both **unconditionally**. `pull version` raises `TSS1431` naming the kinds
it does not reach, but only where they are absent, and never for an **empty
pool**, which it declines to nag about; and a run that pulled the envs once goes
stale the moment someone adds one server-side. The notice and the commands each
catch what the other misses, so a Migration does both.

An empty pool is neither refused nor skipped: `pull variables --write` writes a
real `variables { }` file. A present but empty `variables.sigma` therefore means
*looked, found nothing*, where an absent one cannot be told from nobody having
run it.

What this is worth is measurable. A Migration of a 585-entity project pulled the
version and counted **1550** unresolved environment references (TSF2022). Pulling
the pool and the project's five environments left **4**.

Neither kind is ever sent back — see *Which kinds a Delivery never sends* in
`${CLAUDE_PLUGIN_ROOT}/references/delivery.md`.

## The bytes an upload holds, and what they are evidence of

`pull uploads --write` says an upload exists and what it is called. It does not
produce the file. Where the question is what the bytes actually are — whether the
fixture this project holds is the one the suite feeds its steps — `url` fetches
them:

    testsigma pull uploads --write                       # first, and in the same sitting
    testsigma url upload "invoice.pdf"                   # the link, and the version it is for
    testsigma url upload 512                             # by id, where a name matches more than one
    testsigma url upload "invoice.pdf" --output existing/uploads/

It prints the upload with its id, the version it resolved, the link, and how long
that link lasts. `upload` is the only kind it takes: every other entity's content
is already in the workspace, so there is nothing to fetch.

The order matters, and so does the sitting. **`url` reads this workspace, not the
tenant.** The version it signs is the file's newest — its first version block —
and `--version "<name>"`, which is how any other version is chosen, is matched
against the file's blocks too, never against the server's. A name the file does
not hold is `TSS1425`, and the refusal lists the names it does. That is deliberate: the workspace was reconciled against a particular
version, and signing whatever is latest would hand back bytes the workspace never
named.

What follows has to be said out loud. Pull on Monday, someone adds a version on
Tuesday, run `url` on Wednesday, and you get Monday's bytes — correctly, and the
output says nothing about a newer version existing. Meanwhile every step
referencing that upload was repointed to Tuesday's the moment it landed
(ADR-0014). So a file fetched from a stale workspace is evidence of something no
part of the target still runs.

Two things keep it honest, and both are cheap. Pull immediately before fetching,
because the pull is the only one of the two that re-reads the tenant. And
**record the version name beside the bytes** — `url` prints it on its first line.
Evidence whose version is recorded stays true however old it gets; a bare file
quietly becomes a claim about the present that nobody checked.

Fetched bytes go under `existing/` and take its rule unchanged: evidence, never
edited. `--output` writes exactly the stored bytes and touches no `.sigma` and no
baseline, which is what makes filing them there sound. Given
a directory it uses the server's own name for the file, and a trailing separator
is how you name a directory that does not exist yet.

`--force` overwrites a file already sitting at that path, and means nothing else —
it does not reach the fetch. Without it an existing file stops the download
untouched, and `TSS1426` gives the reason in its own words: a download is the one
thing this CLI writes that it cannot write again from the workspace, so the file
it would land on is yours. `--force` with no `--output` is refused
rather than ignored.

The refusal a Migration actually meets is `TSS1407`: the Target Project holds the
upload and this workspace holds no reference file for it, which the exit closes by naming
the pull that would create one. `TSS1406` is the tenant not having it at all,
`TSS1402` a name matching more than one, and `TSS1425` a version name the file
does not hold, listing the ones it does.

The link itself is a presigned object-store URL, and it is **not single-use**:
anyone holding it can fetch until it expires. It carries no credentials for the
project — the signature is the whole authorisation — so it is safe to paste in the
sense that it **cannot open the tenant**, and unsafe in the sense that it is an
**unauthenticated** link to a real file until it expires. Treat it as the file,
not as a reference to it.

How long it lasts is a property of the build, so read it rather than assume it:
the command prints the validity, and `--json` carries `expiresInSeconds` as a
number so nothing has to parse the URL.

`url` performs **no writes through the API**: it resolves a version and follows a
redirect, and mints nothing. What a tenant records server-side is not visible from
here, so that is the whole of the claim.

`existing/` is not one of the Migration Directory's nine files and survey does
not create it when there is nothing to pull. Its absence means the project was
empty, or that nobody looked — which is why survey records which of the two.

## Adoption is read-only against the source project

**This section governs a read-only source project, and only that one.** It says
nothing about the Target Project, which a Migration does deliver into —
`${CLAUDE_PLUGIN_ROOT}/references/delivery.md` owns that, and owns the rule about
which project is which.

Pull, never push. A project holding hand-written work is one a team depends on,
and a Migration's first act against it must not be a write. Where the Operator
names a project as read-only, that is absolute and covers every subcommand that
writes: `push`, `push --delete`, `push --overwrite-remote`, and attaching.

Convert into a project of the Migration's own, and adopt from the existing one by
reference. If the two must eventually be one project, that is a merge the
Operator performs deliberately, once, with both halves finished and checked —
never a side effect of a conversion run.

## An adopted row

A row whose Source Step the project already expresses is `adopted`. Its Expression
cell names the entity on a line of its own:

    Adopted: stepGroup "Search the menu" — verified against MenuPage.searchMenu

The prefix is fixed for the reason `Concession:` and `Kind:` are: the reviewer's
question is "show me everything this Migration did not write", and a fixed prefix
makes that a sweep rather than a reading.

`adopted` is a status and not a kind of `reviewed`, because the two answer
different questions. `reviewed` means a person decided how to express this step.
`adopted` means a person decided it was already expressed. A resume counting
*reviewed n of m* must not report adopted rows as work still to do, and a reviewer
asking what this Migration actually produced must not be shown them either.

**An adopted row is still assembled.** The scenario needs a step where its Source
Step falls, and that step calls the adopted entity. Adoption removes the
authoring, not the step — so coverage is unaffected, and a scenario with adopted
rows has exactly as many blocks as one without. A row that skipped assembly would
be a silent hole of precisely the kind an empty marker block exists to prevent.

## Verify before adopting, never after

A hand-converted step drops actions the same way a generated one does, and the
drop is inherited by every scenario that adopts it. Adoption is the moment to
find that, because after it the row is trusted and nothing downstream re-reads the
source.

So run the call-chain comparison against the pulled working copy, with the Source
Step's implementing symbol:

    python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_call_chain.py \
      --source-root <the suite> --symbol <Class.method> \
      --block <a fragment of the entity's label> \
      .testsigma/migration/existing/<the pulled file>

This is the same check that guards a row the Migration wrote, pointed at a row it
did not. It has to be: an adopted row and an authored one are read identically by
everything after mapping, so they must have cleared the same bar to get there.

Three outcomes, and the third is the one that matters:

- **It agrees.** Adopt the row and record the symbol it was verified against.
- **It cannot compare** — exit 2, no symbol to resolve, a source with no
  implementation behind it. Adopt only on a person's reading, and say in the
  Expression cell that the check could not run. An unverifiable adoption is a
  decision, and one recorded as verified is a lie the next session inherits.
- **It disagrees.** Do not adopt, and do not quietly author a replacement either.
  The existing entity is live: something runs it, and a team believes it covers
  this step. Put the difference to the Operator as an open question, naming the
  actions the source performs that the entity does not.

That last case is why adoption cannot be a bulk operation. Every disagreement is
a fact about the project the Operator owns, and a run that resolves them by
itself has overwritten their judgement with its own.

## Matching, and what a near match means

Match on what the entity does, not on what it is called. A name is how a team
found an entity again, and two teams converting the same step name it two
different things.

Where a name nearly matches and the check disagrees, that is evidence of a
*different* step, not a broken one. The strong case is the opposite pairing: an
entity whose name says nothing and whose actions match exactly.

Where nothing matches, the row is ordinary work. Adoption is an optimisation on
the rows it fits and never a stage everything must pass through.
