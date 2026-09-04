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

- [x] Two fixtures exist, small, hand-built, containing no third-party or client-identifying data
- [x] Deterministic assertions cover skill routing, reading the helper before writing the row, writing an open question, and refusing a test with an unresolved element
- [x] Model-judged assertions cover reporting true sequence, asking rather than guessing, and question hygiene, with narrowly written criteria
- [x] Cases are configured to run with and without the plugin so the difference is reported
- [x] Runs are cost-capped, and the suite reports a pass or fail usable by continuous integration
- [x] The early-access gate is documented alongside the cases so the next person understands why they do not run yet
- [x] Evals run on demand and on changes to the plugin's documents, not on every commit

**Done, 2026-09-04.** 591 tests pass, arcus untouched at 92. Five cases, three
fixtures, and the repo's first CI workflow.

**The gate is confirmed closed.** `claude plugin eval` prints "`plugin eval` is
currently in early access" on 2.1.260, while `--help` prints the full option surface.
Entitlement, not version, exactly as the ticket said. There is no offline validator,
so the cases are checked for well-formedness by `tests/test_evals.py` and nothing
more. Nobody should try to open the gate by editing a settings file; there is no
setting.

**Both source fixtures already existed** from tickets 3 and 11, hand-built and already
covered by tests. Reusing them beats a second copy that can drift.
`evals/fixtures/migration-part-done/` is new: a Migration part-way through, so the
refusal can be checked without an eval first running a whole mapping stage.

**Review found the finding that mattered most: my prompts primed the behaviour they
measure.** Three said "Tell me what that step actually does", which instructs any
competent agent to open the implementation. Both arms would have agreed and the delta
— the only honest measure for a plugin that is nothing but instructions — would have
measured nothing. The prompts now ask only for the row, and the judged criteria read
the row the agent wrote rather than an answer nobody asked for.

Review also rated the cases for discriminating power, which is worth keeping: the
wildcard case is the strongest, and the refusal case is weaker than it looks because
the fixture's own residue entry spells out the reasoning in prose an unprompted model
may simply read.

**The schema research earned its cost by refusing to guess.** `withOnly`, `scored`
and `arm` turn out to exist, so the README's claim that no key was documented was half
wrong and is corrected — but no case sets one, because the automatic behaviour for
`tool_used: Skill` already does the job and a second statement of it can drift. Three
things remain genuinely unconfirmed and are now written down rather than assumed:
`add_dirs` resolution, whether several `add_dirs` are flattened or nested, and the
nested shape of `tool_order`'s `before`/`after`. The third matters most — a wrong
shape would make the read-before-write grader pass while checking nothing.

**The CI applies this plugin's own doctrine to itself.** While unenrolled the eval job
is skipped rather than passing, and a companion job writes "NOT CHECKED" into the run
summary. ADR-0001 says a check that could not run must never read as a pass, and a
green PR check on a gated eval is precisely the reassurance that ADR was written
about.

**Nineteen mutations verified, all caught. Six of my own tests were too weak**, and
review found five of the six:

- `"reviewed" in text` is also true when every row reads `unreviewed` — the opposite
  state. Lexical containment, not inversion.
- the cost cap and threshold were checked against the whole workflow file, so a
  comment could satisfy them. Scoping to the `run:` block was still not enough,
  because a commented-out flag lives inside it; shell comments are now stripped.
- the paths filter was checked by substring, so an added exclusion pattern would
  satisfy it while the positive glob it replaced triggered nothing.
- the enrolment condition was checked for the variable's *name*, not its polarity. An
  inverted condition would have run the paid job precisely when the account is not
  enrolled, and the test could not tell.
- the client-data scan skipped `.tsu` files, leaving the one fixture closest in shape
  to real customer export data unscanned. It now decompresses, with a separate test
  arming that so a broken decompression cannot read as clean.

**And my mutation harness produced a false green.** Three workflow mutations silently
failed to apply because the path was wrong relative to my working directory, and
reported "82 passed". An unapplied mutation is indistinguishable from a caught one
unless the harness proves the edit landed.
