# 34 — The variable pool and its environments

**What to build:** The plugin runs `pull variables --write` and `pull env <name-or-id>
--write`, says where the files land, and says they are project-scoped. It says nothing
about what they *mean*, and four of those silences are load-bearing.

**The pool is the key registry, not a list of defaults.** Server-side resolution is one
`coalesce(ev.value, variable.value)` over a LEFT JOIN, so an environment can never add a
key the pool lacks and never remove one — it can only put a value over a key that already
exists. Therefore `variables.sigma` lists **every** key the project has, and an env file
lists **only** what that environment overrides.

The failure this prevents is a session helpfully filling out each env file into a
complete dictionary. That spells one server state as N files, each stale the moment the
pool changes — the second-copy failure `adoption.md` exists to prevent, arriving in a
place `adoption.md` does not look.

**The magnitude belongs in the document, because it is the argument.** A migration of a
585-entity project pulled the version and measured **1550 unresolved environment
references, down to 4** once the pool and five environments were pulled. That is the
`TSF2022` story with a number attached, and it came from a Migration rather than from a
schema.

**Run the two commands unconditionally, and read the notice afterwards. Both.** `pull
version` raises `TSS1431` naming the exact kinds it does not reach — but only where they
are *absent*, and never for an empty pool, which it deliberately declines to nag about.
So the notice alone misses the empty pool, and running the commands alone goes stale the
moment an environment is added server-side. Each covers the other's blind spot.

An empty pool is not refused and not skipped: `pull variables --write` writes a real
`variables { }`. So a **present, empty** `variables.sigma` means *looked, found nothing* —
and an absent one is ambiguous between "nobody ran it" and "the pool was empty", which is
a distinction this plugin refuses to lose elsewhere. Running it unconditionally collapses
the ambiguity into a file.

**Both kinds are pull-only, and the reason is not tidiness.** `push` refuses them by kind
with `TSS1301`, before any credential is read, so this is a kind-level prohibition rather
than a permission outcome. It is reached two ways — by the file's declared kind and by its
path, since a project-scoped file sits under no application marker — so a Delivery that
walks paths meets the same refusal as one that reads models.

The reason to state is that the server has no untouched-ciphertext classifier for
variables, so echoing a pulled value back would encrypt an already-encrypted secret a
second time and destroy it. A reader told only "pull-only" might still build a sync
affordance; a reader told that will not.

**This is newly load-bearing.** Until ADR-0014 the plugin never pushed anything, so
"these kinds are unpushable" needed saying to nobody. `delivery.md` now enumerates what a
Delivery may do and does not exclude them. Note also that the pull-only set is a live
per-kind judgement and not a property of non-version kinds — uploads were in it and left —
so the rule must not be written in a way that invites generalising in either direction.

**A masked value is any run of bullets, never a length.** An encrypted value pulls as a
sentinel and never as ciphertext, precisely because nothing will ever send it back. The
product writes eight; the recogniser matches any run, because a file holding four is the
same leak as one holding eight and a guard matching on length waves the other through.

`fault-classes.md` already forbids a credential found in a *source* from reaching a
question, a fact file or a commit message. The same hazard exists on the target side and
is worse there, because a mask looks like a value rather than like a secret. `TSS1116` is
the precedent — the push refusal for a test-data cell holding the sentinel, whose own
words are that a run of bullets is what a read shows where a secret is, not the secret.

**Blocked by:** nothing.

**Status:** ready-for-agent

- [ ] `adoption.md` says the pool holds every key and an env file only its overrides
- [ ] It says not to complete an env file from the pool, and why that is a second copy
- [ ] The 1550-to-4 measurement is given as the argument for pulling them
- [ ] Survey runs both commands unconditionally rather than on a condition
- [ ] It also surfaces `TSS1431`, and says what each of the two catches that the other misses
- [ ] A present, empty `variables.sigma` is stated to mean "looked, found nothing"
- [ ] `delivery.md` excludes both kinds from a Delivery, citing `TSS1301`
- [ ] It gives the double-encryption reason rather than only the rule
- [ ] It says the pull-only set is per kind and has changed, so nothing generalises it
- [ ] A masked value is defined as any run of bullets, with no length in the rule
- [ ] The masked value is covered by the rule that keeps a credential out of the record
- [ ] A document test holds the mask rule, so a length cannot be reintroduced
