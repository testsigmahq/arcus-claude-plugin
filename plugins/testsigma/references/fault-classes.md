# Fault classes found by comparing against a source

The Composite Step is the fault class this plugin was designed around: a source
line that hides a helper doing more or less than it implies. The adapter for each
format says where that sequence lives, and the mapping skill requires opening it.

These are the others. Every entry came out of a step-by-step static comparison of
one real conversion against its Java, eleven source steps deep, and every one had
already reached a converted test that compiled, was accepted by the tenant, and
survived a round trip. None of them is hypothetical.

Work through this list for each Step Map row while comparing. It is short on
purpose.

## A format string is a program, not a value

The sharpest fault in the whole pass, and it survives every automated check.

The source built an identifier from a pattern whose letter `S` means
**fraction-of-second** in the date API it used. The conversion reused a
same-looking pattern in a different date API, where `S` means **millisecond**.
Both sides are honestly described as "prefix plus a timestamp", both are correct
against their own library, and the converted value came out eleven characters
longer with completely different variance. The test data itself was written in the
first library's dialect, so copying the pattern text across was the natural
mistake.

A round trip cannot see this. Nor can a render check, nor running the test once
successfully. Only reading which formatter class the source constructs reveals it.

**So a pattern is never copied across runtimes. It is re-derived from the rendered
output.** That applies to date and time patterns, number formats, and regular
expressions alike — anything where a short string is interpreted by a library
rather than used as a value.

The cheap mechanical check, which is what caught this one: render a sample on both
sides and diff the length and the character classes. Two patterns that produce
different lengths are not the same pattern, whatever they look like.

## A value transformed on its way to the browser

Checking that a converted literal matches the suite's test data is a weaker check
than it appears.

The measured case: one test-data key was used twice in one scenario and needed
**two different strings** — hyphenated for a grid assertion, de-hyphenated for a
scan field — because a step definition three calls deep applied a
`replace("-", "")` on the way to typing it. Both uses read the same key. The
conversion got the grid right and typed a string into the scan field that the
source never types.

The question is never "does this literal match the test data". It is **what
actually reaches the browser**. Any step definition is free to rewrite its
argument on the way there, and it will not announce that it has.

So for every value-carrying step, trace the argument from the step to the call
that finally types or asserts it, and record the **expression** rather than the
source literal. An argument that does not pass through unchanged is a conversion
hazard, and the transformation is often the only thing that makes a barcode, a
lookup or an identifier work at all — somebody wrote that `replace` for a reason.

## A non-default argument lost to a platform default

The hardest of these to see, because nothing looks wrong. The step is present,
the verb is right, and only a value is gone.

A source wait of 60 seconds converts to a step that declares no timeout, and the
step takes the platform's default of 30. The converted step reads correctly, the
comparison of *actions* passes, and the test now waits half as long as the suite
it came from.

So compare the arguments, not only the actions. Read every argument the source
passes, including the ones it passes positionally and the ones it passes by
relying on its own defaults, and check each against what the target step actually
declares.

**Treat every numeric argument in a source helper call as a candidate.** They
cluster on waits and retries, which is where a lost value is least visible and
matters most. The intent often moves syntactic place entirely — the source says
"wait longer here" as an argument, and the target says it as a step setting — so a
reader comparing only the action and its operands normalises it away with nothing
downstream complaining.

Note also why such a default exists at all: on this platform an unstated timeout
once meant no wait, so a default was stated precisely to stop absence meaning
zero. A legal value is not a faithful one. A default is not a match for a stated value that happens to equal it,
either: the next platform change moves the default and not the source.

## One target verb serving two source constructs

A total tells you nothing when two different things in the source convert to the
same thing in the target.

In the measured conversion, waits arrived two ways: as steps the feature file
spelled out, and as calls a helper made internally. Both became the same wait
verb. The converted test had eighteen of them, which is a number that cannot be
checked — a suite with the right count can still be missing every wait of one
kind while carrying extra of the other.

Attribute each occurrence to the construct it came from before comparing
anything. Two ledgers, counted separately. And note that the two are not equally
severe: a spelled-out step that is missing is a **dropped step**, while a helper's
internal call that is missing is a fidelity finding. Reporting them as one number
loses that distinction too.

## A difference that improves on the source

Where the source is the weaker of the two, the temptation is to fix it silently,
and that is still a divergence.

A measured example: the source generated an identifier from a fraction-of-second
only, giving ten thousand possible values and a real collision rate between runs.
The conversion used a full timestamp and was effectively unique. Better
engineering, and a difference the reviewing team cannot diff against their own
suite.

Raise it as a question rather than deciding. The Operator's suite may depend on
the weakness; the field may not accept the longer value; and a Migration that
improves what nobody asked it to improve has made itself harder to review. Where
fidelity and engineering judgement conflict, fidelity is the default and the
Operator decides.

## A fault that surfaces far from its cause

An omission early in a test frequently passes every step around it and fails much
later, somewhere unrelated.

In the measured conversion, a lookup field left unset meant the whole scenario
ran in the wrong business unit. Every step passed. It failed minutes later as a
record poll timing out, pointing at a step that was entirely correct — and the
poll is where anyone investigating would start.

So when reporting a finding, name where it will surface as well as where it is.
An Operator handed only the cause will not connect it to the failure they see,
and one handed only the failure will look in the wrong place.

## Partial absence read as omission

Where the conversion does something at some sites and not others, the
inconsistency is the finding.

The measured conversion cleared a field before typing at four sites and not at
four others. Uniform absence would have been a decision worth checking; partial
absence is a mistake, and it means the sites that look right were reached by
accident rather than by rule.

Check every site of a pattern once you have found one wrong, not only the site
that failed. And say which sites, because "this happens sometimes" is not
actionable.

## When the converted test cannot be run

Some Migrations cannot execute what they produce: no tenant reaches the
application under test, and the suite runs later on someone else's instance.

That changes the standard of evidence rather than lowering it. Static comparison
against the source becomes the only gate, so **absence of evidence is not
evidence** — nothing here can be settled by observing that a test ran green.

Two consequences follow. Prefer fidelity wherever fidelity and engineering
judgement conflict, because an unverifiable deviation handed to a reviewing team
is worse than a faithful reproduction of a weakness they already know: they can
only diff it against the source too. And record every check that could not run as
not checked, which `checks.md` requires anyway and which matters more here than
anywhere.

## A readiness check that answers the wrong question

The largest single finding in the conversion this catalogue comes from, and it
recurs in any target with a modern front end.

The source waited for a page by three means: a document-readiness check whose
timeout it deliberately swallowed, an unconditional two-second sleep, and then
polling a named overlay — "Please Wait", "Loading" — until it disappeared. The
converted test used the platform's page-load verb alone, which checks document
readiness by script and nothing else.

Against a single-page application those are not approximations of each other.
Document readiness goes true once, when the shell loads, and stays true; it says
nothing about whether the view now on screen has rendered. The platform's own
documentation for that verb says as much, and recommends waiting on an element
instead. The converted suite had no overlay element at all — a sweep of every
element found nothing matching a spinner, a loading state or a wait overlay.

So treat "did the shell load" and "did this view settle" as two different
questions. Where the source waits on something app-specific, that wait is a
second thing to add rather than a detail of the first, and it usually needs an
element the Migration has not lifted yet.

## A verb that addresses a different thing

Distinct from what a verb *does*: this is what it does it *to*.

The measured case: the source pressed Enter against a named element, which is
deterministic. The platform's verb sends the keypress to whatever currently holds
focus, and no element-scoped equivalent exists — checked against every verb that
mentions a key and takes an element. Nine sites in the conversion relied on it.

The risk is low only while every such step directly follows an action on the
intended element, which is exactly why the missing waits above matter more than
they look: anything that steals focus in between turns a deterministic step into
a coin toss, and nothing in the converted test would show it.

When comparing a verb, ask three things and not one: what it does, what it does
it to, and what it does on failure.

## A race that commits the wrong value rather than failing

Missing waits are usually filed as flakiness. Around an asynchronously populated
field they are worse than that, because the test passes.

The measured case: lookup fields backed by a typeahead. The source settled the
page after every clear, every keystroke sequence and every Enter; the conversion
had one wait at the end of the group. An Enter sent before the suggestion list
settles commits whatever is highlighted, so the field ends up holding a value
nobody chose, the step reports success, and the wrong value flows into everything
downstream.

So where a target field is populated asynchronously, a missing wait is a
correctness finding rather than a stability one, and it belongs with the faults
that surface far from their cause.

## A dropped side effect is judged by its consumers, not locally

A step that captures a value rather than touching the screen leaves nothing
visible when it goes missing, and whether that matters cannot be decided where it
happened.

Two measured cases, opposite outcomes. One captured a window handle that nothing
in the scenario ever read: proven benign, but only by grepping all forty-two
source lines for a consumer and finding none. Another captured a parsed document
that a later step read: a defect, and the later step had already been converted
as a weaker assertion *because* the capture was missing.

That second case is the one to internalise. **A weakness recorded at one step may
originate at an omission several steps earlier.** The later step's substring
comparison was faithful to its own source line; the fault was that the string it
compared had never been captured. Recording the Concession where the weakness
appears rather than where it originates legitimises the omission and closes the
wrong finding.

So for every dropped capture, find its consumers across the whole scenario before
judging it, and for every Concession, ask whether its cause is local or inherited
from an earlier row.

## A heuristic script over source code produces false findings

A script is legitimate where the rule it applies is exact by construction — a
normalisation rule, a count of distinct values. It is not legitimate as a way of
searching source code for faults, and the measured pass proves it three times.

A duplicate-step-definition sweep reported phantoms. An element-collision sweep
reported an ambiguity that was a commented-out declaration. And the attempted fix
for that — stripping `//` line comments — **deleted every XPath in the suite**,
because an XPath begins with `//`, producing a confident "no collisions" result
from an empty input.

The arithmetic that matters: across the whole exercise those broad scripts
produced one false positive and no true positives, while both real element defects
came from targeted greps at the row that needed them. A false finding costs more
than the manual check it replaced, because it has to be investigated and then
retracted.

So analyse source with a parser, or with a rule that cannot mistake an XPath's
leading slashes for a comment, and prefer a targeted check at each row over one
broad sweep across everything. Where a sweep is worth running, treat what it
reports as a question rather than a finding until a direct reading confirms it.

## A converter's positional heuristic drops and invents at once

Where a converter applies a rule about *where* something goes rather than *what*
the source says, it fails in both directions simultaneously, and a count will not
show it.

The measured case: every wait that the source placed **before** an action was
dropped, every wait **after** an action was kept, and three waits with no source
counterpart at all were invented — one of them between two adjacent clicks that
had no wait between them. The totals looked plausible. The positions did not.

So align the converted steps against the source's steps by position and compare
the sequences, rather than comparing how many of each kind there are. A dropped
step and an invented one cancel in a total.

## The target being smarter creates failure modes the source lacks

Twice in one scenario, a target behaviour that is better in isolation produced a
risk the source does not have.

A wait that throws on timeout where the source swallowed it turns a slow page from
a pass into a failure. And an element-resolution strategy that skips a disabled
match to find an enabled one, combined with a source locator that matches two
fields by substring, types a value into the wrong field and reports success —
where the source would have typed into the disabled field and failed visibly.

So "the target does this better" is not the end of the comparison. Ask what the
improvement does when the source's own weaknesses meet it, because a smarter
strategy applied to a sloppy locator is how a silent wrong-field write happens.

## A finding's count and its cause both drift

Findings are not settled when first written, and a Migration that accumulates them
without revisiting will act on stale ones.

Measured, across one pass: a fault first recorded at four sites turned out to have
six. An element count quoted in a dozen later findings was wrong by four. And a
defect characterised as an invented locator was re-characterised as one lifted
from the wrong page class — the defect stood, and its cause, which is what drives
the fix, was wrong.

So re-count a systemic finding as new sites appear, re-check any number quoted
from an earlier finding before relying on it, and separate a finding's verdict
from its cause: the verdict can be right while the cause is wrong, and the cause
is the half the fix is built on.

## A verdict given without the implementation

Not a fault in a conversion but a fault in checking one, and it invalidates work
rather than adding to it.

In the measured pass, every one of the first several verdicts was given before the
jar holding the source's generic step definitions had been opened. The verdicts
did not change afterwards, but their standing did: reasoning about what a step
was *for* produces a plausible mapping, and reading what it *does* produces a
verifiable one. Those are different rungs, and only the second is a check.

So obtain the implementation before starting, not partway through. Decompile the
dependency, fetch the library, read the platform's snippet class. Where a
comparison has already been made without it, re-open those rows rather than
keeping them: a verdict reached from intent is provisional, and a Migration that
records it as reviewed has recorded something it did not check.

## Names that match, behaviour that does not

**The closer two constructs' names are, the less likely anyone checks them.**
This is the reason the readiness fault above took eleven source steps to surface,
and it was hiding in the line that looks most like boilerplate in the whole
feature file.

`Wait for page loading` converting to a page-load verb is such a clean mapping
that nothing prompts you to open either side. But a framework helper is whatever
that team needed it to be after their application kept flaking — usually an
accumulation of hard-won workarounds under a generic name. A verb called `click`
probably is a click. A helper called `waitForPageLoading` is a research project.

So invert the instinct: **name convergence raises the priority of opening the
helper rather than lowering it.** Library and framework helpers are the highest
value things to decompile and the easiest to wave through. Spend the reading time
where the names agree, not where they differ, because a name that differs already
has your attention.

## A name that has drifted from its behaviour

Worse than a misleading name is one that used to be true.

The measured case, from a step named `Click <element> WaitForPageLoading`: both
calls to the wait helper are **commented out** in the step definition, replaced
by two unconditional two-second sleeps. The real behaviour is sleep, click,
sleep — no readiness check and no overlay wait at all, under a name that promises
one. Four sites in one scenario.

Commented-out code is behaviour. It is the fossil of a real debugging session:
someone found the proper wait did not work and swapped in a blunt sleep. In a
mature suite, step names are historical and drift from behaviour is the normal
state rather than the exception, so read the body and treat the name as a hint
about the past.

**And a sleep is semantics, not a smell to be glad is gone.** Twenty-four seconds
of unconditional sleeping is bad practice and it is also the synchronisation
strategy this suite actually passes with. Dropping it while also dropping the
overlay polling removes both layers of settling at once, the deliberate one and
the accidental one. Reproduce the timing the source had and let the owning team
replace sleeps with proper waits afterwards: that is a refactor, and a Migration
is a translation.

## Record the direction of every finding, not only its size

A conversion is rarely uniformly worse. Recording that a row diverges says less
than recording which way.

Measured, in the same scenario: the conversion was **lossy on timing** — sleeps
dropped, overlay waits absent, a non-default timeout halved — and **stronger on
interaction** — the platform's click waits for clickability, retries, and falls
back to a scripted click, where the source's did none of that.

Both directions matter and they need different handling. A loss is a fidelity
finding to fix. A gain is a question for the Operator, because it is still a
difference from the suite they will diff against. Reporting only a count of
findings loses the distinction, and a reviewer given "eleven findings" cannot
tell a halved timeout from an improved click.

## A count that does not match is a question first

Where the number of a construct in the source and in the conversion differ, the
mismatch is a question rather than a defect until you have found where the extra
one came from.

Measured: five clicks of one control in the conversion against four such steps in
the feature. The extra one was correct — a step definition named for typing also
clicked the control, so the fifth click came from a Composite Step rather than
from an invention. Had the count been assumed wrong, a correct step would have
been deleted.

## Verb semantics are Platform Facts, and are established before they are relied on

Several of these faults exist because a target verb was assumed to behave like
its source counterpart.

The measured case: a text-entry verb was assumed to clear the field first. It does
not — it appends. Every place the source cleared before typing therefore needed an
explicit clear, and the assumption had already been written down as a fact and
had to be corrected. A verb's real behaviour is settled by probing, recorded in
`platform-facts.md` with how it was established, and corrected in place when it
turns out to be wrong.

**The authority is the implementation, and reaching it takes more than one hop.**
On this platform the chain runs catalogue, then the seed data that maps a step
template to its snippet class, then the snippet class itself — and only the last
of those says what happens to the browser. The catalogue gives a sentence and
parameter slots and settles nothing about behaviour. Follow the chain to the end
rather than stopping at the first document that mentions the verb.

**Once a semantic is settled, turn it into a sweep.** The clear-before-typing
finding became a mechanical rule the moment the verb's behaviour was known: every
clear in the source is a required clear in the target. Sweep the whole suite for
it at once rather than rediscovering it site by site, which is how it came to be
missing at four sites and present at four others.

**Read what the platform says about its own verbs.** The readiness gap above was
discoverable from the target side alone, with no access to the source: that
verb's own success message warns that single-page applications need an element
wait instead, and that string appears in the report of every run. A verb's
documentation, its success and failure messages, and its diagnostics are all
Platform Facts waiting to be read, and cost nothing compared with inferring
behaviour from a name.

Establish the semantics of a verb before writing a row that depends on them.
Where two verbs look equivalent the difference is usually in what they do to
state: whether they clear before writing, whether they throw or swallow on
timeout.

A verb can be simultaneously **weaker and more brittle** than the source's. The
measured case is the wait above: it did less, having no overlay handling, while
also failing on a timeout the source deliberately ignored — so a page slower than
the limit passed in the source suite and fails in the converted one. "Is this
equivalent" is therefore not one question with one axis, and a verb can need
fixing in both directions at once.
