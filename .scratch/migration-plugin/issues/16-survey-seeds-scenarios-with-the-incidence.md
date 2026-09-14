# 16 — Survey seeds `scenarios.md` with the incidence

**What to build:** Survey already walks every line of a suite to count how often each
Source Step occurs, and throws away which scenario each occurrence came from. That
incidence is what the Conversion ordering needs, so survey starts recording it.

When survey finishes, `scenarios.md` holds one row per source scenario with the
Source Steps it reaches and a status of `pending`. Scenarios that survey screens as
unconvertible — spreadsheet seeding, database steps, shell, version control — are
seeded `out-of-scope` with the reason, never omitted. An absent row would read as
"nobody looked", when what happened is that somebody looked and ruled it out.

Survey continues to seed every distinct Source Step as `unreviewed` in the Step Map.
That is unchanged and stays unchanged: the denominator and the anti-stall signal both
depend on the empty rows existing to be visibly unfilled.

Capturing the incidence costs one extra column in a pass survey already makes over
every line. It must not become a second pass over the source.

**Blocked by:** 15.

**Status:** ready-for-agent

- [ ] The survey skill emits the scenario-to-Source-Step incidence as part of the
      existing mechanical enumeration, not as a second pass
- [ ] Survey seeds `scenarios.md` with one row per scenario, status `pending`
- [ ] Scenarios screened as unconvertible are seeded `out-of-scope` with the reason
- [ ] Survey still seeds every distinct Source Step as `unreviewed`, unchanged
- [ ] Survey commits `scenarios.md` with the rest of the Migration Directory
- [ ] Survey's report to the Operator mentions how many scenarios are in scope and how
      many were ruled out, in their terms and carrying none of the forbidden detail
- [ ] Demoable on the existing Cucumber fixture: survey finishes and the file has rows
- [ ] Document tests cover the seeding, the `out-of-scope` rule and the unchanged Step
      Map seeding
