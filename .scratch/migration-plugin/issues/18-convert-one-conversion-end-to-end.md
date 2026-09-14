# 18 — `convert`: one Conversion, end to end

**What to build:** The tracer bullet, and the reason for the whole change. A new
`convert` skill performs exactly one Conversion and stops.

One invocation reads the Migration Directory, picks the next scenario, maps the
Source Steps that scenario reaches, resolves their elements, assembles the test, runs
the stage's checks, records what ran, writes the `assembled.md` row with the versions
it consumed, commits, reports, and ends. The Operator gets a working Testsigma test
on the first day of a Migration instead of in the third week.

It performs one and stops rather than looping. A loop accumulates every scenario's
source reading in one context window, and by the tenth the judgement calls this
plugin exists to protect would be happening well outside the window in which a model
reasons sharply. One per invocation also means each session starts from the Migration
Directory and nothing else, which is what the directory was built for.

`map` and `assemble` are called, not absorbed. Both carry measured rules that merging
would risk losing, and both are already shaped for this: `map`'s call-chain expansion
is already scoped to a scenario, and `assemble` is already scenario-at-a-time. What
`convert` owns is the queue, the ordering and the re-queue trigger — none of which
belong to either.

The report leads with tests delivered of total scenarios, because that is the number
the customer is owed. Rows reviewed of total distinct stays as the second line: it is
the anti-stall signal, and it is what explains why the third Conversion took an hour
and the three-hundredth took four minutes.

Nothing shown to the Operator carries code, a file path, a stack trace or a
diagnostic code. The new reporting is not exempt from that.

**Blocked by:** 16, 17.

**Status:** ready-for-agent

- [ ] A `convert` skill exists, with a description that makes it the way to convert a
      scenario and not the way into a Migration
- [ ] It refuses to run where no Migration has been surveyed
- [ ] It performs exactly one Conversion per invocation and stops, stated as a binding
      rule rather than a preference
- [ ] It selects the next scenario using the selection from ticket 17
- [ ] It calls the mapping and assembly skills rather than restating their rules
- [ ] Every Source Step it maps still gets the helper opened and the comparison run
      before its row is reviewed — delivering sooner weakens no check
- [ ] It writes the `assembled.md` row with the scenario, the test and the row
      versions consumed
- [ ] It sets the scenario's status to `done`
- [ ] It commits the Migration Directory and the assembled test as the Conversion ends
- [ ] It reports, in order: the test delivered; tests delivered of total scenarios;
      rows reviewed of total distinct; rows new versus reused; any Concession or
      Residue recorded
- [ ] Its report carries none of the four forbidden kinds of detail
- [ ] It carries no permission-granting hedges, as every other skill is checked for
- [ ] Document tests cover the one-and-stop rule, the delegation, the `assembled.md`
      write and the report's contents
