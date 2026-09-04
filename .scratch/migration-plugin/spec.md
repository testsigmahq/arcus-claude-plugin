# Spec — the Testsigma migration plugin

Status: ready-for-agent. Not published to a tracker; local by request.
Derived from the `/grill-with-docs` session of 2026-09-03. Vocabulary is from
`plugins/testsigma/CONTEXT.md`; decisions are constrained by ADR-0001..0005 in
`plugins/testsigma/docs/adr/`.

## Problem Statement

An Operator has an existing automation suite and wants it in Testsigma. The suite is
large, so converting it takes many days and many sessions. Today there is nothing that
holds a Migration together across those sessions, and the Operator cannot read code,
so every question about what the source really does has to reach them in Testsigma
terms or not at all.

The harder half of the problem is that converting a test is easy to do wrongly and
almost impossible to notice. One scenario was converted end to end as evidence for
this spec. It passed every automated check on the first attempt, and it was still
wrong in six ways. Four of the six were steps whose source line hid a helper that did
less or more than the line implied. One weakened a structural assertion into a
substring match. One rendered conditional bodies outside their block. Every one of
them produces a test that runs and passes while testing something weaker or
different, which is the defining property of the class: executing the test cannot
find them.

So an Operator's real problem is not that conversion is slow. It is that a finished
Migration looks identical whether it is right or wrong, and nothing tells them which.

## Solution

A Claude Code plugin whose skills run a Migration as a fixed sequence of Phases, with
the checks that catch Divergence built into the Phase that produces the work rather
than bolted on at the end.

The Operator starts a Migration against a source suite, and the plugin surveys it:
picks a Source Adapter, measures the Collapse Ratio, records which CLI build is
installed and what it checks, and creates the Migration Directory inside the source
suite. From then on, one command resumes the work in any new session by reading that
directory, so no session begins by re-reading a handoff.

Mapping builds the Step Map one distinct Source Step at a time, and a row is not
finished until it has been compared against the source's implementation, not its
surface syntax. Assembly builds tests from reviewed rows and checks each one for
document order and block nesting. Anything the format cannot express becomes Residue
with a stated cause that can later be overturned. Anything learned about Testsigma
becomes a Platform Fact the plugin settles by probing. Anything only a person can
answer becomes an Application Fact that stays visibly open until answered.

Two Source Adapters ship: a Cucumber suite over Java page objects, and a Tosca
subset export. A fifth skill lets someone write a third adapter without us.

## User Stories

### Starting and resuming a Migration

1. As an Operator, I want to start a Migration by pointing at my source suite, so that I do not have to prepare anything by hand first.
2. As an Operator, I want the plugin to refuse to start against a source folder that is not under version control, so that a Migration's state cannot be lost the way the first conversion's nearly was.
3. As an Operator, I want the source suite snapshotted at the moment a Migration starts, so that later changes to the suite cannot silently invalidate work already done.
4. As an Operator, I want the plugin to tell me which Source Adapter it picked and why, so that I can correct it before any work is based on the wrong reading of my suite.
5. As an Operator, I want to be told the Collapse Ratio before mapping begins, so that I know whether my suite has a vocabulary worth mapping or is 35 unrelated scenarios.
6. As an Operator, I want to be warned when the Collapse Ratio is near 1.0, so that I can decide against a Migration rather than discover its cost halfway through.
7. As an Operator, I want a single command that resumes a Migration in a fresh session, so that starting work is one command rather than an act of archaeology.
8. As an Operator, I want resume to tell me which Phase is active, which Step Map rows are unreviewed, and which questions are unanswered, so that the next thing to do is never ambiguous.
9. As an Operator, I want resume to tell me when the installed CLI has changed since my last session, so that I learn about it before it changes what a check means.
10. As an Operator, I want the Migration Directory to live inside my source suite, so that my own repository versions it and it travels with the code it describes.
11. As an Operator, I want each concern in the Migration Directory kept in its own file, so that I can read and review one thing at a time in a normal diff.

### Mapping Source Steps

12. As an Operator, I want the plugin to extract every distinct Source Step from my suite with its occurrence count, so that I can see the vocabulary I am actually converting.
13. As an Operator, I want each distinct Source Step mapped once and the verdict reused everywhere it occurs, so that the cost of mapping scales with my vocabulary rather than my line count.
14. As an Operator, I want a Step Map row to carry the source text, occurrence count, parameter shapes, the proposed expression, and a status, so that reviewing a row does not require going back to the source.
15. As an Operator, I want one Source Step to be allowed to map to several Testsigma steps, so that a source line that really does three things is not forced into one.
16. As an Operator, I want the plugin to open the helper behind a source line and read its sequence, so that a Composite Step is caught before it becomes a converted test.
17. As an Operator, I want to be told explicitly when a helper does less than its source line implies, so that we do not invent a click that the source never performed.
18. As an Operator, I want to be told explicitly when a helper does more than its source line implies, so that a conditional expand or a clear is not silently dropped.
19. As an Operator, I want every wait, until, refresh and poll helper treated as a loop until the source proves otherwise, so that a helper that re-drives the interface is not flattened into a passive wait.
20. As an Operator, I want a value written in the source's own small language recognised as a sequence, so that a value meaning click then arrow-down then enter is not converted as a single click.
21. As an Operator, I want a wildcard or substring comparison in the source treated as a question rather than a licence, so that a weak assertion in the source does not authorise a weak assertion in Testsigma.
22. As an Operator, I want a Step Map row to be unfinishable until it has been compared against the source's implementation, so that the comparison cannot be skipped by running out of time.
23. As an Operator, I want the comparison to read the source's implementation rather than its surface syntax, so that it catches the faults that the surface syntax cannot show.

### Elements

24. As an Operator, I want locators taken from my source when my source carries them, so that I am not asked to point at screens the code already describes.
25. As an Operator, I want locator reading and sequence reading to happen in one pass over the same files, so that we do not open a page object for locators and forget to ask what it does.
26. As an Operator, I want existing Testsigma screens and elements reused where they match by name, so that a Migration does not duplicate screens I already maintain.
27. As an Operator, I want to be asked to capture an element only when neither my source nor my Testsigma project can supply it, so that my time is the last resort and not the first.
28. As an Operator, I want Element Resolution to become its own Phase only when my source carries no locators, so that a Tosca Migration gets the stage it needs and a page-object Migration does not sit through one it does not.
29. As an Operator, I want a test that references an unresolved element to be blocked rather than assembled with a placeholder, so that I never receive a test that looks finished and cannot run.

### Assembling tests

30. As an Operator, I want tests assembled from reviewed Step Map rows only, so that an unreviewed mapping cannot reach a finished test.
31. As an Operator, I want every assembled test checked for document order and block nesting, so that conditional bodies cannot be drawn empty and run late.
32. As an Operator, I want that check computed from the step tree itself rather than delegated, so that it holds whether or not the installed CLI performs it.
33. As an Operator, I want the order check to run at the level of a whole test rather than a single step, so that it sees the fault class that only exists between steps.

### Checks and the Check Record

34. As an Operator, I want the checks run in a fixed order that puts source comparison near the front, so that the one check with a record of finding faults is not the one that gets skipped.
35. As an Operator, I want a Unit of Work to be undone until its own Phase's checks have passed, so that "done" means something.
36. As an Operator, I want a check that could not run recorded as not checked, so that an absent check never reads as a pass.
37. As an Operator, I want a Check Record naming which checks ran against which Unit of Work, so that I can see the actual state of verification rather than infer it.
38. As an Operator, I want work converted before a new check existed marked as not checked against it, so that a growing tool does not leave me with silently unverified work.
39. As an Operator, I want the decision to go back and re-check to be mine, with a known cost, so that it is a choice rather than an oversight.
40. As an Operator, I want the plugin to ask the installed CLI which diagnostics it supports, so that it never claims a check that the CLI no longer performs.
41. As an Operator, I want the CLI build recorded when a Migration starts, so that a later change to the tooling is visible as a change.

### Questions, facts and residue

42. As an Operator, I want questions phrased in Testsigma terms, so that I can answer them from what I know.
43. As an Operator, I want to never be shown source code, a stack trace, a file path or a diagnostic code, so that a question is never one I have to decode before I can answer it.
44. As an Operator, I want to be shown the converted test as the app draws it, or a screenshot of my own application, so that I can judge whether it is right by looking.
45. As an Operator, I want every question to offer a short list of answers with one recommended, so that I am never asked to compose an answer from nothing.
46. As an Operator, I want a question to be answerable with my application open and no code checked out, so that answering does not require a developer.
47. As an Operator, I want an unanswered question to stay visibly open, so that it cannot be asked once, ignored, and forgotten by everything in the system.
48. As an Operator, I want facts about Testsigma kept apart from facts about my application, so that the plugin can go and settle the first kind itself.
49. As an Operator, I want the plugin to settle a Platform Fact by probing rather than asking me, so that I am only asked what only I can answer.
50. As an Operator, I want an Application Fact to persist across sessions until answered, so that the answer is not lost with the session that asked.
51. As an Operator, I want Residue to state a cause per entry, so that I know whether a step was unexpressible or an element unresolved.
52. As an Operator, I want a Residue entry to record the reasoning that produced it, so that it can be revisited rather than treated as settled.
53. As an Operator, I want an inexpressibility ruling revisited when the format gains a spelling, so that a wrong early call does not quietly limit the rest of my Migration.
54. As an Operator, I want to know that a Divergence is a different thing from Residue, so that I understand one as work declined and the other as work done wrongly.

### Source Adapters

55. As an Operator, I want a Cucumber suite over Java page objects supported out of the box, so that the most common source shape needs no setup.
56. As an Operator, I want a Tosca subset export supported out of the box, so that a Tosca suite is not a bespoke project.
57. As an Operator, I want each adapter to state whether my source hides its real sequence behind a helper layer, so that the cost of comparison is known before mapping starts.
58. As an Operator, I want each adapter to state whether my source carries locators, so that the Phase structure of my Migration is decided by my source rather than assumed.
59. As an Operator, I want each adapter to state whether values in my source carry a language of their own, so that a value hiding a sequence is read as one.
60. As a plugin maintainer, I want a skill that writes a new Source Adapter, so that a third source format does not require us.
61. As a plugin maintainer, I want adapters to be documents rather than parsers, so that the judgement a source reading needs is expressible at all.

## Implementation Decisions

**Shape.** A Claude Code plugin at `plugins/testsigma`, alongside the existing `arcus`
plugin in the same marketplace. Its `plugin.json` already exists. Everything added is
markdown: skill documents, one command document, and two Source Adapter documents.
There is no runtime code, by ADR-0004.

**One skill per Phase.** Four stage skills, because the Phases already block each
other and a skill per Phase makes the next action obvious across many sessions:

- **survey** — pick the Source Adapter, snapshot the source, measure the Collapse Ratio, probe the CLI, create the Migration Directory. Refuses when the source folder is not version-controlled.
- **map** — build the Step Map, one distinct Source Step at a time. Owns the compare-to-source check. Where the source carries locators, resolves elements in the same reading.
- **resolve-elements** — runs only when the adapter declares that the source carries no locators.
- **assemble** — build tests from reviewed rows. Owns the document-order and nesting check.

Plus **write-an-adapter**, which produces a new Source Adapter document.

**No verification skill**, by ADR-0005. Compare-to-source lives inside `map`;
order and nesting live inside `assemble`. A Phase does not finish until its own
checks pass. The Check Record is the only verification artifact that outlives a Phase.

**A resume command** is the session entry point. It reads the Migration Directory and
reports the active Phase, unreviewed Step Map rows, unanswered Application Facts, and
whether the installed CLI build has changed. It is the answer to a Migration spanning
many sessions.

**Any skill may raise a question.** Questions arise mid-work, so asking is not a skill.
What lives outside a Phase is the outstanding question: one file of open questions in
the Migration Directory, appended to at the moment a question arises, cleared only by
an answer.

**Migration Directory** at `.testsigma/migration/` inside the source suite, by
ADR-0002. One file per concern, each independently readable and diffable, because a
person reviews them and they land in the source repository's diffs:

- the Step Map, as a table — the largest artifact
- Platform Facts and Application Facts, as two separate files, because who can answer them is the distinction that matters
- open questions
- Residue, with a cause and the reasoning per entry
- the Check Record, per Unit of Work
- the source snapshot reference and the CLI build recorded at start

**Check order** is fixed by ADR-0001: Validity, then compare-to-source, then tenant
acceptance, then round trip, then render-check. Compare-to-source sits second
deliberately, against cheapest-first, because it needs no tenant and is the only
check with a record of finding anything. A check that cannot run is recorded as not
checked and never as a pass.

**CLI coupling** is by probe, never by pin, per ADR-0003. Each check names the
diagnostic code it relies on. An absent code downgrades that check to not checked.
Where the plugin can compute a property itself it does: the document-order property
is that for every step with a parent, the child's order lies strictly between the
parent's order and the parent's next sibling's order, or infinity where there is no
next sibling. That is arithmetic over the step list and holds regardless of CLI
version.

**Adapter declarations.** Every Source Adapter declares three independent properties.
The two shipping adapters happen to cover all three in both directions, which is why
a third adapter is not needed for coverage:

| | hides sequence behind a helper | carries locators | values carry their own language |
|---|---|---|---|
| Cucumber over Java page objects | yes | yes | no |
| Tosca subset export | no | no | yes |

**Tosca reading**, established by reading a real export rather than documentation. A
`.tsu` is gzipped JSON: one flat array of entities, each with an object class, a GUID
surrogate, string attributes, and associations by surrogate. Order is carried only by
position within the association arrays; no entity has an order, index or sequence
attribute, so a reader that walks the entity list in file order produces a scrambled
sequence that looks complete. The export is transitively closed, so reusable step
blocks and the library they live in are included and true sequence is recoverable
from the file alone. It contains no locators of any kind: no module attribute
entities, and no identification parameters. Control flow is explicit, as nodes with
branch folders. Data-driven tests appear as a template plus instances, so migrating
the instances rather than the template yields N duplicated tests.

**No tenant is required** for survey, mapping, element resolution from source, or
assembly. Only the third and fourth checks need one. The plugin must remain fully
useful offline, and a missing tenant downgrades those checks rather than blocking work.

## Testing Decisions

A good test here asserts external behaviour and nothing about internal wording. For a
plugin made of documents, "external behaviour" has two distinct meanings, and they
need two seams.

**Seam 1 — the document contract.** One pytest suite at `plugins/testsigma/tests`,
mirroring the existing style in `plugins/arcus/tests`, which already tests a skill by
parsing its frontmatter and asserting that the body names the required procedure and
does not name the wrong invocations. Prior art is the arcus plugin's skill test; the
package layout and pytest configuration follow its `pyproject.toml`.

What this seam asserts:

- every skill document parses, and its declared name matches its directory
- each skill's description contains the words an Operator's request would actually carry, since the description is what gets matched against a natural-language request
- the mapping skill's body requires the compare-to-source check and requires opening a helper for sequence
- the assembly skill's body requires the document-order and nesting check
- no skill exists whose job is verification, which is ADR-0005 expressed as a test
- each of the two adapters declares all three properties, with an explicit value for each
- the resume command names the Migration Directory and reports the four things it must report
- the Migration Directory's file set is named consistently across the skills that write it

What it must not assert: exact phrasing, section ordering, or anything that makes
rewording a document a test failure. The test checks that a required instruction is
present, not how it reads.

**Seam 2 — behavioural evals.** The document contract can only prove a skill says the
right words, not that it steers an agent. The faults this plugin exists to prevent are
behavioural, so the higher seam is `claude plugin eval`.

**This seam is blocked today.** `claude plugin eval` is in early access and is not
enabled on this machine. The installed Claude Code is 2.1.259, well past the 2.1.224
that the unified result document needs, so the gate is entitlement rather than
version. Enablement is an environment variable obtained from Anthropic. Nobody should
try to enable it by editing a settings file. So the eval cases get authored as part of
this work, because they are only files, and they begin running when the gate opens.
Seam 1 carries the suite until then, and the spec should not pretend otherwise.

Mechanics, so the cases are authored correctly the first time. Cases live in `evals/`
beside the plugin, one directory per case, each holding a required `prompt.md` whose
frontmatter names the case, its tags, its run count and the plugin under test, plus a
`graders/` directory. Fixtures are declared in an optional `case.yaml` under
`context.add_dirs`, and are copied into a fresh throwaway workspace per run rather
than mutated in place, which is what makes a fixture suite safe to convert against
repeatedly.

Six grader types are available. Four are deterministic and are where the weight
belongs: `tool_used` (was a given tool or skill invoked, matched against its input),
`tool_order` (did one precede another), `file_exists` (did the agent write a named
file), and `regex` over the agent's last message, the event trace, or the contents of
a file it produced. Two are model-judged and noisy: `llm`, a free-text criterion, and
`baseline`, a comparison against a reference file.

That split determines what each eval can honestly assert:

- **Deterministic, and the primary assertions.** That the mapping skill was actually the skill invoked. That the agent read the page-object file before writing a Step Map row, which `tool_order` expresses directly and which is the whole composite-step discipline in one check. That an open question was written to the questions file. That no test file was written for a scenario with an unresolved element.
- **Model-judged, used sparingly.** Whether the agent reported a helper's true sequence rather than the source line's implication. Whether it raised a question instead of guessing. Whether a question it raised is free of code, paths and diagnostic codes. These are the checks that matter most and the ones that cannot be made deterministic, so they carry an accepted flakiness cost and their criteria must be written narrowly.

Ablation is the reason this seam is worth its cost. The default mode runs each case
both with and without the plugin and reports the delta, so an eval measures whether
the skill document changed the agent's behaviour rather than whether a capable model
happened to do the right thing anyway. For a plugin that is nothing but instructions,
that delta is the only real measure of whether an instruction is earning its place.

Two fixtures, both small and hand-built rather than lifted from a client suite:

- a Cucumber suite over Java page objects, containing one helper that does more than its Gherkin line implies and one that does less, plus a wait-until helper that re-drives the interface
- a Tosca export containing a reusable step block, a value written in the source's own small language, and a wildcard comparison

Runs are gated on cost with `--max-cost-usd` and scored against `--threshold`. The
result document and an HTML report land under the eval directory. CI consumes the
exit code, where zero means every case met the threshold. Evals run on demand and on
changes to the plugin's documents, never on every commit. A failing eval is a reason
to read the skill document, not automatically a bug in the plugin.

`/skill-doctor` is unrelated to evals and worth running separately. It reports which
skills are actually being loaded and what they cost in context, which for a plugin
made entirely of documents is a real signal about whether a description is triggering.

## Out of Scope

- **Pushing to a tenant.** A Migration ends at files. Pushing is a separate, explicit act.
- **Anything the `arcus` plugin does.** Separate plugin, separate CLI, unrelated concern.
- **A third Source Adapter.** Plain scripts with no helper layer, Robot Framework and Katalon are all deliberately deferred. The two shipping adapters already exercise every declared property in both directions, so a third adds a data point and no new combination.
- **Parsing any source format.** Adapters are documents, by ADR-0004.
- **Reading a Tosca project directly.** Only the subset export is in scope. No Tosca Commander API, no TC-Shell.
- **Concurrency.** Two sessions writing one entity is unsafe and the tooling cannot see it, per the CLI's ADR-0008. The plugin assumes one Migration, one writer, and does not try to arbitrate.
- **Fixing the format's gaps.** Where a spelling does not exist, the plugin routes the case upstream and carries a workaround. It does not extend the format.
- **Recording a tracker configuration.** `/setup-matt-pocock-skills` has never been run in this repository, so there is no `docs/agents/` and no recorded issue tracker. Worth doing separately.

## Further Notes

**The evidence base is one scenario.** Roughly 1 of 35 scenarios of one suite, of one
source shape, converted end to end. The six faults it produced are the requirements
document for the verification half of this spec, and they are a sample of six. Expect
fault classes this spec does not anticipate.

**The first conversion's workspace is not under version control.** It sits unversioned
in a temp directory, and the zip beside it holds the original source only, with no
conversion inside it. That is the failure mode ADR-0002 exists to prevent, and the
Migration that produced this spec would fail the rule the spec now imposes. It should
be put under version control independently of this work.

**Ladder coverage moves underneath a Migration.** One fault class was caught by a
person and, within about a day, had become an automatic refusal in the CLI. That is
why ADR-0003 requires probing rather than pinning, and why the Check Record has to
record what ran rather than what was expected to run.

**One number is unmeasured.** The Collapse Ratio of the evidence suite was never
computed. It decides whether mapping each distinct Source Step once is cheap or
ruinous, which is the affordability assumption underneath the whole mapping Phase. It
should be measured before the mapping skill is built.

**The render-check is unproven.** Two faults were found by a person looking at the
application, and neither came from a question anyone asked. The one structured
question of that kind ever put to an Operator was never answered, and nothing recorded
that it was outstanding. So the fifth check has evidence that looking works and no
evidence at all that asking works. Treat it as a hypothesis and design the tracking of
an unanswered question as the harder half.

**Source exports carry third-party identifying data.** The Tosca export read for this
spec contains an internal corporate username and a fully qualified internal hostname
in ordinary step attributes. A Migration Directory built from such an export will
accumulate that data as a side effect, inside the customer's own repository. Worth a
deliberate decision before the Tosca adapter ships.
