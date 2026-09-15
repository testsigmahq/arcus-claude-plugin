# 31 — One block may claim several source steps

**What to build:** An empty block means two opposite things, and the impostors outnumber
the real signal 13 to 1.

`assemble` says one block per source step, labelled with that step's text, because
`check_coverage.py` reads those labels to prove no source step was silently dropped. It
also says a Residue row is assembled as an **empty block** whose label names what was
needed, so a declined step is never absent from the test.

Those meet badly wherever a target construct absorbs several source steps. Testsigma's
`api "name" { }` *is* the request, its send and its assertions, so five Gherkin steps
collapse into one block. Four of the five are genuinely converted and have no statement
of their own to stand in, so following the rule literally produces four empty blocks
labelled "(checked by the request above)" — the shape that means *nobody could express
this*, used to mean *expressed, inside its neighbour*.

**Measured** across four converted tests, 648 blocks: 85 empty (13%, and 19% in one
test). 79 are absorbed-into-a-neighbour. **Six** are true Residue markers. A reviewer
sweeping for what a Migration did not do meets thirteen impostors for every real one, and
a reader going top to bottom concludes the conversion is threadbare.

**The fix: a block claims every source step it performs.** The api block carries all five,
coverage counts each, and the empty blocks disappear. An empty block then means exactly
one thing again — which is why this needs no marker prefix to tell the two apart, and why
the prefix alternative was rejected: it would have made the real markers greppable while
leaving 79 blocks whose *shape* still said nothing was written here.

**Why not record absorption in the Migration Directory.** Because a record the same run
writes about its own completeness is not independent evidence. The check's value is that
it compares the test artifact against the source, so a claim that lives anywhere else
lets an assembler assert the thing the check exists to doubt.

**The claim is a list, never a position.** A claim spelled "this block covers the next
N source lines" is cheaper and is wrong. Measured in the WLM test: the GET pattern repeats
18 times, and 12 of the absorbed steps — `Store Value from get response details in Request
Body from key …` — sit a line or two *after* the block that performed them, because the
source interleaves a wait. A contiguous run is the common case, not the rule, so the claim
names its steps explicitly and in any order.

**The carrier is the block's name, and it is the only honest one.** A block takes no
arbitrary attribute — `covers = [...]` and `description = ...` are both `TSF2003`, on every
kind. The `as myLabel` identifier is a bare camelCase token and prose there is a parse
error. Comments are refused outright (`TSF1003`), because `pull` regenerates the file and
would destroy them. So the claim lives in the name, which is also what the app shows as
the step.

Length is not a constraint: the compiler has no length check, and server-side a block's
name is the step's `action` column, `text` in utf8mb4 at 65,535 **bytes**, validated only
for blankness. 412 characters is nowhere near it, and nothing truncates.

**The separator is ` | `.** It survives a round trip, reads in the app's step list, and
occurs nowhere in the measured fixtures. Where a source step does contain it, the claim's
segment simply fails to match a known step and is reported — a loud failure, not a silent
pass, which is the only property that matters here.

**Every segment is a source step.** The absorber's own step comes first, so the step list
stays legible without inventing a summary line. A synthesised head such as `POST /orders`
would be a segment that claims nothing, and the check would have to tolerate an
unaccountable segment to accept it — which is the loosening this issue must not make.

**One thing is read off the code and not observed on the wire.** "Nothing truncates" comes
from the DDL and the validator, not from a push. One 412-character block pushed and pulled
settles it, in the Operator's own project.

**What must not weaken.** `check_coverage.py` is the only check that catches a conversion
stopping early, and it is not being loosened — it is being taught that one label may
account for more than one step. Coverage stays a multiset, a nested block still claims
nothing, and a label still claims a step only by equalling it or by equalling it with a
bracketed qualifier. The new claim is an addition to that grammar, not a relaxation of it.

**Blocked by:** nothing. The carrier is settled; the push proof is an Operator action
and does not block the code.

**Status:** ready-for-agent

- [ ] `assemble` says a block claims every source step it performs
- [ ] The rule says an empty block means Residue and nothing else
- [ ] A residue marker and an absorbed step are no longer the same shape
- [ ] `check_coverage.py` counts every step a multi-step claim accounts for
- [ ] It still refuses a nested block's label as a claim
- [ ] It still requires an exact step, or a step with a bracketed qualifier
- [ ] Coverage remains a multiset — a step written twice needs two claims
- [ ] A claim that accounts for a step the source does not hold is an extra, not a pass
- [ ] The claim is spelled in the block's name, with ` | ` between steps
- [ ] Every segment is a source step, the absorber's own first
- [ ] A segment matching no source step is reported rather than ignored
- [ ] A 412-character name is shown to survive a push and a pull
- [ ] A claim names its steps explicitly, and never by position or count
- [ ] A claim holds where an absorbed step is not adjacent to its absorber
- [ ] The measured cases are fixtures: a contiguous run, and a separated one
