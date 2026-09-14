# 22 — `resume` reports the Conversion queue

**What to build:** A Migration runs over many days and every session starts blank.
`resume` is the session entry point, and the question a fresh session now asks is
"which Conversion next, and is anything waiting on me".

Its Phase line goes. With survey the only Phase, that line would read "converting" for
three weeks, which is noise in front of the thing the Operator actually needs. In its
place: what is done, what is pending, what is parked and what each parked Conversion
waits on, and which Conversion would be taken next.

Everything else `resume` does is kept — unanswered questions, and whether the
installed Testsigma command-line tool has changed since the Migration was pinned. It
stays read-only, with the one existing exception for correcting a record that has
become wrong.

**Blocked by:** 18.

**Status:** ready-for-agent

- [ ] `resume` reports the Conversion queue: done, pending, parked with reasons
- [ ] It names which Conversion it would take next
- [ ] The Phase line is gone
- [ ] Unanswered questions and command-line-tool drift are still reported
- [ ] It remains read-only apart from the existing correction case
- [ ] Its output carries none of the four forbidden kinds of detail
- [ ] Its own description matches what it now reports
- [ ] Document tests cover the queue reporting and the removed Phase line
