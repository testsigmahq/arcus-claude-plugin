# 19 — Parking

**What to build:** A Conversion that needs something only the Operator can give is
parked, and the loop takes the next one.

Under Phases, one unanswered question could hold up an entire Migration, because a
Phase blocks the next and nothing downstream may start. For a customer onboarding
onto Testsigma that is the failure this whole change exists to prevent: weeks of
silence traceable to a single question nobody chased.

A parked Conversion records what it is waiting on, in the Operator's terms. It is
revisited when that thing clears — an answer arriving in the open questions, or an
element becoming available — and it goes back through the same loop rather than a
second path.

Residue never parks a Conversion. A Source Step the format cannot express is a decided
outcome, not an outstanding one, and it already assembles as a marker so the step is
never silently absent. Losing a whole test to a step that was correctly declined would
be a regression.

**Blocked by:** 18.

**Status:** ready-for-agent

- [ ] `convert` parks a Conversion when it needs something only the Operator can
      supply, rather than stopping the run
- [ ] The scenario's status becomes `parked` and its `Reason` says what it waits on,
      in the Operator's terms and carrying none of the forbidden detail
- [ ] Having parked, the invocation ends — it does not go on to another Conversion in
      the same window
- [ ] A parked Conversion becomes selectable again once the thing it waited on clears
- [ ] A re-taken Conversion goes through the same loop as any other
- [ ] Residue does not park a Conversion; the marker behaviour is unchanged
- [ ] The Operator is told what parked and why, without being asked to decode anything
- [ ] Document tests cover parking, the reason, the non-stall and the Residue exception
