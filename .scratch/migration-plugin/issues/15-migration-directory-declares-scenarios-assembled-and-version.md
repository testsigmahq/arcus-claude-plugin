# 15 — The Migration Directory declares `scenarios.md`, `assembled.md` and a row Version

**What to build:** The Migration Directory's file set grows by two, and the Step Map
gains the column that makes a decision correctable later.

`scenarios.md` holds one row per source scenario: the scenario, the Source Steps it
reaches, a status of `pending`, `done`, `parked` or `out-of-scope`, and a `Reason`
used by `parked` and `out-of-scope` alike. It is both the incidence and the
Conversion queue, so one read answers what is left and what it would cost.

`assembled.md` holds one row per assembled test: the scenario, the test, the row
versions it consumed, and when. It is what makes a corrected row's dependents
findable without re-reading the working copy.

`step-map.md` gains a `Version` column beside `Status`, bumped only when the row's
Expression or Status changes — never when occurrence counts or provenance are
corrected, because those change every Conversion and a version churning on them
would re-assemble the suite for nothing.

Nothing writes either file yet. This ticket declares the shape so that every later
ticket edits against it rather than inventing one, and so `assembled.md`'s columns
are settled before anything depends on them. The unseen count is deliberately not a
column: it is computed on demand, because a stored count is stale the moment any
Conversion finishes and a stale count silently mis-orders the queue.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] The reference that fixes the Migration Directory's file set declares both new files, what each holds, and why, and carries a skeleton for each
- [ ] The single constant the document tests read lists both new files, so their contract coverage follows from it
- [ ] The Step Map's documented columns include `Version`, placed beside `Status`, with the bump rule stated
- [ ] The `Reason` column is documented as serving both `parked` and `out-of-scope`
- [ ] The four statuses are documented as the complete set
- [ ] It is stated that the unseen count is computed, never stored, with the staleness reason
- [ ] Document tests cover each of the above, asserting the rule is present and binding rather than its wording
- [ ] The existing suite stays green
