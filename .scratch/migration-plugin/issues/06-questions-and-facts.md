# 06 — Questions, Platform Facts and Application Facts

**What to build:** How the Migration talks to the Operator, and how it remembers what it
learns. Any skill can raise a question at the moment it needs one, because that is when the
information is missing. A question is phrased in Testsigma terms, offers a short list of
answers with one recommended, and never contains source code, a stack trace, a file path
or a diagnostic code. The test of an admissible question: someone with the application
open and no code checked out can answer it.

Two kinds of accumulated fact are kept apart, because who can answer them is the
distinction that matters. A Platform Fact is something true of Testsigma's own authoring
surface, and the plugin settles it by probing rather than asking. An Application Fact is
something only a person who knows the application can answer, so it stays open until
answered.

The failure being designed against is specific and already happened. A question was asked
once, never answered, and nothing anywhere recorded that it was still open.

**Blocked by:** 04

**Status:** ready-for-agent

- [x] Any skill can raise a question mid-work without handing off to a different skill
- [x] Questions carry a short list of answers with one recommended, so nothing must be composed from scratch
- [x] Questions contain no code, file paths, stack traces or diagnostic codes
- [x] An unanswered question persists across sessions and is surfaced by resume until answered
- [x] Platform Facts and Application Facts are recorded separately, and a Platform Fact is settled by probing rather than by asking the Operator
- [x] Answering a question clears it, and only an answer clears it
- [x] Tests assert the question rules, including the prohibition on code and diagnostic codes

**Done, 2026-09-04.** 208 tests pass. Asking is not a stage, so the discipline is a
reference — `references/asking.md` — that any skill points at and follows mid-work.
A skill that had to hand off in order to ask would ask later, or not at all.

The admissibility test is stated as a test rather than implied: someone with the
application open and no code checked out can answer it. The prohibition on code,
file paths, stack traces and diagnostic codes is paired with where each goes
instead, because every one of them is a fact the Migration still needs.

Reviewed, and the review found a bypass class none of the earlier ones had.

**Additive contradiction.** Every assertion in this suite is a positive existence
check, so a rule can be gutted by leaving its sentence untouched and adding a
paragraph beside it that grants an exception. Four were demonstrated at once, all
passing: strike a question a later Phase made moot, treat the recommendation as a
nicety, show an experienced Operator the raw detail on request, and file a fact in
either of the two fact files. Paragraph scoping cannot see any of them, because the
correct paragraph is still there.

Closed with a section-wide check for permission-granting vocabulary, which is the
opposite scoping to everything else here and is why it works. It narrows the class
rather than closing it — a walk-back written without any permissive word would still
pass — and `hedges_in` says so rather than implying otherwise.

**A live drift, found by the same review.** Both survey and resume restated the
forbidden list with "a command" where this reference says "code" — narrower, and
wrong, since a shell command is not the concern and source identifiers are. Both now
defer, and a test fails any document that restates the list while omitting one of
its four items.

**Three of my own tests were too loose,** all the same fault: section-scoped presence
is not instruction-scoped presence. A well-written document states a rule and then
says what to do instead, so the vocabulary repeats and deleting the rule leaves the
section still matching. Worst of the three, `only an answer clears it` was satisfied
by an unrelated paragraph that happens to say "exists only in the session's
transcript... depends on the answer". The rule could be deleted outright.

**Noted.** I reached for an `absent` guard that matched the honest document for the
third time. Where a rule is short enough to be its own phrase, asserting the phrase
beats guessing at inversions.
