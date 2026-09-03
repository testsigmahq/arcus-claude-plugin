# 03 — Measure the Collapse Ratio of the evidence suite

**What to build:** The one number the whole mapping approach rests on and nobody has
measured. Mapping each distinct Source Step once and reusing the verdict is only
affordable if source steps repeat. Apply the Cucumber adapter's normalisation rule to the
suite that produced the six faults, and report the total step count, the distinct count,
their ratio, and the size of the long tail that occurs exactly once.

The long tail matters as much as the ratio. Steps appearing once cannot amortise anything,
so they set the floor cost of a Migration.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] Total source step occurrences and distinct Source Step count both reported, with the normalisation rule stated so the number is reproducible
- [ ] The ratio reported, along with the count of Source Steps occurring exactly once
- [ ] The most frequent Source Steps listed with their counts, so the shape of the vocabulary is visible and not just its size
- [ ] A stated conclusion on whether per-distinct-step comparison is affordable for a suite of this shape
- [ ] If the ratio is near 1.0, say so plainly, because that is a reason to reconsider the mapping design rather than a number to file
