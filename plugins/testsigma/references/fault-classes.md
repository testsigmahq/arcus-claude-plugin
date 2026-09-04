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
declares. A default is not a match for a stated value that happens to equal it,
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
