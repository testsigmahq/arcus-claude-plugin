# Authoring the target, and what the push refuses

Everything else in `references/` is about reading a source. This is about writing
Testsigma correctly, and about the constraints that only appear when you try.

Each rule below was established by authoring a real conversion and pushing it to a
tenant, not from documentation. Diagnostic codes are recorded here and are never
spoken to the Operator (`asking.md`).

**These are observations of one CLI build against one tenant.** Re-probe rather
than assuming they still hold — `cli-probe.md` says how, and ADR-0003 says why.

## A deprecated template is a hard error, not a warning

`deprecated: true` on a step template means **a new step may not use it**. The
distinction that catches people is that deprecated is not removed: existing steps
keep working, so reasoning "deprecated still runs" is true for what is already
there and false for anything you create. The push refuses the create outright.

So treat a deprecated template as an authoring error at the moment a row proposes
it, not as something to discover at push time, and keep a replacement for every
one you have met. The measured case is worth recording because the replacement was
*better* than the deprecated verb it replaced: where a source clicked an element
matched by contained text, the replacement iterates every match, clicks the first
whose text contains the value, and throws listing the actual texts it found —
which is the source's semantics, decomposed into an element plus a text filter.

Scope such an element to a container. An unscoped contains-text match will happily
click an outer wrapper that also contains the text.

**Do not choose a verb by its name.** One verb whose name reads as clicking text
is OCR-based: it screenshots, extracts text, and clicks a coordinate. It is not an
XPath match, and nothing in the name says so. Resolve the verb to its
implementation before using it (`fault-classes.md`).

## Values, names and layout the validator enforces

- **Environment names need bracket lookup.** An `UPPER_SNAKE` name is not
  identifier-safe, so dotted access fails validation. Emit the bracket form
  always — `env["MAWM_WEB_URL"]` — including inside interpolation, where it needs
  escaping: `"${env[\"MAWM_API_BASE_URL\"]}/path"`. Dotted access working for some
  names is a trap, because any sane naming convention produces names it fails on.
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

## Api blocks, and a Residue cause overturned

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
  divergence described in `fault-classes.md` does not apply to it.
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
