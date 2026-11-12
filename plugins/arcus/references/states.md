# States, results, refusal reasons and exit codes

The CLI puts a `next` line on every state and every refusal. That line is the authority. This list helps you explain
it in plain words. If the CLI says something else, trust the CLI.

## Exit codes (all commands)

| Exit | Means |
|---|---|
| `0` | Done |
| `1` | A file was refused, failed, conflicted or did not pass. Or QI or Arcus refused. Or the network failed. Read the JSON. A report has `ok: false` |
| `2` | Not signed in, the sign-in expired, or the project region differs from the signed-in region. Failure code `AUTH` |
| `3` | Wrong use or wrong setup: a QI command in a direct project, no context, a stale context, a closed sprint, a lock that does not fit the mode, a bad flag, a missing tool. A wrong command line (bare entity, unknown command, missing argument, unknown option) has the failure code `USAGE`. Other setup problems have `VALIDATION`. stdout is empty. stderr is one JSON object with `ok: false`, `code`, `exitCode`, `message` and `remediation` |
| `4` | The command needs approval and says the command to run again with `--yes`. Failure code `CONFIRMATION`. The CLI does not use it today |

The same object and the codes are in `${CLAUDE_PLUGIN_ROOT}/references/commands.md`.

## `arcus test status`, qi mode: one state per file

| State | Means | Do |
|---|---|---|
| `pending` | In step with its head. QI has not decided | Nothing. Wait for review |
| `accepted` | The head is the accepted version in Arcus | Nothing |
| `modified` | The file changed after its last push | Run it, then push |
| `behind` | The case moved in QI. The file has no local change | `arcus test pull <path>` |
| `diverged` | The case moved and the file has local changes | `arcus test pull <path>`: it merges |
| `conflict` | The file holds conflict markers from a pull | Resolve the markers, then check, run, push |
| `rework` | A reviewer asked for changes. Comments are in the answer | Read them, edit, run, push |
| `rejected` | A reviewer rejected the head. A kind and a reason come with it | See the kinds below |
| `suggestion` | The story changed. QI suggests new steps | `arcus case show <id>`, update the file, run, read the context again, push |
| `automation_behind` | A reviewer changed the manual steps after this automation | Read the steps, update the file, run, push |
| `unmapped` | The case has no issue yet. Push works, accept does not | A reviewer links it to an issue in QI |
| `changed_after_accept` | A newer head waits after an accept | A reviewer accepts again, or `arcus test accept <path>` if the policy allows |
| `no_shadow` | This machine has no local record of the file | `arcus test pull --rebuild` |
| `missing` | The file is gone | Restore it, or remove its line by `arcus test detach` |
| `local` | Detached: a local test | `arcus test attach <path>` to sync it again |

Rejection kinds: `duplicate` (names the case that already covers it: read it, move missing steps there, or push onto
it with `--rebind`), `wrong` (fix and push), `not_wanted` and `out_of_scope` (ask the developer: detach the file or
delete it). Do not push a rejected file again without the user's say.

## `arcus test status`, direct mode

`new` (never pushed), `changed`, `in_step`, `no_base` (a fresh clone: the push compares with Arcus), `missing`,
`conflict`. No server call.

## `arcus test status --ci`

Exit `1` when a file is in a failing state.

| Mode | Failing states | Other states |
|---|---|---|
| qi | `not_pushed`, `untracked`, `missing`, `conflict` | `in_step`, `behind`, `rejected`, `local`, `case_not_found`, `unchecked` |
| direct | `untracked`, `missing`, `conflict` | `tracked` |

## `arcus test push`, qi mode: result per test file

| Result | Means |
|---|---|
| `would_push`, `would_create` | Dry run only. This is what a push will do |
| `pushed` | A new head on the case. Shows `base -> revision` |
| `created` | A new case. `mapped: false` means it is in the unmapped cases. A `warning` may name a likely duplicate |
| `unchanged` | The file equals its head |
| `skipped` (`local_only`) | The file is detached |
| `refused` | Not sent. See the reasons below |

Refusal reasons: `run_required` (policy needs a run of the file as it is now: run it, push again), `head_moved`
(`arcus test pull`, run, push), `check_failed` (`arcus test check <path>`), `unbound` (give `--case <id>` or `--new`),
`ambiguous_case` (the case id is not under this issue: pick one from `arcus issue show <KEY>`), `element_not_pushed` (push the
element first, or fix it), `already_bound` (the file has a case: push without `--new`), `conflict` (markers in the
file). With `--accept`, a failed accept gives `reason: accept_failed` and a `retry` command. The push still stands.

Errors that stop the whole push (exit `3` unless noted): no context on this machine; a context older than the policy
allows; a closed sprint; a flag that needs `qi` mode in a direct project; region mismatch (exit `2`).

## `arcus test push`, direct mode: result per file

`created`, `updated`, `renamed`, `unchanged`, `refused`, `conflict`, `missing`, `failed`. Each has a message. A
`conflict` means the same step changed in Arcus and in the file. A `refused` file is not sent.

## QI refusal codes (`QI refused: <code>`)

| Code | Say and do |
|---|---|
| `versioning_off` (exit `3`) | The account has case versions off. Stop. Do not change the mode yourself. Tell the user |
| `issue_not_found` | Check the key and the project. For a new issue: `--new --unmapped` |
| `no_sprint` | The issue is not in a sprint. Push new tests with `--new --unmapped` |
| `sprint_closed` | QI takes no new versions for this issue. Read the context again. Or use an issue of the open sprint that links to it |
| `context_stale` | The story changed after you read it. Read the context again, read each case's suggested steps, update, run, push |
| `case_not_found` | Wrong case id or project |
| `policy_forbids` | The user's Arcus role does not allow it. Ask a project admin. Do not retry |
| `project_not_found`, `project_scope_required` | Wrong project, or an old CLI. Update the CLI |

## `arcus test accept`: result per file

`accepted` or `refused`. Reasons from the CLI: `unbound`, `missing`, `no_shadow`, `automation_behind`, `modified`,
`case_not_found`, `case_unmapped`, `head_moved`. Reasons from QI: `head_rejected`, `case_changed`, `policy_forbids`
(leave it to the reviewer), `arcus_unavailable` and `arcus_error` (run the `retry` command). `ok: false` gives exit `1`.

## `arcus test pull`: result per file

`up_to_date`, `updated`, `merged`, `conflict` (exit `1`; markers are in the file), `kept_ours`, `taken_theirs`,
`automation_behind`, `automation_unavailable` (a script edited in Arcus cannot be read yet: do not push that file, pull
again later), `rebuilt`, `skipped`.

## `arcus issue verify`: verdict per case

`covered` (passed), `failing`, `missing` (no script in QI, no file), `local_only` (QI holds no script yet: push it),
`rejected` (listed, not run). `ran` says if the file or QI's script ran. `local_differs` means the file is not the text
QI holds. Exit `1` unless every case is `covered` or `rejected`.

## `arcus test run`

JSON `run.status`: `passed`, `failed`, `refused` (did not compile; no run started), `interrupted` (not a verdict).
Exit `0` for passed, `1` for the others, `3` when this machine cannot run it. Only `passed` and `failed` runs are kept
as evidence for a push. See `${CLAUDE_PLUGIN_ROOT}/references/running.md`.
