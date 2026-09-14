# 17 — Choosing the next Conversion

**What to build:** The rule that decides which scenario is converted next, as a script
rather than as prose an agent re-approximates every session.

The first Conversions are chosen by greedy set cover: the scenario introducing the
most unseen Source Steps, where unseen means the Step Map has no reviewed row for it
yet. That front-loads the judgement while it is still cheap to correct, and makes
every later Conversion cheaper fastest.

When the next scenario would introduce fewer than about three unseen Source Steps,
vocabulary has saturated and the ordering hands over to whatever the Operator's
priority is. The threshold is measured rather than a fixed count, because a fixed
count guesses at a suite's shape — on one suite the curve flattens at the eighth
Conversion and on another at the fortieth. The switch is reported when it happens, so
the Operator knows they can start naming what they want next.

This is mechanical in the same sense survey's enumeration is: exact by construction.
It joins the existing family of check scripts so it is unit-tested directly.

**Blocked by:** 16.

**Status:** ready-for-agent

- [ ] A script computes the unseen count per scenario from the Migration Directory,
      never reading a stored count
- [ ] It selects the next Conversion by greedy set cover among `pending` scenarios
- [ ] `out-of-scope` scenarios are never selected
- [ ] `parked` scenarios are not selected while still parked
- [ ] It reports when the threshold is crossed and ordering hands over to Operator
      priority
- [ ] Selection is deterministic: two runs over the same state select the same
      scenario, including when two scenarios tie
- [ ] Unit tests cover selection, the threshold switch, the exclusions and the tie
- [ ] Prior art for the tests is the existing check-script tests
