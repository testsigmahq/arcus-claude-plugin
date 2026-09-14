# Authoring the target, and what the push refuses

Everything else in `references/` is about reading a source. This is about writing
Testsigma correctly, and about the constraints that only appear when you try.

The rules below have two provenances, and they are not re-established the same
way. Some say what the target can **express** — which verbs exist, whether one is
deprecated, which kinds of value a slot will hold. Those the build itself will
answer, and ADR-0006 says the plugin holds none of them: the section on asking
the build is how each is established. The rest say what an expression **does**
once it runs — that a wait for an absent element succeeds, that a write count is
not evidence of a push — and no catalogue contains those. They were bought by
authoring a real conversion and pushing it to a tenant, and only another push
can revise one.

So neither kind is documentation, and neither is permanent. A fact about what is
expressible is re-established by asking the installed build; a fact about
behaviour is re-established by pushing again. Diagnostic codes are recorded here
and are never spoken to the Operator (`asking.md`).

**These are observations of one CLI build against one tenant.** Re-probe rather
than assuming they still hold — `cli-probe.md` says how, and ADR-0003 says why.

## A deprecated template is a hard error, not a warning

`deprecated: true` on a step template means **a new step may not use it**. The
distinction that catches people is that deprecated is not removed: existing steps
keep working, so reasoning "deprecated still runs" is true for what is already
there and false for anything you create. The push refuses the create outright.

So treat a deprecated template as an authoring error at the moment a row proposes
it, not as something to discover at push time, and keep a replacement for every
one you have met.

**Ask before authoring, rather than meeting the refusal.** `deprecated` is a
field on the verb, and a third of the web surface carries it, so meeting it by
pushing is a choice and not a necessity. Compile the verb and read the answer:
the build reports a deprecated verb as **`TSF2008`**, with its template id in the
message. The section below says how to compile one question.

**The offline check is weaker than the tenant here, which is the trap.**
`TSF2008` is a **warning**. It does not fail a validate, and the tenant refuses
the create anyway. So a session that compiles, sees a warning, and reads the exit
code as the answer will carry the row all the way to a push that refuses it. Read
the diagnostic, not the exit code. This is the inverse of the assumption
ADR-0001's check order rests on — usually the offline check is the strict one —
and it is the only case met so far where it runs the other way.

The measured case is worth recording because the replacement was *better* than
the deprecated verb it replaced: where a source clicked an element
matched by contained text, the replacement iterates every match, clicks the first
whose text contains the value, and throws listing the actual texts it found —
which is the source's semantics, decomposed into an element plus a text filter.

Scope such an element to a container. An unscoped contains-text match will happily
click an outer wrapper that also contains the text.

**Do not choose a verb by its name.** One verb whose name reads as clicking text
is OCR-based: it screenshots, extracts text, and clicks a coordinate. It is not an
XPath match, and nothing in the name says so. Resolve the verb to its
implementation before using it — see
`fault-classes.md#verb-semantics-are-platform-facts-and-are-established-before-they-are-relied-on`.

## Asking the build: one question, one compile

Per ADR-0006 the plugin holds no catalogue, so every fact about what is
expressible is established here. Per ADR-0009, enumerate first: `list verbs` and
`list blocks` answer *what spellings are there*, and `cli-probe.md` says what
each covers. This loop answers the other question — *is this spelling legal in
this slot* — which no enumeration answers, because what the build has for it is
a compiler that names what it refuses.

**Say which catalogue you are asking for.** `list verbs` and `list blocks` answer
from the Web catalogue regardless of what is attached, and say nothing about
which platform the list is for. There is no inference to rely on: the grammar
kinds answer from the catalogue compiled into the build and never open the
marker, so standing inside an attached Unified version and enumerating still
gives Web. Against a Unified
application, pass `--dialect unified`:

    testsigma list verbs --dialect unified
    testsigma list blocks --kind step --dialect unified

Omitting it does not fail quietly for long, and it does not fail cheaply either.
`attach` wrote `applicationType` into the marker, and the working copy compiles
against the catalogue that names, so a web verb written into a Unified
application is refused at `validate` with `TSF2001` — offline, first run, after
the steps are written. The cost is a Conversion's work and a reader sent hunting
for spellings that were never going to resolve.

The flag is read-side and belongs to the grammar kinds, the ones that answer
without reading the workspace at all. Its values are `web` and
`unified`, lowercase, and `web` is the default. A value that is neither prints
the accepted set and **exits 0**, so read the line rather than the exit code.

**Build a scratch workspace.** `validate` reads a workspace, and a workspace is
three marker files under `tests/testsigma/`. Write them by hand; the ids and the
names are both arbitrary because nothing offline checks either — but **all three
markers must carry a name.** A bare `project [id = 1]` is TSF2051, and the build
refuses the whole workspace before compiling anything, so the answer you came
for never arrives:

```
tests/testsigma/p/project.sigma         project "P" [id = 1] { }
tests/testsigma/p/a/application.sigma   application "A" [id = 2] { }
tests/testsigma/p/a/v/version.sigma     version "v1.0" [id = 3] { }
```

The `tests/testsigma/` prefix is not decoration: a tree without it is TSF2051
too. Run `validate` from the workspace root, or point `--root` at it.

An absent `applicationType` on the application marker means web, which is the
server's own default. For unified, write `applicationType = "unified"` inside
the application block — the catalogues do not overlap, so the wrong marker
answers a question about a different platform and looks like an answer.

**Build it outside the suite**, in a scratch directory, and never inside the
source suite or anywhere a working copy lives. The fabricated ids are the whole
trick and they are also the hazard: they name project, application and version
coordinates that exist on no tenant, and a `push` from inside this workspace
would aim them at a real one. This workspace is never pushed, never committed and
never kept.

**Then ask one question.** Write the smallest file that puts the verb and the
value in question into a step, and run `testsigma validate --json`. The
diagnostics answer directly:

| Code | What the message tells you |
|---|---|
| `TSF2012` | the slot refused this kind of value, **and names every kind it accepts** |
| `TSF2016` | the slot takes one of an enumerated set, and names the set |
| `TSF2008` | the verb is deprecated, with its template id |
| `TSF2001` | there is no such verb, with the nearest name it knows |

It is one question per compile. A stage that wants "every verb for this
category" asks `list verbs --category <name>` instead (ADR-0009) — and must not
read this loop's silence as an absence, because `TSF2001` naming a near miss is
not evidence that nothing else exists.

**Record the answer, then delete the workspace.** The answer is a Platform Fact
and goes in `platform-facts.md` with the build identity beside it; the workspace
is a question that has been asked and is worth nothing afterwards. Per ADR-0003,
record at survey which of these codes the installed build produces, so a check
that leans on an absent one is recorded as not covered rather than as passing.

## A value kind, and which slots will take one

A step's slot does not simply take "a value". Each slot declares the **value
kinds** it accepts, and a value's kind is a consequence of how it is written:

| Kind | Written as | What it is |
|---|---|---|
| raw | a literal | typed into the step |
| parameter | `param[...]` | a column of a test data profile |
| runtime | `runtime[...]` | a value an earlier step stored |
| global | `env[...]` | an environment variable |
| random | `random(n)` | a generated string of that length |
| function | a `gen.` call | one of the catalogue's data generators |
| phone_number | `phone[...]` | a provisioned test phone number |
| mail_box | `mailbox[...]` | a provisioned test mailbox |
| upload_path | `upload[...]` | a file the tenant holds for upload |

The slot decides, not the verb and not the value: a slot's `allowedTypes` names
the kinds the server will store there, and a reference of any other kind is
refused however sensible it reads. The kinds are not evenly available — a slot
taking an upload path is rare, where most slots take a literal — so "this worked
in the last row" is not evidence about this one.

This is why a mapping can be correct about the verb and still illegal. A source
value that has to come from somewhere other than the test — a timestamp, an
address, a value an earlier step captured — is expressible only where that slot
allows the kind that carries it. Establish the slot's kinds before proposing the
row, by asking the build — the section above is how.

Where no allowed kind can carry the value, the row is Residue, and its standing
is which of the two the slot's refusal is: a gap where the format may gain the
kind, a refusal where the slot is never going to hold it. Do not reach for a raw
literal instead. Freezing a generated or captured value into a literal is a
Divergence that passes every check — the step runs, and it runs the same input
every time, which is the one thing the source did not do.

The data generators behind the `function` kind are a generated catalogue inside
the CLI build — 125 of them in 22 groups when this was measured, against one
build, so treat the figure as dated rather than as a fact about the installed
one. Establish the one you need by compiling it, the same way as any other
catalogue fact, rather than copying any part of the list here — which is the
staleness `README.md` in `adapters/` warns about, and which ADR-0006 refuses.

## What a correct file looks like

`${CLAUDE_PLUGIN_ROOT}/examples/worked/` is one small workspace that validates
with no errors and no warnings. Read it before authoring the first file of a
kind you have not written.

It carries what no listing can: the nesting, the quoting, `element.name` against
`element["name with spaces"]`, an `if` header without parentheses, a setting in
`[ ]`, an empty `block` as a marker, and a screen's elements ordered by name.
`list blocks` gives a block's grammar; this gives a file's shape, and measured
runs spent six `validate` calls rediscovering it.

## Values, names and layout the validator enforces

- **Environment names need bracket lookup.** An `UPPER_SNAKE` name is not
  identifier-safe, so dotted access fails validation. Emit the bracket form
  always — `env["APP_BASE_URL"]` — including inside interpolation, where it needs
  escaping: `"${env[\"API_BASE_URL\"]}/path"`. Dotted access working for some
  names is a trap, because any sane naming convention produces names it fails on.

- **A dynamic locator has two shapes, and neither is a step setting.** There is
  no placeholder binding: `testsigma list blocks --kind step` prints all fourteen
  step settings and none carries one, which is the listing that ends the search
  rather than extending it.

  **Verb-selected.** The catalogue holds ~65 verbs whose sentence names the
  locator shape and takes the value in the ordinary test-data slot — `Select
  option with label ${test-data} in the radio button group #{ui-identifier}`.
  The element is synthesised at run time and never stored. Find one with
  `testsigma list verbs --all | grep -i "with label\|with text"`.

  **A stored element carrying a parameter reference**, with `dynamic = true`
  beside a locator that embeds one. This is a real, product-supported shape:

      element "Adult Details" {
        locator = "//div[contains(text(),\"Adult ${param.number}\")]"
        dynamic = true
      }

  **Write the format's own spelling, and let the compiler check it.**
  `${param.number}` is the reference; the wire's `@|number|` is refused with
  **TSF2065** — *"a marker the run substitutes, so this text cannot mean
  itself"*. The name is checked: a column that exists validates clean, and a
  typo is refused with **TSF2021**.

  That paragraph said the exact opposite this morning, and the build changed
  under it within the day — sigil accepted and format spelling refused, then the
  reverse, with the parameter name going from unchecked to checked. **Re-probe
  before relying on it.** A stale entry here does not merely lag: a reader
  trusting the old one would have written the spelling now refused and avoided
  the one now required, which is worse than having no entry at all.

  `pull` decodes, so the sigil does not arrive from the server — an element
  stored with `@|number|` comes down as `${param.number}` and round-trips with
  no difference (verified by pushing the format spelling and pulling it back).
  A file holding the sigil was written by hand or pulled by an older build, and
  the current compiler refuses it; rewrite it.

  **The check is workspace-wide, so it is weaker than run time.** TSF2021 asks
  whether any profile in the workspace declares the column, not whether the
  profile that will supply it does. Verifying that is per *test*, not per
  profile: an element belongs to a screen, not to a profile — it is shared by
  every test that uses it and carries no profile scope of its own — and at run
  time the value comes from whichever profile the executing test is bound to. A
  dynamic element used by two tests needs its column in **both**.
  `${CLAUDE_PLUGIN_ROOT}/scripts/check_profile_refs.py` does that pass.

  **Only one of the three reference kinds is silent when it misses.** A `param`
  that resolves nowhere fails the run — the lookup throws "test data not found" —
  and so does a missing `env`. A missing **runtime** variable is the silent one:
  the marker survives as literal text and the step passes having checked
  nothing.

  A `{value}` hole is neither shape. It is literal text, and a locator carrying
  one compiles cleanly and matches nothing — which is how a measured run reached
  a file that looked finished and was inert. Where no verb names the shape and
  no parameter fits, that is Residue with cause `step addon`.

- **Interpolation is legal in few places, and a step's value slot is not one of
  them** (TSF2013). It works where the server keeps the reference inside the
  text: an api step's url, a raw body, a GraphQL variable, a generator argument.
  Everywhere else a value stands alone with its kind recorded in a column beside
  it, and a slot that already has a kind column has nowhere to put a second
  reference inside the same string.

  That is the whole rule, and it explains a pair that otherwise looks arbitrary:
  `storeValue(random(8), …)` pushes and `storeValue("x${random(8)}", …)` does
  not. The bare one has a kind column to live in. It is not about generators —
  `"x${param.prefix}"` fails identically.

- **A per-run unique id is a whole value, never a prefix plus a suffix.** This
  one matters out of proportion to its size, because appending a timestamp or a
  random tail to a fixed prefix is how source suites make ids unique, so a
  migration meets it constantly. The spellings that push are whole-value:
  `random(8)`, or a generator bare such as `gen.date.currentTimestamp()`.

  Where the source genuinely needs `PREFIX` joined to a generated tail, do the
  joining where interpolation is legal — inside an api step's body or url — or
  store the generated part in a runtime variable and let the step that consumes
  it do the joining. Dropping the prefix to make the file compile changes the
  value the test produces, and that is a Concession: it is recorded, with the
  platform limit that forced it, or it is a Divergence.
- **The layout is fixed, and a file in the wrong directory is refused**
  (TSF2050). Ask for it — `testsigma list layout`, or `--json` for a `path` per
  kind. Read `path`; the other fields are its parts, and assembling them is the
  step that goes wrong.

  **Where that command is absent, use the map below rather than experimenting.**
  `list layout` is recent and a build without it is one this plugin still has to
  work against. The general fallback in `cli-probe.md` — compile a candidate and
  read the refusal — does not apply here: there is nothing to compile against,
  so "interrogate instead" means trying directory names, and a measured run
  doing that deleted each candidate between attempts inside the Operator's own
  repository. A copy that goes stale is the lesser fault.

      tests/testsigma/<project>/            project.sigma
        envs/                               *.env.sigma        (project-scoped)
        variables.sigma
        <application>/                      application.sigma
          uploads/                          *.upload.sigma     (application-scoped)
          <version>/                        version.sigma
            tests/       <folder>/          *.test.sigma
            stepGroups/  <folder>/          *.stepGroup.sigma
            tdps/        <folder>/          *.tdp.sigma
            elements/                       *.screen.sigma

  Prefer the probe whenever it answers, and record in `platform-facts.md` which
  of the two the installed build gave you — a row converted against the map is a
  row checked against something that may have moved.

  Three things decide a file's home and a file can miss any of them: the
  directory, the `.<kind>.sigma` sub-extension, and for a foldered kind a folder
  directory carrying `folder.sigma`. They do not always agree with the entity —
  a `screen` lives in `elements/` — which is why this is asked rather than
  guessed. TSF2050 names the home it wanted, so a refusal is usually enough on
  its own.

- **Probe by adding, never by deleting.** Where a convention has to be
  established by experiment, write one candidate file and run `validate`.
  Do not remove directories or files to find out what the compiler wants. A
  measured run looking for the elements directory ran
  `for dir in screens Screens elements Elements element screen; do rm -rf "$dir"; done`
  and then deleted every sibling directory between attempts — inside the
  Operator's own repository, against work an earlier stage had already produced.
  The workspace is the Operator's, not a scratch pad, and a wrong guess that
  only adds a file costs a `validate`, while a wrong guess that deletes one
  costs work nobody can get back. The same rule holds for the tenant: a spelling
  is established with `validate` offline, never by pushing something to see what
  happens.

- **Environments are project-scoped**, not application-scoped: the `envs/`
  directory sits beside the project, not inside the application directory.
- **`attach` takes positional arguments**: project, application, version. There are
  no `--project` or `--application` flags to reach for, and the version may be
  omitted where the application has one.
- **Layout is canonical and the validator enforces it.** Blank lines only at block
  boundaries and never between consecutive plain statements; an empty step-group
  invocation occupies two lines; an api block's children must appear in schema
  declaration order. There is no formatter command — the only way to obtain
  canonical text is `pull --write` after a successful push.

## The first push of a new entity kind, then pull

The server materialises defaults you did not write. After pushing an api step it
added an `advanced` block of four settings, and rewrote a numeric status equality
as a string. Web steps do the same with their own settings.

Left alone, that is a permanent difference between the working copy and the
tenant, and every later round trip reports it. So after the **first** push of a
new kind of entity, run `pull --write` to adopt the canonical form. From then on
the round trip is stable and a difference means something.

## Verify a push with a round trip, never with the write count

A push reporting a handful of writes for a step group of dozens of steps looks
exactly like the fault where steps are silently dropped. It is not: write counts
are **entity-level** operations — create, batch, reorder, baseline — and bear no
relation to the number of steps.

The check that means something is `pull` on the file returning no difference. It is
cheap, it is per-file, and it is the only thing that confirms what the tenant now
holds. Inferring success from a count is reading a number that measures something
else, which is its own fault class.

## A deliberately unconverted region gets a marker, not a silence

An empty inline block — a named container with no body — validates, pushes, and
shows its label in the tenant's own view. That makes it the right representation
for work a Migration has declined: a Residue entry has somewhere to point, and the
gap is visible to whoever opens the test rather than inferable only from the
Migration Directory.

Use it for any region left unconverted on purpose. Do not drop the steps silently,
and do not leave a comment in their place — a comment is invisible in the tenant.

**The label is the whole content of the marker**, so it carries what was needed
and not that something is missing. `Not converted` tells a reader nothing they
could act on; `Needs a step addon: scan a barcode into the receiving field` names
the work and the person who can do it. Write the source's intent in the
Operator's language, then the Cause, using the fixed set in
`migration-directory.md`.

### A block never contains another block

The tenant has no nested blocks. A block holds steps, and a block is not a step,
so writing one inside another is **TSF2079**. The server keeps no nesting for a
block — its id is a number on the block step itself, with no parent pointer — and
the app refuses to build one, so this is the tenant's rule rather than the CLI's.

The refusal is **transitive**: `block { for { block } }` is refused too, because
the inner steps inherit the outer block's parent id and the same guard fires.

What stays legal, so this is not over-corrected: a block on its own, blocks side
by side, a block inside a `for`, `while`, `if`, `else` or `else if`, a loop inside
a block, and an `if` inside a block. Only another block is an unlawful parent —
`else` and `else if` are parents like any other. Reading that list as exhaustive
costs the same as over-drawing the rule: a run avoids a shape it could have used.
Where real nesting is needed, a step group is the construct that nests — a
separate entity with its own file.

The empty block carrying a suffix was checked against a real tenant rather than
reasoned about, because the shape it replaces has a near neighbour that fails: an
empty **group** is TSS1102 at push with `validate` silent beforehand. An empty
block is not the same case. A group invocation must resolve to a step group that
exists on the server, and preflight cannot find one; an empty block resolves to
nothing because it *is* the row — a `BLOCK` with its own id, no children, the long
parenthesised label stored intact, and `pull` reporting no difference.

A
marker therefore has exactly one legal position: it **is** the source step's own
block, standing **where the step would have gone** — same position in the
sequence, empty body. A marker collected at the end of a test loses the one thing
it was for, which is showing a reader the point in the sequence where the test
stops matching its source.

That leaves nowhere to put a nested marker, and nowhere is the right answer: the
need goes **into the label of the block that would have contained it**, as a
parenthesised suffix after the source step's text.

```
block "And the audit record is written (needs a step addon: read the audit
table and assert one row)" {
}
```

The suffix works the same way when the step is *partly* converted, and this is
the case most often missed. A step whose sequence converts except for one action,
or whose value differs from the source's because the platform cannot reproduce
it, is a step a reader sees as fully converted — the block has a body, and
nothing in the file says otherwise. Two measured conversions did exactly that:
one entered a value the source strips characters from, the other generated an id
of a different shape. Both were reasoned about and recorded as open questions,
and both stood in the test as ordinary blocks. A gap the Migration Directory
knows and the test does not is a Divergence, which is the one thing the term
exists to prevent, and recording it elsewhere does not repair it.

So the rule is about the *gap*, not about whether the whole step was refused:
anything the block does not do that its source does carries a suffix, however
small. Write what the step does convert to in the body, and name the remainder
in the suffix:

```
block "Then I validate the receiving grid (needs a step addon: compare all ten
column values against the ASN)" {
  verifyPageHasElement(element.receivingGrid)
}
```

This shape is what the coverage check already reads. It matches a block to a
source step when the label is that step, or that step followed by a parenthesised
qualifier — so the suffix costs no coverage, while a separate marker block
labelled only with the need counts as a block matching no source step *and*
leaves its step accounted for by nothing. One block per source step, always,
whether it is converted, half converted, or not converted at all.

A marker is not a substitute for a Residue entry, and neither is a substitute for
the other. The entry carries the reasoning and gets revisited; the marker is what
a person sees when they open the test and never reads the Migration Directory.
Writing one without the other leaves either a gap nobody can find or a gap nobody
can explain.

## Api blocks, and a Residue cause overturned

**Read the grammar before writing one**: `testsigma list blocks --kind api
--json`, and `--kind verify` or `--kind store` for a sub-block. The prose below
says what an api block can do; only the probe says how to spell it, and the
spellings are not guessable. A condition is a named argument rather than a call,
so a status check is `status(equals = 200)` and a path check is
`bodyPath("$.id", isNotNull = true)`. `verify body` additionally takes at most
one of `path`, `file` or `storedObject`, where naming one replaces the value
compared against — which no amount of trying would suggest. `cli-probe.md` holds
the commands and ADR-0009 the reasoning.

An api block expresses method, url, headers, query, several body kinds, most
common authentication schemes, verification of status, timing, size, body and
**body path**, and storing values out of a response body, header, cookie or
status.

That last capability overturns a Residue cause recorded during the audit. A
structural JSON assertion — this path inside that object has this value — has no
web-side spelling at all: across every catalogue there is no JSON verb. Recorded
as inexpressible, it was inexpressible *in a web test*. In an api block, `verify
bodyPath(...)` expresses it directly.

This is exactly what Residue's reasoning field is for. The entry was right about
the web catalogue, wrong about the format, and a cause is overturned when a
spelling is found rather than being treated as settled. The practical consequence
is large: in the measured estate around 28 of 35 scenarios use api steps and are
therefore convertible, where the web-only reading had written most of them off.

## Element names are global, so collisions must be disambiguated

Element references are unqualified, so a workspace has one namespace for every
element in it. Two page classes in the source can each declare a field of the same
name with genuinely different locators, and both may be needed.

The measured case: an "ok button" on a popup and on a JSON viewer, different
locators, both required. The second cannot reuse the name. So when naming
elements, check the name against everything already in the workspace and
disambiguate by the owning source class — a popup one becomes the popup's ok
button — rather than by a number, which loses the reason.

## Verb semantics established while authoring

These are Platform Facts, recorded here because they were established by reading
the implementation and are reusable across Migrations.

- A verb that verifies text across **all** matched elements iterates every match
  and passes if any one equals the value. That decomposes a source assertion of
  the form "every expected value appears somewhere in this list" into one call per
  expected value. It reads the element's text directly, so the inner-markup
  divergence described in
  `fault-classes.md#verb-semantics-are-platform-facts-and-are-established-before-they-are-relied-on`
  does not apply to it.
- A verb that waits for the page to contain given text is the right mapping for a
  source wait on a locator built from a runtime value: it keeps both the wait and
  its non-default timeout, where a static element cannot express the locator at
  all.
- Waiting for an element to reach "not visible" **succeeds on an element that is
  absent**, and does so quickly. So a wait for a spinner to disappear needs no
  conditional guard around it, and adding one is a step that can only be wrong.

## Credentials found in a source

A real suite carried a hardcoded authentication header and an encoded password,
both committed to its repository.

Never inline such a value into a converted test. Route it to an environment
variable, put the variable name in the working copy and the value in the tenant,
and record in `platform-facts.md` that the value came from the source rather than
from the Operator. Then tell the Operator plainly that the credential is in their
version control history and should be rotated — that is a finding about their
suite, and it is theirs to act on rather than the Migration's to quietly work
around.

Never copy the value into the Migration Directory, a question, a commit message
or a report.
