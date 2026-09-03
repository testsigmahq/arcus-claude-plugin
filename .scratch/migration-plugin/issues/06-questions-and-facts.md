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

- [ ] Any skill can raise a question mid-work without handing off to a different skill
- [ ] Questions carry a short list of answers with one recommended, so nothing must be composed from scratch
- [ ] Questions contain no code, file paths, stack traces or diagnostic codes
- [ ] An unanswered question persists across sessions and is surfaced by resume until answered
- [ ] Platform Facts and Application Facts are recorded separately, and a Platform Fact is settled by probing rather than by asking the Operator
- [ ] Answering a question clears it, and only an answer clears it
- [ ] Tests assert the question rules, including the prohibition on code and diagnostic codes
