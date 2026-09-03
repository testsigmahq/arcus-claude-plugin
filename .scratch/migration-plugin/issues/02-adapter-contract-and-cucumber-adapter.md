# 02 — Source Adapter contract and the Cucumber adapter

**What to build:** The format for a Source Adapter, and the first one. An adapter is a
document that tells an agent how to read one source format into Source Steps, and it must
state three things about its format up front: whether the real action sequence hides
behind a helper layer, whether the source carries locators, and whether values carry a
small language of their own. Then the Cucumber-over-Java-page-objects adapter written
against that format.

When this lands, an agent handed a Cucumber suite can enumerate its distinct Source Steps
with occurrence counts and say which of the three properties apply.

**Blocked by:** 01

**Status:** ready-for-agent

- [x] An adapter document format is defined and documented, including how the three properties are declared
- [x] The Cucumber adapter declares all three properties with an explicit value for each, and declares that this source hides sequence, carries locators, and has no value language
- [x] The adapter states the normalisation rule that decides when two source lines are the same Source Step, precisely enough that two people applying it get the same count
- [x] The adapter says where to find the layer that holds true sequence, and that it must be opened for sequence and not only for locators
- [x] Tests assert that any adapter document declares all three properties, so an adapter missing one fails
- [x] Demonstrated against a small fixture suite: distinct Source Steps enumerated with occurrence counts

**Done, 2026-09-03.** 115 tests pass, 2 skipped. Adapters live at `adapters/`,
with `README.md` as the format and one document per source format beside it.

The three properties are frontmatter, each taking `yes`, `no` or `sometimes`.
`sometimes` exists because Katalon hides sequence only where a called test case or
custom keyword is used. Six sections are required and their presence is checked,
never their wording, with one stated exception: where a source hides sequence, the
Sequence section must mention both sequence and locators.

How criterion 3 was made real rather than asserted. The rule is seven ordered steps in
the adapter, and `tests/gherkin.py` is that rule as code. The suite applies the code to
the fixture and compares against the worked-example table in the adapter itself, so
the document's rule and its own counts cannot drift apart. The reviewer was asked to
challenge whether that violates ADR-0004 and concluded it does not: the module is
imported by nothing outside `tests/`, and it encodes only the normalisation rule the
adapter already calls mechanical and imperfect. It never touches sequence recovery,
locators or values, which are the judgement calls ADR-0004 protects.

**Six bugs found in my own rule, five by attacking it and one by review.** The
single-quote pass read apostrophes in prose as delimiters. An outline placeholder
inside a quoted span produced nested quotes. `*` bullet steps were not recognised.
Comma-grouped numbers split. A localised feature file yielded no steps at all, so a
Collapse Ratio of zero would have read as an answer. And the one review found: the
number rule refuses a digit abutting a dot so that `1.2.3` survives, but trailing
punctuation was stripped afterwards, leaving `I see 5.` and `I see 5` as two Source
Steps. That last one is the worst kind, because the code faithfully implemented a rule
that was itself wrong, so comparing code against the document could never find it.

The fixture is two feature files and four page objects, each carrying one trap: a
helper doing more than its line implies, one doing less, one named like a wait that is
a loop re-driving the interface, and one that delegates to another page object so its
true sequence is only visible a level down. The fourth came from review, which noted
the adapter tells the reader to follow nested calls while the fixture had no nested
call to follow. The suite asserts every trap is still present, because ticket 13's
evals are worthless against a fixture quietly simplified.

Fifteen step lines, eight distinct Source Steps, a Collapse Ratio of 1.88, four
Source Steps occurring once. Two of the eight are a singular/plural pair a textual
rule must split and a person would treat as one; the adapter documents that limit and
a test asserts the limit is real so the warning cannot go stale.

Nine mutations verified. One methodology note worth keeping: rapid same-second file
swaps during mutation testing can defeat Python's bytecode cache check and produce a
false result, which happened once here. The battery was re-run with bytecode writing
disabled and all nine were caught.
