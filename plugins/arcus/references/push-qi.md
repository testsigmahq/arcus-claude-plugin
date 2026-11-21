# Push in qi mode

Read by `/arcus:push` when `arcus project mode show` says `qi`. An element goes to Arcus first. A test goes to QI as a
new head on the working line of its case. Modes and results are in `${CLAUDE_PLUGIN_ROOT}/references/workflow.md` and
`${CLAUDE_PLUGIN_ROOT}/references/states.md`.

## Files

The push also needs: an issue context on this machine (`/arcus:align`), younger than the policy allows, for an issue
whose place (sprint or ad hoc session) is open; and, when the policy says `run: required`, a run of the exact text of the file (`/arcus:run`).
After any edit, run again.

The push goes into the place saved with the issue context. When the issue is in several places, the developer chooses
one first: `arcus issue show <KEY> --place <id or human id>`. `arcus test push` has no `--place` option. Never choose a
place for the developer.

Paths: the files the user named, or the files you just changed, else no path (the whole project; files that did not
change come back `unchanged`). `arcus test status` first shows where each file stands.

A test file needs a case:

| The file | Flag, for the first push only |
|---|---|
| Automates a case from `arcus issue show` | `--case <id>` (one file per command). It works only when the current issue context is the story of that case: run `arcus issue show <KEY>` for that story first |
| Is a new test with no case | `--new` |
| Is new, and QI does not know the issue or has no place for it | `--new --unmapped`, and `--issue <KEY>` as a hint for the reviewer |
| Must move to another case (a duplicate warning names it) | `--rebind <id>` (one file) |

After the first push, `arcus.lock` binds the file. Push it again with no flag. Ask the user before `--new`: a new case is
something the reviewer did not ask for. When `/arcus:prove` proposes the push of a `local only` test, `--new` is the
flag, and the user's yes covers it.

## The dry run

The JSON has the Arcus part (`files[]`, for elements) and `cases` with `issue`, `build` and `files[]`. Each case file is
`would_push` (with its base), `would_create`, `unchanged`, `skipped` or `refused` (with `reason`, `message` and `next`).
`build` is the last git commit of the repo, so commit your work before a push, or QI sees an older build.

## The plan, in words

Begin with the place: `Tests go to QI, as new versions of these cases, under issue <KEY>, in place <type, title, human id>. Elements go to the Arcus
project "<project>".` Say the policy: a reviewer accepts, so nothing joins the accepted suite yet.

Then one line per file: `would_push` adds a head to case <label>; `would_create` makes a new case (say `unmapped` when
it has no issue: a reviewer must link it before it can be accepted); `refused` gives the reason and `next`. Call out: how
many new cases, and a changed element with how many tests use it (its whole locator list is replaced for all of them).

## Before the yes

- If a file was never run here and the policy is `run: required`, the dry run says `run_required`: offer `/arcus:run`. If
  the policy is `optional`, say once that the file was not run, and offer a run. A push with an `optional` policy and no
  run is allowed: the dry run, the result and `arcus test status` show `no local run`. It is not a pass.
- The plan shows, for each file, the run it uses: its platform (and, on Android, the device) and its result. The gate
  takes the newest matching run of any platform, so an Android run can be the evidence for a test that also runs on web.
  Say the platform to the user.
- A failed run counts as a run. If the last run failed, say so: the push would send the file with a failed result. Ask if
  the user still wants it. A failure caused by the app is a finding, not a reason to change the test.

## After the push

For each file: `pushed` (`base -> revision`), `created` (the new case id; a `warning` may name a likely duplicate: show
it and the `--rebind` it offers), `unchanged` (the file equals its head: nothing was sent). The text line reads
`(vN, pending review)`: say the head is **pending review**. Show `took the suggested steps` when it appears. The files
do not change, but `arcus.lock` does: tell the user to commit it with the tests.

Next is review. A reviewer (QA or a PM) accepts or rejects the test in QI. The user can check with `/arcus:sync`
(`arcus test status`). Then `rework` or `rejected` means change the test, run it and push again.

## Failures to explain

| You see | Tell the user |
|---|---|
| `run_required` | The policy needs a run of the file as it is. Run it (`/arcus:run`), then push |
| `head_moved` | The case moved in QI. Pull (`/arcus:sync`), then push. Run again before the push when the policy needs it or you judge the merge can affect the test |
| `check_failed` | The offline check failed. `/arcus:author` fixes it |
| `unbound` | No case yet. Say which flag fits (`--case`, `--new`) and ask |
| `ambiguous_case` (`case … is not under <KEY>`) | The issue context on this machine is another story than the story of that case. Run `arcus issue show <KEY>` for the right story, then push again with the same `--case` |
| `element_not_pushed` | Push the element first, or fix why it failed |
| `versions_turned_on` | Case versions were turned on after this file was pushed. The file has no base. `arcus test pull <path>`, then push |
| Whole-run error, exit `3` | Stale or missing context, or a lock that does not fit the mode. Give the message and its `remediation` |
| `QI refused: place_required` | The issue is in several places. The developer chooses: `arcus issue show <KEY> --place <id or human id>`. Then push again |
| `QI refused: place_not_found` | QI has no such place. `arcus issue show <KEY>` shows the places. The developer chooses. Push again |
| `QI refused: place_closed` or `sprint_closed` | The place is closed: QI takes no new versions. The developer chooses an open place, or uses an issue of an open place that links to it. New tests with no issue: `--new --unmapped` |
| `versioning_changing` (exit `3`) | QI is changing how it stores case versions. Nothing was sent. Try again later |
| Other `QI refused: …` | Use the table in `states.md` |

## Case versions off

The answers of push carry `versioning: "off"`. Some accounts keep no versions of a case. Then:

- **What works.** Push (of a bound file and of a new case with `--new`), status and verify of the local file.
- **What the CLI cannot tell.** The dry run and the result show no version, no base and no review of a version. Do not say
  `vN` or `pending review`.
- **The last push wins.** A push replaces the automated part of the case. The manual steps stay. There is no conflict
  check and no history. Say this before the yes. A teammate's push before yours is replaced.
- `unchanged`: QI already holds this test, build and run. Nothing was written.
- If the account is later turned to versions on, a push is refused with `versions_turned_on`. The fix is
  `arcus test pull <path>`, then push.

## Never

- Add `--new` or `--unmapped` on your own.
- Get past a refusal by editing `arcus.lock` or `.arcus/`, or by renaming files.
