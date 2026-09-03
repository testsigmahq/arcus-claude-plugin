---
name: cucumber-java
source: Cucumber feature files over a Java page-object layer
hides-sequence: "yes"
carries-locators: "yes"
value-language: "no"
---

# Source Adapter: Cucumber over Java page objects

Gherkin `.feature` files, step definitions in Java, and a page-object layer
holding the Selenium calls. The most common source shape, and the one with
end-to-end evidence behind it: a scenario from a suite of this shape was
converted, passed every automated check first time, and was still wrong in six
ways. Four of the six came from trusting a feature-file line instead of reading
the helper underneath it.

## Source Step

One step line in a `.feature` file, with its keyword dropped.

`Given`, `When`, `Then`, `And`, `But` and `*` are all equivalent for this
purpose. `And` and `But` inherit the previous step's keyword at run time, and the
same phrasing under a different keyword is the same unit of intent, so the
keyword is not part of the identity of a Source Step.

Count step lines **as written**, not as executed. A `Background` block is written
once and runs once per scenario in the file; it counts once. A `Scenario Outline`
step is written once and runs once per `Examples` row; it counts once. Counting
executions would inflate the total and tell you nothing about the vocabulary,
which is what a Collapse Ratio is for.

These are not step lines and are not counted: comments, tags, data-table rows,
`Examples` table rows, and anything inside a docstring. A line inside a docstring
that begins with `Given` is prose.

**English keywords only.** Gherkin allows localised keywords through a
`# language:` pragma. This rule is written for the English ones. A suite that
declares another language needs its keyword set added to the rule first; do not
enumerate it and report a number, because a reader that does not recognise the
keywords finds no steps at all and zero looks like an answer.

## Normalisation

Two step lines are the same Source Step when this produces the same string for
both. Apply in order:

1. Drop the leading keyword and any whitespace after it. `*` is a keyword too.
2. Replace every double-quoted span with `"<param>"`.
3. Replace every single-quoted span with `"<param>"`, but only where both quotes
   sit on a boundary: the opening quote at the start or after a space, the
   closing quote at the end or before a space or punctuation. Without that
   restriction `I don't see the user's name` reads `'t see the user'` as a
   parameter, which is why the restriction is part of the rule rather than an
   implementation detail.
4. Replace every `<placeholder>` from a `Scenario Outline` with `"<param>"`.
5. Collapse every run of whitespace to a single space, then trim.
6. Strip trailing `.`, `,`, `;`, `:` and `!`.
7. Replace every standalone number with `<number>`. A number is standalone only
   when it is not adjacent to a word character or a dot, so `3` in `3 results`
   is a parameter and `05` in `ILPN05` is not. A comma-grouped number such as
   `1,000` is one number, and a version-like `1.2.3` is left alone.

Three consequences of that order are deliberate.

**Quoted spans are replaced before outline placeholders**, so a placeholder
written inside a quoted literal is swallowed along with the literal instead of
being rewritten into nested quotes. `When I open a "quoted <term> inside"`
normalises to `I open a "<param>"`, one parameter, not three.

**Trailing punctuation is stripped before numbers are replaced.** The number
rule refuses a digit that abuts a dot, so that a version-like `1.2.3` is not
mangled. Stripping a sentence-ending full stop afterwards would leave
`Then I see 5.` and `Then I see 5` as two different Source Steps, which they are
plainly not.

**Every literal collapses onto the same placeholder**, whichever way it was
written. So `When I search for "A1"`, `When I search for 'A1'` and
`When I search for <lpn>` are one Source Step asked three ways. Quoting style is
not part of what a step means.

**A parameter is sometimes a verb.** Where the parameter of a collapsed step is
the action rather than the data, the row covers more than one action. In a
measured suite `API send "<param>" request` occurred 80 times and its parameter
was the HTTP method, 56 POST and 24 GET. The rule is right to collapse it, since
the source wrote one phrasing, but the Step Map row is two rows of work wearing
one row's clothes. Look for this whenever a parameter's distinct values are few
and read like commands.

**The rule is textual, and that has limits you should expect.** `I see <number>
result` and `I see <number> results` normalise differently and count as two
Source Steps, because singular and plural are different strings. That is correct
behaviour for a mechanical rule and usually wrong as a judgement. Treat a pair
like that as one Source Step when mapping, and say so in the Step Map row rather
than editing the rule.

## Sequence

**The feature file does not tell you what a step does.** It names a step
definition, the step definition calls a page-object method, and the page-object
method holds the Selenium calls. The sequence lives there and nowhere else.

Recover it by opening the page-object method, every time, for every distinct
Source Step. Read it for **sequence**, not only for locators. This is the single
most important instruction in this document, because it is the one that was
skipped: on the evidence conversion those same page objects were opened, they
were read for locators, nobody asked what the code actually did, and four of the
six faults went through.

Three traps recur. All three produce a converted test that runs and passes.

**A helper that does less than its line implies.** `When I select "Damaged"
reason code` reads as a choice being committed. The method only sends text. There
is a submit control on the page and no caller ever clicks it. Converting the
implied submit invents a step the source never performed.

**A helper that does more than its line implies.** `When I search for LPN "X"`
reads as typing. The method tests whether the field is displayed, clicks an
expand control when it is not, clears the field, types, then presses Enter. Four
actions, one conditional among them, none of it visible from the feature file.

**A helper named like a wait that is a loop.** Treat every helper whose name
contains `wait`, `until`, `refresh` or `poll` as a loop until the source proves
otherwise. Include the shape that reads as an assertion: a step like
`Wait and Validate <thing> status is "<value>"` polls, and measurement of a real
suite of this shape found 50 occurrences of that pattern against 8 of the more
obvious `Click refresh until …`. The obvious ones are not where the volume is. These typically re-drive the interface on each pass, retyping a filter
and clicking refresh, so flattening one into a passive wait produces a test that
looks right and does something else. `refreshUntilRecordAppears` is this shape.

**A helper that delegates.** When a method calls another method, follow it; the
sequence is the flattened sequence of the leaves. `putAwayLpn` reads as two
actions and is five, because the search helper it calls is itself four. Stopping
at the first method the step definition names is the most natural way to get this
wrong, because that method looks complete.

## Locators

In the page objects, as `@FindBy` annotations and `By.id`, `By.xpath`,
`By.cssSelector` literals. Lift them as they are; do not reinvent them.

This is the same file you are already opening for sequence, so it is one reading
with two questions, not two readings. Keeping them separate is what allowed the
sequence faults: the files were opened for locators and the sequence question was
never asked. Element Resolution is therefore part of mapping for this source, not
a Phase of its own.

Where a locator is built at run time rather than declared, treat the element as
unresolved and record it, rather than guessing a static equivalent.

**The element vocabulary does not collapse with the step vocabulary.** A generic
step such as `Click "<param>" on "<param>"` takes the control and the screen as
parameters, so one Source Step occurring hundreds of times still names hundreds
of different things to find. In a measured suite of this shape, that one step
carried 108 distinct control-and-screen pairs across 38 screens. Estimating
element work as a proportion of Source Steps will be badly wrong; count the
distinct parameter values, not the steps.

## Values

This format has no value language. A Gherkin value is a literal: a quoted string,
a bare number, or an outline placeholder standing for one. There is no embedded
syntax to interpret, so a value never hides a sequence.

Docstrings and data tables attached to a step are **data**, not language. They
carry a payload for the step, and they belong in a Step Map row's parameter
shapes rather than being read as actions.

The Composite Step in this format therefore only ever appears in the helper
layer, which is why `hides-sequence` matters here and `value-language` does not.

## API steps

A suite of this shape is usually not only UI. Measurement of a real one found that
29 distinct Source Steps, 8% of the vocabulary, carried 511 occurrences, 19% of all
step lines: sending a request, asserting a response code, reading a value by JSON
path, minting an access token, setting a request body from a file.

**Classify these by reading them, never by keyword.** A keyword pass over the step
text was tried on that suite and got it wrong in both directions: it missed four
steps carrying 40 occurrences that say "Json" rather than "response", and it
wrongly claimed a UI step that mentioned a payload. Whether a step is API or UI is
a judgement made while mapping it, like everything else in this document.

These are the same format and a different mapping target. They have no page
object, so there is no helper layer to open and nothing for the Composite Step to
hide behind. They have no locators either, so this adapter's
`carries-locators: "yes"` describes its UI steps and says nothing about these.
Classify each distinct Source Step as UI or API before mapping it, because the
reading that recovers a UI step's sequence does not apply and looking for a page
object that does not exist wastes the effort that matters.

What replaces the helper read for an API step is the request definition: the
endpoint, the method, the body file, and the assertions made against the
response. Those live in the step definition itself or in the payload files it
names, not in a page-object layer.

## Enumeration

1. Find every `.feature` file in the suite.
2. Extract every step line, skipping comments, tags, table rows and docstrings.
3. Normalise each line by the rule above.
4. Count occurrences of each distinct result.
5. Report the total, the distinct count, their ratio, and how many Source Steps
   occur exactly once.
6. Report the parameterisation profile as well: how many distinct Source Steps
   carry no parameter, how many carry one the suite only ever fills a single way,
   and how many genuinely vary.

The last number matters as much as the ratio. A Source Step occurring once
amortises nothing, so the long tail sets the floor cost of a Migration.

The parameterisation profile matters because it says which rows are expensive. In
a measured suite of this shape, 219 of 351 Source Steps carried no parameter at
all and another 67 carried one the suite always filled the same way, leaving 65
that genuinely varied. A fixed phrasing is a much cheaper row than a parameterised
one, so a schedule built on an average row will mis-order the work. The
parameterised rows are where the Composite Steps and the judgement concentrate.

### Worked example

Against the fixture in `tests/fixtures/cucumber-java`, which is two feature files
and three page objects:

| Source Step | Occurrences |
|---|---|
| `I see the LPN "<param>" in the list` | 5 |
| `I am signed in` | 2 |
| `I refresh until the record appears` | 2 |
| `I search for LPN "<param>"` | 2 |
| `I put away LPN "<param>"` | 1 |
| `I see <number> result` | 1 |
| `I see <number> results` | 1 |
| `I select "<param>" reason code` | 1 |

Fifteen step lines, eight distinct Source Steps, a Collapse Ratio of 1.88, and
four Source Steps occurring exactly once.

Note what the ratio does not tell you. Two of those eight are the
singular/plural pair discussed under Normalisation and are really one step.
`I search for LPN "<param>"` is the four-action Composite Step. And
`I put away LPN "<param>"` occurs once, looks like the smallest row in the table,
and is the largest: it delegates to the search helper, so its true sequence is
five actions and only two of them are visible in the method the step definition
names. A healthy-looking ratio says the vocabulary is worth mapping. It says
nothing about how much work any row is.
