# 28 — Every command has an owner, or a stated absence

**What to build:** A CLI audit named seven flags the plugin never mentions, and this
issue was written to add them. Most of that premise is now spent: `25` documented
`--dialect`, `26` the upload flags, `27` the `url` flags. What the audit could not see
is the larger version of the same fault, found while implementing `27`.

`references/cli-probe.md` lists seven commands as "the workspace CLI this plugin needs".
One of them, `run`, is mentioned there and **nowhere else in the plugin** — no stage
drives it, no reference describes it, nothing says why. The table's own text accounts
for the others: the first four are what the Migration's stages drive, `list` is how the
platform gate reads a project, and `url` is now described. `run` is unaccounted for.

`attach` has the opposite problem. It is described four times in four files — its
positional arguments in `authoring.md`, the `applicationType` it writes in
`authoring.md`, its `TSS1609` refusal in `cli-probe.md`, its binding of the working copy
to the Target Project in `delivery.md` — and owned by none of them. A reader who wants
to know what `attach` does reads four files and hopes that was all of them.

**The rule this issue keeps.** A flag or command earns a line only where a flow is wrong
or weaker without it, and the line goes in that flow's own document. The tool's help
owns the rest. A table of the whole surface is a second copy of `--help` that goes stale
the way ADR-0009's block count did, and staleness beside correct text is what makes a
wrong line read as checked.

**What that rule leaves, once the spent premise is removed:**

`run` — decide and state. A Migration converts and delivers and never executes: running
needs a tenant, agents and test data that a Migration does not arrange. If that is right,
the table should say so where it names the command, because "the workspace CLI this
plugin needs" currently promises seven and uses six. An unused command listed as needed
reads as one the reader has not found the instructions for yet.

`attach` — give it one owner and leave pointers behind. The fragments are individually
correct, which is what makes the split hard to see.

`list generators` — `migration-directory.md` records a Residue cause "no generator
produces this value" and `map` tells a reader to reach that verdict. No document says how
to check. A reader who cannot enumerate the generators is guessing at a cause that gets
written down as a fact.

With no flags it is an index — a count per group. `--all`, or `--group <name>`, prints
rows, and a row carries the call, a sentence and an example per argument, so the verdict
is answerable from the output rather than from the names. The group is the middle segment
of the call, `gen.<group>.<name>()`, so it is the authoring-side spelling and not an
internal taxonomy.

Two things to state that a reader will otherwise assume wrongly. **Generators are one
catalogue, not two:** `--dialect` is accepted and the output is identical, so the rule
issue 25 established for verbs does not carry over, and a reader who has just learned
that rule will expect it to. And the Residue verdict is **two questions**, not one —
whether a generator produces the value, and whether the slot takes a `function` at all. A
generator written into a slot closed to functions is refused at validate with `TSF2012`,
which is not the generator being absent.

`list verbs --deprecated` — **the concern inverts, and the item changes.** Deprecated
verbs are hidden from `list verbs` by default: 315 rows without the flag, 473 with it,
158 deprecated. The flag includes them rather than filtering to them. So an agent that
enumerates and then picks cannot pick a deprecated verb at all, and the only way to land
on one is to guess a spelling without enumerating — which ADR-0009 already forbids. The
flag needs no line; the default listing is already the protection.

What is missing is not a warning but a **pointer**. `authoring.md` holds a thorough
deprecation rule and `map` — the stage that picks verbs — never mentions it. `map` has no
occurrence of the word. A reader mapping a row learns the rule only by having read
another document first.

Two facts belong in the rule that already exists: that the default listing hides them,
which is what makes enumerate-first protective rather than merely tidy, and that `push`
refuses a new step on a deprecated verb with `TSS1106` while `validate` only warns
(`TSF2008`, exit 0) — so the mapping work is done and wasted by the time the refusal
arrives.

`pull version --prune` — **the hazard is real and is not the one this issue first
named.** An earlier draft said it destroys the `existing/` inventory. It cannot: it walks
`tests/testsigma` only, only kinds the run settled, only files carrying a binding, and
`existing/` is outside the workspace root. A reader told a false hazard stops believing
the true ones, so that framing must not survive.

The true one is that it deletes a working copy for an entity that may still exist. The
lists it compares against carry more soft-deleted rows than live ones, and a soft-deleted
entity reads from here exactly as a removed one does — the command cannot tell them
apart. A Migration has no reason to run it. If one ever does, `--prune` without `--write`
lists what it would delete and deletes nothing, and every row wants reading first.

**Still unearned, and left to `--help`:** `--ignore-refusals`, `pull <file>
--delete-local`, `attach --as`, `list verbs --role`. No flow needs them. If one later
does, it gets its line then.

**Decided: `run` is out of scope by design.** A Migration converts and delivers; it
never executes. Running needs a tenant, agents and test data a Migration does not
arrange, and a converted test that has never run is still the deliverable.

So this writes a sentence, not a section. The table says what it needs `run` for —
nothing — and stops promising instructions that were never coming. Do not reopen this
by adding a `run` procedure; a Migration that ran its own tests would be arranging
state in the Target Project outside a Delivery, which ADR-0014 gives to the Operator.

**Blocked by:** nothing.

**Status:** ready-for-agent

- [ ] The rule is written where a future reader meets it before adding a table
- [ ] `run` is either described or stated to be out of scope, where the table names it
- [ ] The table stops implying a Migration needs a command no stage drives
- [ ] `attach` has one owning description, and the other three sites point at it
- [ ] No fragment of `attach` is left saying something its owner does not
- [ ] `map` or `migration-directory.md` names `list generators` at the generator verdict
- [ ] `map` points at the deprecation rule `authoring.md` already holds
- [ ] The rule records that the default listing hides deprecated verbs
- [ ] The rule separates `validate`'s warning from `push`'s refusal, with both codes
- [ ] `list generators` is named where the generator verdict is reached
- [ ] It says generators are one catalogue, so the verb dialect rule does not carry
- [ ] The generator verdict is stated as two questions, with `TSF2012` for the second
- [ ] The `--prune` hazard is the soft-deleted one, and no document claims it reaches `existing/`
- [ ] The four unearned flags are not documented, and the rule says why
- [ ] No flag table enumerating the whole surface is added anywhere
