# A Migration pushes, but never by itself

A Migration delivers into the **target project**, and the target is the project
the working copy is attached to — the folder the new tests are written in. No
separate pinning: `attach` already established it, and a Migration that asked
again could be told a different answer than the one its files are bound to.

But **no conversion ever pushes.** `convert` ends where it ends today, at the
Migration Directory and the assembled working copy, committed. Push is a separate
act the Operator triggers, at a moment the Operator picks.

And a Migration usually has **one** Testsigma project — the target. A separate
read-only project to adopt from is a real case but an uncommon one, and every
rule about pushing has to say which of the two worlds it is in.

## Considered Options

Pushing per Conversion was the obvious shape: each test is finished, checked and
committed, so send it. It was rejected on blast radius. Uploads are
application-scoped, and a new upload version makes the server repoint every
referencing step across *every version of that application* — not only the
target. Per-Conversion push spreads that consequence across weeks of unattended
runs, where nobody is present to connect a changed test in some other version to
a Migration that was running at the time. Once, deliberately, with a person
watching, is the only way that consequence is attributable.

Pushing once automatically at the end was rejected for the same reason with a
smaller number attached. The question is not how often the write happens but
whether a person chose the moment.

Making the plugin project-agnostic — never naming a target, leaving delivery
entirely outside the plugin — was rejected because it is what the plugin does
today by accident. `push` appears in exactly one place, `references/adoption.md`,
as a prohibition scoped to a read-only source project. With no target-push story
beside it, that correctly-scoped rule reads as a general one, and a reader
concludes a Migration never pushes at all. An undocumented half of a decision is
not neutrality; it is the other half asserting itself.

Deleting the read-only-source world to get one simple story was rejected too. It
would have removed a fault class outright — source-tenant ids can only reach a
target where two tenants exist — but the case is real, and a plugin that denies a
case its users have does not stop them having it.

## Consequences

**`convert` and `assemble` do not change.** The deliverable is still the
committed working copy. Nothing in the conversion loop gains a network write, and
a Migration remains re-runnable because nothing it did escaped the disk.

**Every push rule names its world.** `references/adoption.md` keeps "Pull, never
push" and gains an explicit scope: it governs a separate read-only source
project. The common case — the target is the only project — is written beside it
rather than left to be inferred from its absence.

**Uploads are the exception that gets stated, not assumed.** An upload push
cannot be confined to the target version, because the working copy lives under
the application and no route takes a version. A Migration may create a new upload
freely, since nothing references it yet. It may add a version to an *existing*
upload only where the Operator says so for that upload. "The Operator agreed to a
push" is not that consent; the consent is per upload.

**The Operator inherits a decision the plugin cannot make, and is told so.** An
earlier draft of this ADR required the versions that would be repointed to be
named before consent was asked for. They cannot be: nothing in the build or the
server maps an upload to the steps that reference it, and the only list that can
be assembled — the tests in the workspace — holds exactly the steps that are *not*
at risk, since the damage lands in the application's other versions.

So the plugin names none of them and says that is what it is doing. Only a person
knows whether another version of the application is in use. A blast radius
reported as empty because nobody could look is the failure this plugin exists to
prevent, arriving at the scale of another team's test run.

**Delivery gains no inventory precondition.** The live preflight already refuses a
binding from the wrong tenant — absent (`TSS1101`) or resolving to a different
entity (`TSS1201`) — because a pulled file carries a content baseline. What the
plugin owes instead is a rule about authoring: an `[id = N]` enters a file only by
pull or by push write-back, never by hand, because a hand-written binding has no
baseline and nothing compares it.

ADR-0012 is unaffected: this says nothing about how many scenarios a Conversion
covers, only that none of them delivers to a tenant.
