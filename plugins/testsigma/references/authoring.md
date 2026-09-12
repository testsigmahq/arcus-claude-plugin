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
expressible is established here. The build has no command that lists verbs and
no schema to read — what it has is a compiler that names what it refuses.

**Build a scratch workspace.** `validate` reads a workspace, and a workspace is
three marker files. Write them by hand; the ids are arbitrary because nothing
offline checks them:

```
project.sigma       project [id = 1] { }
application.sigma   application [id = 2] { }
version.sigma       version "v1.0" [id = 3] { }
```

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

It is one question per compile and there is no way to ask for a list. A stage
that wants "every verb for this category" cannot have it from an install, and
must not read the silence as an absence — `TSF2001` naming a near miss is not
evidence that nothing else exists.

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
        locator = "//div[contains(text(),\"Adult @|number|\")]"
        dynamic = true
      }

  **The sigil is the wire's, and it is the only spelling that compiles here.**
  `@|number|` passes; the format-native `${param.number}` is refused with
  TSF2013. That is backwards from every other position in the format, and it has
  a consequence worth more than the surprise: the sigil is opaque text to the
  compiler, so **nothing checks that a parameter of that name exists**. A typo
  produces a file that validates, pushes, and matches nothing at run time.

  Checking it by hand is per *test*, not per profile, and the difference is not
  pedantic. An element belongs to a screen, not to a profile — it is shared by
  every test that uses it and carries no profile scope of its own. At run time
  the value comes from whichever profile the executing test is bound to. So a
  dynamic element used by two tests needs its column in **both** their profiles,
  and checking one is the phrasing that passes a suite which fails on the second
  test.

  Note what `validate` does and does not give you here, because the two look
  alike and neither is what a reader assumes. A parameter in an ordinary value
  slot is checked for existence **somewhere in the workspace** — every profile's
  columns pooled into one set — so `param.notInAnyProfile` is refused with
  **TSF2021** while a test bound to profile A may reference a column declared
  only in profile B and compile cleanly. Inside a locator there is no check at
  all. Both are weaker than the runtime requirement, by different amounts, and
  the syntax does not say which you are looking at.

  **This is not a locator problem, and only one of the three is silent.** A
  `param` that resolves nowhere **fails the run** — the lookup throws "test data
  not found" — and so does a missing `env`. A missing **runtime** variable is the
  silent one: the marker survives as literal text and the step passes having
  checked nothing. A cross-profile `param` is therefore a run that will
  definitely fail, which is a better reason to catch it offline than the one
  this paragraph used to give. Run
  `${CLAUDE_PLUGIN_ROOT}/scripts/check_profile_refs.py <workspace>` over
  assembled work; it checks each test that declares a profile against that
  profile's own columns. A test declaring none is skipped on purpose — unbound
  `param` is the norm, the profile arriving from a suite or plan, and refusing
  it would flag most of a healthy workspace. A step group's body is out of scope
  for the same kind of reason and not for caution: a `stepGroup` has a `profile`
  attribute of its own, so its references resolve against that rather than the
  caller's, and `override(…)` replaces a value at the call site.

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

An empty block is legal anywhere a step is legal, so put it **where the step
would have gone** — same position, same nesting. A marker collected at the end
of a test loses the one thing it was for, which is showing a reader the point in
the sequence where the test stops matching its source.

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
