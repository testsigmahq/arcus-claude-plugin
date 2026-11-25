# Changelog

## 0.1.0

The first version. `/arcus-jit:catch` catches a change before review, on the developer's own stack, after Meta's
just-in-time catching tests (JiTTesting).

- **Regression lane:** the story's own tests (the files `arcus issue show` names for its cases, when this checkout has
  them) run on the change and on its merge base. A story case that breaks blocks the merge, unless the developer fixes
  it.
- **Catch lane:** the `catch-writer` subagent writes catching tests in a fresh session, in the background, by the
  `arcus` plugin's author and run skills. A failing one is a catch. Catches are advisory.
- `scripts/catch.mjs` keeps a test only when it fails on the change, fails again on a re-run, and the base passed or
  failed another way. It runs one test file per `arcus test run`.
- The `catch-judge` subagent rules on each difference from a packet: the story, its cases, the test, each build's
  outcome and screenshots, and the team's rubric. It has only a file reader and never gets the diff.
- The developer fixes each real or unclear difference, or ships it with a one-line reason. Real catches are pushed to QI
  as pending cases either way. Nothing is accepted.
- One PR comment, posted or edited through `gh` after a yes. With a "Ran locally" comment on the PR, the section goes
  into it.
- `arcus-jit.json`, next to `arcus.json`, holds the repo's settings: the address, the commands that serve the base and
  the branch again, the `--var` names, the budget, and an optional judge rubric. Without it the skill stops. It never
  compares with a deployed environment and never runs in CI.
