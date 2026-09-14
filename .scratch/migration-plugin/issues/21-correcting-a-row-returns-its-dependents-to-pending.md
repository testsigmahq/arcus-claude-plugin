# 21 — Correcting a row returns its dependents to pending

**What to build:** The machinery for an obligation the plugin already holds. The
Migration Directory reference already says a row that fails re-check "stops being
`reviewed` and is worked again, along with every test already assembled from it."
Under whole-suite Phases no test existed yet when a row was revised, so the rule was
unreachable. Conversions make it reachable, and nothing could find those tests.

When a row's Expression or Status changes, its `Version` is bumped. A script then
reads `assembled.md`, finds exactly the scenarios that consumed an older version of
that row, and returns them to `pending`. They are re-taken as Conversions through the
same loop — there is one path to a delivered test, not two.

A re-opened scenario visibly goes back to pending, which is what keeps the delivered
count honest. Without it the suite would report tests delivered that were built on a
decision since ruled wrong, which is precisely what the check record and Residue exist
to prevent.

The same ticket adds the consistency check that keeps the queue trustworthy: no
scenario may be `done` without an `assembled.md` row, none may be `parked` without a
`Reason`, and none may hold two statuses at once.

**Blocked by:** 18.

**Status:** ready-for-agent

- [ ] A row's `Version` is bumped when its Expression or Status changes, and not when
      its occurrence count or provenance is corrected
- [ ] A script reads `assembled.md` and returns exactly the scenarios that consumed a
      superseded version to `pending` — no more and no fewer
- [ ] Re-opened scenarios are re-taken through the same `convert` loop
- [ ] The delivered count reflects the re-opening rather than continuing to count the
      superseded test
- [ ] A consistency check rejects `done` with no assembled row, `parked` with no
      reason, and contradictory statuses
- [ ] The Operator is told which scenarios were re-opened and why, in their terms
- [ ] Unit tests cover the invalidation set, the bump rule and each consistency failure
- [ ] Prior art for the tests is the existing check-script tests
