---
type: llm
criteria: |
  The response reports progress as a count of tests delivered against the total
  number of scenarios in the Migration — for example "one of six delivered" —
  rather than only describing the test it wrote. An equivalent phrasing counts,
  and so does reporting the remaining count alongside it. It fails if no
  progress against the whole suite is given, or if the response claims more
  scenarios are finished than tests were written. Judge only whether delivered
  and total were both reported; ignore wording, formatting, and everything said
  about mapping, checks or commits.
---
The number a customer onboarding onto Testsigma counts progress in, and the
reason one Conversion per invocation is tolerable to them: a run that stops after
one test has to say what it stopped in the middle of, or stopping reads as
failing.

A model converting freehand reports what it did. It has no reason to report the
denominator, because nothing told it the queue was the unit of work.
