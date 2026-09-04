# Behavioural evals

The pytest suite in `../tests/` proves the plugin's documents *say* the right
things. It cannot prove they *steer an agent*, and every fault this plugin exists
to prevent is behavioural. These cases are the higher seam.

## They do not run yet, and that is not a misconfiguration

`claude plugin eval` is in early access and is not enabled for this account.
Running it prints:

```
`plugin eval` is currently in early access
```

Early access here is an **entitlement**, not a version. The installed Claude
Code is 2.1.260, well past any version minimum, and `claude plugin eval --help`
prints the full option surface — the command exists and is complete, and the
account is not enrolled. There is no settings file that turns this on: the gate
is server-side, so the only way through it is to have the account enrolled.
Until then these cases are files, checked for well-formedness by
`../tests/test_evals.py`, and they begin running the day the gate opens.

## Why ablation is the whole point

The default mode runs each case twice, once with the plugin and once without the
plugin, and reports the delta between the two arms. For a plugin that is nothing but instructions, that delta is
the only honest measure of whether an instruction is doing any work.

A capable model may open the page-object helper unprompted. If it does, the
document telling it to has earned nothing, and the eval should say so rather than
scoring a pass that the model would have earned on its own. A case that passes
identically in both arms is a case that has measured nothing.

A `Skill` invocation cannot happen in the no-plugin arm, so scoring it would
guarantee a delta that means nothing. `claude plugin eval --help` says graders
marked with-only, "incl. `tool_used: Skill`", are treated as a plugin-fired
indicator rather than part of the score — so the `Skill` graders here rely on
that stated automatic behaviour.

**There is an explicit modifier family — `withOnly`, `scored`, `arm` — and no
case here sets one.** It is not needed: the automatic behaviour above already
does what these cases want, and an explicit key would restate it in a second
place that can drift. `arm: both` exists as an override for a grader that should
be scored in both arms, which is not what a `Skill` grader is.

**Three things about the case format are genuinely unconfirmed, and nothing here
guesses at them.** They are written down so the first real run settles them
rather than someone rediscovering each one:

1. Whether `context.add_dirs` resolves relative to the case directory or to the
   plugin root. The paths here are relative to the case directory, and
   `../tests/test_evals.py` asserts they exist from there.
2. Whether several `add_dirs` entries are flattened into one sandbox root or
   nested under each directory's basename. Every prompt here describes the
   fixture files at the root — `.testsigma/migration/step-map.md`,
   `features/journal.feature` — which is only true under flattening. If they
   nest, the prompts need the basename prefixes; the graders' `input_match`
   patterns are unanchored and would match either way.
3. The nested shape of `tool_order`'s `before` and `after`. The field names are
   documented; that each takes `{tool, input_match}` is not. This matters more
   than the other two, because the read-before-write grader is the single most
   valuable assertion in this suite, and a wrong shape would make it silently
   pass without checking anything.

There is no offline validator for these files, so well-formedness is as far as
the pytest suite can get.

## What is asserted, and why the split matters

Deterministic graders carry the weight because they are stable across runs:

- **the skill that ran** — that mapping was routed to the mapping skill at all
- **reading the helper before writing the row** — one ordering assertion that
  expresses the entire composite-step discipline, and the single most valuable
  check here
- **a question written down** — that an unanswered question reached
  `open-questions.md` rather than the transcript
- **no test written for a scenario with an unresolved element** — the refusal,
  checked by the absence of the file

Model-judged graders are used sparingly, only where nothing deterministic
reaches, and their criteria are written narrowly because a broad criterion is a
coin flip:

- whether the agent reported the helper's **true sequence** rather than the
  source line's implication
- whether it **raised a question instead of guessing** at a wildcard comparison
- whether the question it raised is free of code, paths and diagnostic codes

These are the checks that matter most and the ones that cannot be made
deterministic, so they carry an accepted flakiness cost. That is why each case
runs more than once and is scored against a threshold rather than a single pass.

## Fixtures

Both source fixtures are shared with the pytest suite rather than copied, so
there is one hand-built example of each format and no drift between the two
seams:

| Fixture | Holds |
|---|---|
| `../tests/fixtures/cucumber-java/` | a helper that does more than its line implies, one that does less, a wait-named helper that is a loop, and one that delegates |
| `../tests/fixtures/tosca-subset-export/` | a reusable step block, a value in the source's own language, a wildcard comparison, a cycle, an orphan step |

`fixtures/migration-part-done/` is local to the evals: a Migration Directory
already part-way through, with reviewed rows and one Residue entry naming an
unresolved element. It exists so the refusal can be checked without an eval
having to first run a whole mapping stage.

None of the three contains data from any real suite, any client, or any tenant.
They are hand-built, and the traps in them are real shapes met in real suites
rather than invented edge cases.

## Running them, once the gate opens

```bash
cd plugins/testsigma
claude plugin eval . --max-cost-usd 5 --threshold 0.8
```

Exit status is 0 when every case met the threshold, 1 when one did not, and 2 if
the cost ceiling aborted the run. That exit code is what continuous integration
consumes.

The threshold is below 1.0 deliberately: three of the graders are model-judged
and a single flaky verdict should not fail the suite, while a case that fails
repeatedly will drop below 0.8 and will.

**Run them on demand, and on changes to the plugin's documents. Never on every
commit.** They cost money and they are slow. A failing eval is a reason to go and
read the skill document, not automatically a bug.
