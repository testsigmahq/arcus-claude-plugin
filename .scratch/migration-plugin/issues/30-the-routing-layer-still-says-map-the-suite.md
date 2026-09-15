# 30 — The routing layer still says "map the suite"

**What to build:** A Migration run after ADR-0012 and issue 24 still defaults to mapping
the whole vocabulary before converting anything. The procedures are right — `map`'s
Step 0 says "across the whole scenario", and `convert` performs one Conversion and stops.
What is wrong is the layer that decides which skill runs at all, which no document test
reads.

A skill's `description` is a **context pointer**: it is loaded every turn and its wording,
not its target, decides when the skill is reached. Three pointers still point at bulk.

**`survey` hands over to bulk mapping.** Its last instruction says what happens next is
"mapping, and roughly how large it is **in rows**". Rows are the vocabulary. So the
session that just finished surveying is told its next job is the Step Map entire, sized
in the unit of the whole suite. Under ADR-0012 what happens next is the first Conversion,
sized in scenarios.

**`map`'s description advertises two bulk branches.** It fires on "building or continuing
the Step Map" and on "working through unreviewed rows". Both are the suite-wide job.
Compare `resolve-elements`, whose pointer says "**Called by convert and scoped to** the
screens one Conversion needs" — the same relationship, stated. `map` never says it.

**`map`'s gate admits a session with no Conversion.** It requires only that
`.testsigma/migration/` exists. A Conversion is what scopes mapping to the steps one
scenario reaches, and nothing asks for one.

**Why the tests did not catch it.** Every document test reads section bodies. A
frontmatter `description` and a handover sentence are the routing layer, and nothing
asserted that routing agrees with ADR-0012. The Phase framing was retired from the
procedures and left standing in the three places that choose a skill.

**Write the pointers positively.** A prohibition drags the banned behaviour into context;
`map`'s pointer should lead with the Conversion-scoped trigger rather than opening with a
ban on bulk. One trigger per branch, and the bulk branches go rather than being renamed.

**Blocked by:** nothing.

**Status:** ready-for-agent

- [ ] `survey`'s handover names the first Conversion, sized in scenarios
- [ ] No handover sentence sizes the next step in rows
- [ ] `map`'s description carries no branch that fires on a whole suite
- [ ] `map`'s description says it is called by `convert` and scoped to one scenario
- [ ] `map`'s gate requires a Conversion, and says what scopes mapping without one
- [ ] `map` stays inside its progressive-disclosure budget
- [ ] A test reads the routing layer — descriptions and handovers — against ADR-0012
- [ ] That test fails on the text this issue was written against
