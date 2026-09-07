> **Superseded, 2026-09-03.** The `/grill-with-docs` session this file was written
> for has run. Its outcomes are in `CONTEXT.md` (the glossary) and `docs/adr/`
> (ADR-0001..0005) beside this file, and those win wherever they disagree with what
> follows. Two claims below are now known to be wrong: "no source export carries
> locators" is false for a page-object source, and a Tosca `.tsu` is readable gzipped
> JSON rather than an opaque format. Read this file only for the fault evidence in
> section 2, which is still the requirements document.

# Handoff — designing the Testsigma migration plugin

**Next session's focus:** design and build a Claude Code plugin whose skills run a
test-suite migration into Testsigma `.sigma` format, over many sessions, for **any**
source — Cucumber/Java, Tosca `.tsu` exports, other frameworks, framework-less
projects. Not fixed to the one suite we have converted.

Written 2026-09-03. The evidence below comes from converting **one** scenario of a
real suite end to end. That conversion is the requirements document; this file is its
summary.

---

## 1. Start here, and what not to re-litigate

A `/grill-with-docs` on this exact question was **started and paused** at the top of
the previous session. Its glossary is already written:

    ~/repos/all/arcus-claude-plugin/plugins/testsigma/CONTEXT.md

Terms defined there: Operator, Migration, Migration Directory, Phase, Source Step,
Source Adapter, Collapse Ratio, Step Map, Element Resolution, Residue.

**Settled — do not re-open:**

- `arcus` and `testsigma` are separate plugins with separate CLIs. What the arcus
  plugin does is irrelevant here.
- Target is `.sigma`. Not code-v2, not `.spec.ts`.
- Unit of work: convert per Source Step, then assemble.
- Source adapters are files, so a new source format is a file, not a code change.
- Migrations are large: many days, many sessions. Without a fixed workflow "the
  activity just does not work at all" (user's words).
- The Operator may not read code but knows Testsigma. Questions to them must be in
  Testsigma vocabulary — never code, never stack traces.
- The flow ends at files. Pushing to a tenant is a separate, explicit act.
- Snapshot the source at the start of a migration.
- Use a local build of the CLI for now, not a published npm package.

**Still open when it paused:** Step Map row format; what an Operator question may
contain; element/locator resolution strategy.

---

## 2. The finding that should drive the design

One scenario was converted. It passed `validate`, `push` preflight and a full
round trip — clean, first time. **It was still wrong in six ways.**

| Fault | What actually caught it |
|---|---|
| A click the source's page object does not perform | re-reading the Java |
| A poll loop flattened into a passive wait | re-reading the Java |
| A structural JSON assertion weakened to a substring match | re-reading the Java |
| Three searches missing a conditional expand + clear | re-reading the Java |
| A date format the app rejects | **the user, looking at the app** |
| Conditional bodies rendered outside their block | **the user, looking at the app** |

Nothing automated caught any of them. Every one produces a test that **runs and
passes** while testing something weaker or different — which is the defining
property: executing it does not find them.

**So the plugin's hard problem is verification, not translation.** The three skills
with no tool behind them today:

1. **Compare-to-source** — step-by-step, against the source's *implementation*, not
   its surface syntax.
2. **Render-check** — look at the converted artifact as the target app draws it.
3. **Classify-what-cannot-be-expressed** — and put it to the Operator as a decision.

### 2a. The composite-step trap (source-agnostic)

The single most productive error class. A source line hides a multi-step helper, and
the helper is **not** what the line implies:

- `Select "X" Reason Code` → the page object only sends text. *Less* than it looks;
  we added a submit click that does not exist.
- `Search LPN with Variable Name` → clicks an expand icon when the field is hidden,
  then clears, then types, then presses Enter. *More* than it looks.

Neither is visible from the feature file. Both need the helper opened for **sequence**,
not just for locators. Tosca modules and reusable test-step-blocks have the same
property, as does any framework with a page-object or keyword layer.

### 2b. "Wait until X" helpers are usually loops

This suite's polling helpers **re-drive the UI** while waiting (re-entering a filter,
pressing Enter, clicking refresh). Flattened to a passive `waitUntil*` verb they look
right and behave differently. Treat every wait/until/refresh-until helper as a loop
until the source proves otherwise.

### 2c. Expressibility gaps are real and must reach the Operator

Three met in one scenario:

- No verb for "attribute X is present inside JSON object Y" → downgraded to a
  substring check. Recorded in the test's own `description`.
- `PREFIX + timestamp` id composition had no spelling until `gen.string.paramSubstituter`
  was found; `gen.string.concat` is variadic and currently unspellable.
- Iteration over runtime-collected data has **no** `for` spelling — every Testsigma
  loop verb iterates a test-data profile. Unrolling vs synthesising a TDP changes what
  the test means, so it is the Operator's decision, never a converter's default.

### 2d. A class worth naming: stated-but-unenforced rules

Two instances: interpolation refused in a step slot, and wire markers written into a
generator argument. Both were stated in the format's own docs and enforced nowhere, so
files written against them compiled and failed later. Cheapest class of bug to fix,
most expensive to find in the field.

---

## 3. Source-agnostic: what we know and do not

Deep evidence exists for exactly **one** source shape: Cucumber/Gherkin over a Java
page-object layer. We have **none** for Tosca `.tsu`, other frameworks, or
framework-less projects.

That is a genuine gap in the requirement the user has stated, and it is a reading task
rather than a design one. Worth running `/research` as a background agent on the Tosca
export format before or during the grilling.

---

## 4. What exists, and where

**The converted workspace** (source and conversion side by side):

    ~/temp/MAWM_SeleniumAutomation-TestSigma30/
      src/test/resources/FeatureFiles/   the Cucumber source (16 features, 35 scenarios)
      src/test/java/web/Pages/           page objects — where sequence lives
      tests/testsigma/                   the .sigma conversion

Converted and clean: one scenario (88 steps), three reusable step groups, eight
screens / 46 elements, plus two deliberate probes kept as regression fixtures.
Roughly 1 of 35 scenarios.

**Suite shape, measured — do not re-derive:**
- 35 scenarios: 5 need a real mobile APK, 21 use a *web* "WM Mobile" second window,
  9 are single-window web. "Mobile" means two different things; conflating them
  overstates the APK dependency five-fold.
- No `Scenario Outline` / `Examples` anywhere. The only genuine loop is refresh-until.
  Apparent iteration is unrolled indexed access.
- Several step definitions are invoked by no feature file at all (dead code). The same
  was true of the suite's service accounts.

**The CLI being targeted:**

    ~/repos/active/testsigma-cli      (symlink to ~/repos/all/testsigma-cli)
      CONTEXT.md                      the format's glossary — read this first
      docs/adr/                       ADR-0001..0015; 0008 and 0015 matter most here
      .scratch/sync/                  specs and research

Workspace layout is `tests/testsigma/<project>/<application>/<version>/` with
`project.sigma` / `application.sigma` / `version.sigma` markers. `testsigma attach`
resolves three names against a tenant and writes the ids; it never creates.

**Prior memory** (already loaded each session):

    ~/.claude/projects/-Users-rahul-repos-active/memory/
      mawm-sigma-conversion.md
      testsigma-cli-live-push-findings.md

---

## 5. Cautions

- **The CLI is under active development in a parallel session.** ~17 defects were
  found and fixed during the conversion. Pull and rebuild before trusting behaviour;
  do not assume a bug described anywhere is still present.
- **Do not treat a clean round trip as proof of correctness.** It reconstructs from
  parentage and cannot see document-order faults, weakened assertions, or missing
  steps. It is one rung of five.
- **Concurrent pushes are unsafe and the tooling cannot see it.** Two sessions pushed
  one entity minutes apart; both passed preflight because each read the state it then
  replaced. Recorded in ADR-0008. Agree ownership of an entity before writing to it.
- **Credentials.** The tenant is reached through `TESTSIGMA_HOST` and
  `TESTSIGMA_API_KEY` environment variables. Values are **not** recorded here and must
  not be. The source repo's `Config/*.yml` contains live-looking third-party secrets —
  reference file and key, never the value.
- The plugin work needs **no tenant at all**. Authoring and `validate` are fully
  offline.

---

## 6. Suggested skills

1. **`/grill-with-docs`** — the entry point, run from
   `~/repos/all/arcus-claude-plugin/plugins/testsigma`. It resumes the paused thread
   and keeps its paper trail in the `CONTEXT.md` already there. Point it at section 2
   of this file: the design question is the verification ladder, not the translation.
2. **`/research`** — in parallel, as a background agent, on the Tosca `.tsu` export
   format and one other non-Cucumber source. Feeds the grilling; does not replace it.
3. **`/domain-modeling`** — pulled in by the grilling whenever a term is fuzzy or
   overloaded. "Verification", "fidelity" and "residue" all need sharpening.
4. **`/to-spec`** then **`/to-tickets`** once the grilling settles — this is certainly
   a multi-session build. Keep 1–3 in one unbroken context window.
5. **`/implement`** per ticket, `/clear`ing between. Here — and only here — pull in
   **`plugin-dev`**'s `plugin-structure`, `skill-development` and `command-development`
   for the mechanics of writing the plugin.
6. **`/writing-for-agents`** while authoring the skill files themselves.

**Not** `/wayfinder`: the destination is visible and the scope is stated. **Not**
`plugin-dev` first: it builds the artifact, it does not decide which skills exist.
