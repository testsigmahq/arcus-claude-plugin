# 13 — Eval fixtures and eval cases

**What to build:** The behavioural seam. The document tests can only prove a skill says the
right words; these check whether it actually steers an agent. Two small fixtures, both
hand-built rather than lifted from any real suite, and the eval cases over them.

The fixtures: a Cucumber suite over Java page objects containing one helper that does more
than its source line implies, one that does less, and a wait-until helper that re-drives
the interface; and a Tosca export containing a reusable block, a value in the source's own
small language, and a wildcard comparison.

Deterministic assertions carry the weight, because they are stable. Was the mapping skill
the skill that ran. Did the agent read the helper file before writing the Step Map row,
which expresses the entire composite-step discipline as one ordering assertion. Was an open
question written down. Was no test written for a scenario with an unresolved element.

Model judgement is used sparingly and only where nothing else reaches: whether the agent
reported the helper's true sequence rather than the source line's implication, whether it
raised a question instead of guessing, and whether the question it raised is free of code
and paths. These matter most and cannot be made deterministic, so they carry a known
flakiness cost and their criteria must be written narrowly.

Running each case both with and without the plugin is the point. For a plugin that is
nothing but instructions, the difference between those two runs is the only honest measure
of whether an instruction is doing any work. A capable model may open the helper unprompted,
and if it does, the document telling it to has earned nothing.

Note the gate: the eval runner is in early access and is not enabled here, and the
installed Claude Code is well past every version minimum, so this is entitlement rather
than version. The cases are authored anyway, because they are only files, and they begin
running when the gate opens. Nobody should try to enable it by editing a settings file.

**Blocked by:** 07, 09, 11

**Status:** ready-for-agent

- [ ] Two fixtures exist, small, hand-built, containing no third-party or client-identifying data
- [ ] Deterministic assertions cover skill routing, reading the helper before writing the row, writing an open question, and refusing a test with an unresolved element
- [ ] Model-judged assertions cover reporting true sequence, asking rather than guessing, and question hygiene, with narrowly written criteria
- [ ] Cases are configured to run with and without the plugin so the difference is reported
- [ ] Runs are cost-capped, and the suite reports a pass or fail usable by continuous integration
- [ ] The early-access gate is documented alongside the cases so the next person understands why they do not run yet
- [ ] Evals run on demand and on changes to the plugin's documents, not on every commit
