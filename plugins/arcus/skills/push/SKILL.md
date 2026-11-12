---
name: push
description: Use when a developer wants to send Arcus tests and elements from the repo, or asks what a push would do. Works in both modes (direct pushes tests to Arcus, qi pushes tests to QI as case versions and elements to Arcus). Always runs arcus push --dry-run first, shows the plan in plain words, and pushes only after the user says yes. Then explains every result and refusal and gives the next step. Does not write tests, run them, or accept.
---

# Push: send tests and elements

A push changes what the team sees. Never push first. Show the plan, wait for a yes, push, then explain. The CLI decides
what can be sent. You put its answers in words. See `${CLAUDE_PLUGIN_ROOT}/references/workflow.md` for the modes, and
`${CLAUDE_PLUGIN_ROOT}/references/states.md` for every result and reason.

Exit `2` (not signed in, expired, or a region mismatch) or no project: run `/arcus:setup`. Never sign the user in.

## 1. Mode and files

Run `arcus project mode`. With several projects ask which one and pass `--project <folder name>` everywhere.

- `direct`: a test and an element go to Arcus.
- `qi`: an element goes to Arcus first. A test goes to QI as a new head on the working line of its case. The push also
  needs: an issue context on this machine (`/arcus:context`), younger than the policy allows, for an issue whose sprint
  is open; and, when the policy says `run: required`, a run of the file as it is now (`/arcus:run`).

Paths: the files the user named, or the files you just changed, else no path (the whole project; files that did
not change come back `unchanged`). In qi mode, `arcus status` first shows where each file stands.

A test file needs a case in qi mode:

| The file | Flag, for the first push only |
|---|---|
| Automates a case from `arcus context` | `--case <id>` (one file per command) |
| Is a new test with no case | `--new` |
| Is new, and the issue is not in a sprint or QI does not know it | `--new --unmapped`, and `--issue <KEY>` as a hint for the reviewer |
| Must move to another case (a duplicate warning names it) | `--rebind <id>` (one file) |

After the first push, `arcus.lock` binds the file. Push it again with no flag. Ask the user before `--new`: a new case
is something the reviewer did not ask for.

## 2. Dry run, always

```
arcus push --dry-run --json [flags] [paths] --project <name>
```

Nothing is sent or written. It does read QI and Arcus, so it needs the sign-in. The exit code is `1` when any file is
refused, conflicts or fails. All checks that stop a real push run here too, so a refusal here is a refusal there.

- direct: JSON has `destination` (`project` and `folder`, each an `id` and a `name`, the name `null` when Arcus would
  not give it; `region`; `arcusUrl`) and `files[]`. Each file has `result`, `message`, `diagnostics` and for a test a
  `plan` (`keep`, `edit`, `new`, `remove`, `move`). Read each file's `result`. Do not read `summary`: it counts only the
  offline findings.
- qi: the JSON has the Arcus part (`files[]`, for elements) and `cases` with `issue`, `build` and `files[]`. Each
  case file is `would_push` (with its base), `would_create`, `unchanged`, `skipped` or `refused` (with `reason`, `message`
  and `next`).

## 3. Show the plan, in words

Begin with the place:

- direct: `This goes to the Arcus project "<project>", in the folder "<folder>", at <arcusUrl>.` A name that is `null`:
  give the id and say Arcus did not give the name.
- qi: `Tests go to QI, as new versions of these cases, under issue <KEY>. Elements go to the Arcus project "<project>".`
  Say the policy: a reviewer accepts, so nothing joins the accepted suite yet.

Then one line per file. Direct: `created` is a new Arcus test with N steps; `updated` changes N steps (steps changed in
Arcus are merged into the file: `fromArcus`); `renamed` changes the title for everyone; `conflict` and `refused` are not
sent (give the reason); `missing` is skipped. Qi: `would_push` adds a head to case <label>; `would_create` makes a new
case (say `unmapped` when it has no issue: a reviewer must link it before it can be accepted); `refused` gives the
reason and `next`. Call out: how many new cases or tests, any rename, and a changed element with how many tests use it
(its whole locator list is replaced for all of them).

## 4. Ask

- If a file in a qi push was never run here and the policy is `run: required`, the dry run says `run_required`: offer
  `/arcus:run`. If the policy is `optional` or the project is direct, say once that the file was not run, and offer a
  run. Do not hold a direct push back for it. A qi push with an `optional` policy and no run is allowed: the dry run,
  the result and `arcus status` show `no local run`. It is not a pass.
- The plan shows, for each file, the run it uses: its platform (and, on Android, the device) and its result. The gate
  takes the newest matching run of any platform, so an Android run can be the evidence for a test that also runs on
  web. Say the platform to the user.
- A failed run counts as a run. If the last run failed, say so: the push would send the file with a failed result.
  Ask if the user still wants it. A failure caused by the app is a finding, not a reason to change the test.
- Ask for a clear yes to push exactly this, to that place. A past yes does not carry over.
- Refused or conflicting files: do not push them. Say which and why, and offer the fix. To send the clean files now,
  push with their paths only.

## 5. Push

```
arcus push --json [flags] [paths] --project <name>
```

Compare the result with the plan and report any difference. Say where it went, in the past tense, with the same words
as the plan.

- direct: `Pushed to the Arcus project "<project>", folder "<folder>".` Never say only "pushed". Always give the `url` of each
  pushed test as a link. A CLI with no `url` gives none: then say to open `arcusUrl`, the project, the folder, and look
  for the title. Never build a link yourself. A new test is in the folder shown. An updated test stays where it was.
- qi: for each file `pushed` (`base -> revision`), `created` (the new case id; a `warning` may name a likely duplicate:
  show it and the `--rebind` it offers), `unchanged`. Say the head is **pending review**. Show `took the suggested steps`
  when it appears. The files do not change, but `arcus.lock` does: tell the user to commit it with the tests.

A push that stops half way is safe to run again. Do not add `--accept` unless the user asks to accept too: see
`/arcus:accept`.

## 6. After the push

- direct: the CLI rewrites each pushed file to Arcus's text. Tell the user to read `git diff`. Server lines
  (`serverProblems`, `serverWarning`) never undo a push: read them out and offer `/arcus:author`.
- qi: next is review. The user can check with `/arcus:sync` (`arcus status`). Then `rework` means change and push again.

## Failures to explain

| You see | Tell the user |
|---|---|
| `run_required` | The policy needs a run of the file as it is. Run it (`/arcus:run`), then push |
| `head_moved` | The case moved in QI. Pull (`/arcus:sync`), run, push |
| `check_failed`, direct `refused` with diagnostics | The offline check failed. `/arcus:author` fixes it |
| `unbound` | No case yet. Say which flag fits (`--case`, `--new`) and ask |
| `ambiguous_case` | That case is not under this issue. Pick from `arcus context` |
| `element_not_pushed` | Push the element first, or fix why it failed |
| direct `refused: A test named "…" already exists` | Another test has that title. Pick another |
| direct `conflict` | The same step changed in Arcus and in the file. Undo the local edit to it, or make the file equal Arcus's text. Delete the base in `.arcus/base/` only if the user says to |
| `failed` | An unexpected error. Report it as it is. A rerun is safe |
| Whole-run error, exit `3` | Closed sprint, stale or missing context, a QI flag in a direct project, or a lock that does not fit the mode. Give the message and its `remediation` |
| `QI refused: …` | Use the table in `states.md` |

Automation turned off in Arcus is for a project admin. Never change project settings.

## Never

- Push without a dry run and a yes for this push, or read `summary` as the outcome.
- Get past a refusal by editing `arcus.lock` or `.arcus/`, or by renaming files.
- Add `--new`, `--unmapped` or `--accept` on your own.
- Sign in, delete anything, or change project settings.
