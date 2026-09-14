# 29 — The push story

**What to build:** `push` appears once in this plugin, in `references/adoption.md`, as
a prohibition. Every skill ends at "commit the working copy". A reader who works
through the whole plugin concludes a Migration never delivers to a tenant.

It does. ADR-0014 settles the shape: the target project is the one the working copy is
attached to, no conversion ever pushes, and the Operator triggers delivery at a moment
they pick. None of that is written down anywhere a reader would find it.

This issue writes the missing half, in a reference of its own, and scopes the existing
half so the two stop contradicting each other.

**The two worlds.** A Migration usually has one Testsigma project, the target. It
sometimes also has a separate read-only project to adopt from. `adoption.md`'s
"Pull, never push" is correct for the second and wrong for the first, and today nothing
says which it governs. Every rule the new reference states must name its world.

**The trap the second world carries, and what actually stops it.** Resolution is by
name against the working copies on disk, and the ids sent come from those files'
bindings. Ids are per tenant. An entity pulled from the read-only source project and
never re-pulled from the target carries foreign ids, and `validate` runs offline —
`TSF2023` and `TSF2063` ask only whether this workspace declares the thing.

The live preflight catches it, so there is **no inventory precondition**. A foreign id
absent from the target application refuses with `TSS1101`; one that resolves to a
*different* entity refuses with `TSS1201`, because a pulled file carries a content
baseline and the target entity does not hash to it. Uploads cannot be forced past
`TSS1201` at all. Other kinds can, with `--overwrite-remote`, which is why a Migration
never passes it.

**The name is not the guard, and must not be described as one.** A name mismatch is a
*notice*, `TSS1109`, exit 0. For a test or step group it means the push **renames** the
target entity to the file's name and writes over it, because the binding wins over the
name (ADR-0006). Relying on names would make the trap silent; the baseline stops it one
step earlier.

**So the precondition is about authoring, not sequencing.** The baseline guard needs the
file to have a baseline. A pulled file always does; a file whose `[id = N]` was written
**by hand** never does, and gets `TSS1111` — a notice, not a refusal — after which
binding proceeds on the id alone with nothing compared. Hence the rule: never hand-write
an `[id = N]`. An id enters a file only by pull or by push write-back, or by
`pull --adopt-id`.

`--adopt-id` needs describing precisely, because it is the sanctioned route and it is
not a complete substitute. It writes the binding and nothing else — no hash. So an
adopted file carries no baseline either, and its next push also meets `TSS1111`. What it
cannot do is bind a *foreign* id: it runs only where the local file matched a target
entity by name, and the id it writes was resolved live from the target in that same
command. Adoption is therefore safe from the wrong-tenant trap by construction, and
exposed only to drift afterwards, until a baseline exists. A baseline appears on the
next `pull --write` of that file, or when a push completes.

**Decided: do not require a `pull --write` after adopting.** It was considered, and it
would make the baseline guard live from the moment of adoption rather than from the
first push. It buys only protection against the entity drifting server-side between
adoption and delivery — the wrong-tenant case, which is what the rule exists for, is
already covered by construction. The dry run before every push surfaces that drift at
the moment it matters, and a second sequencing step spread across weeks of a Migration
is one people forget, which is worse than not having it. Do not re-add it without a
drift that the dry run failed to catch.

**The flags.** `--dry-run` runs the whole preflight against the live tenant and writes
nothing, and it runs **before every push** — not only where there is reason to doubt.
The trap above is precisely the one that gives no reason to doubt. It also renders the
exact ledger rows the real run would write, which is how an Operator sees what an upload
push would touch before any bytes move. It is not a perfect rehearsal: a step whose
visual check compares against a local golden refuses under it with `TSS1138`, which
reads as "run it once for real", not as a fault.
`--overwrite-remote` means "the server moved since this file was reconciled, send
anyway" and has no place on work the Migration authored — and it is unavailable for
uploads at all (`TSS1201`, no flag offered). `--discard-healing` reverts a server-side
heal and is never routine. `--delete` removes the bound entity *and the local file*, and
excludes uploads. Removing a version block from a file deletes nothing and the block
returns on the next pull.

**Blocked by:** nothing. Blocks 26.

**Status:** ready-for-agent

- [ ] A reference owns the target-push story, and `adoption.md` links to it
- [ ] `adoption.md`'s "Pull, never push" is scoped to the read-only source project
- [ ] The target is stated to be the attached folder, with no second pinning
- [ ] It says plainly that no conversion pushes, and why the Operator picks the moment
- [ ] Each flag is named with when a Migration may use it, and three with why not
- [ ] The foreign-id trap is described, with the baseline named as what catches it
- [ ] `TSS1109` is described as a notice that renames, never as a guard
- [ ] Hand-writing an `[id = N]` is forbidden, and `pull --adopt-id` named instead
- [ ] `--adopt-id` is described as writing no baseline, and why it is still safe
- [ ] `--dry-run` runs before every push, with the reason it is not doubt-triggered
- [ ] The read-only source project's rules are never stated as though they were general
- [ ] Document tests cover the scoping, so the two worlds cannot drift back together
