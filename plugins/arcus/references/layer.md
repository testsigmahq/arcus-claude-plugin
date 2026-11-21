# The rules of the layer

In a qi-mode project, QI is the alignment and verification layer of the developer's coding agent. QI says what an issue expects. The agent builds the code. Then the agent shows the gaps between the code and the expectation before the work reaches QA. `/arcus:align` is the start of the work. `/arcus:prove` is the end. These seven rules hold for both.

1. **The plugin suggests.** It never dictates build order, when to write a test, or how the app is built and started. Where a skill says "you can" or "a useful order is", it is a suggestion. The developer decides how the app runs. Ask when you do not know.
2. **Every case QI returns is the expectation.** QI has no "verified" state for a case today.
3. **Read the steps of every case before the first code edit.** Keep them so that they survive a compaction of the session. How you keep them is your choice.
4. **You may repair a test. You never weaken one.** Remove no step and no check (`verify`) that the case has. Do not change an expected value to what the app shows.
5. **A failure does not block the developer.** "Done" means every case passes, or the developer says it is done. A loop of fix and run again is a suggestion, not a duty.
6. **Verification is the default for an issue that has cases.** The developer can say "skip".
7. **Every push needs the developer's yes.**

## Also

- No cases for the issue: do not stop. Go on from the Jira text, and say that QI gives no expectation.
- No issue named: ask once. With no answer, go on and do not ask again.
- The plugin has no hooks. The skill text carries the default.
- Do not guess an `arcus` command or flag from memory. Use `${CLAUDE_PLUGIN_ROOT}/references/commands.md` or `arcus <command> --help`. If they differ, the CLI is right.
