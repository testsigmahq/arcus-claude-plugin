---
name: push
description: Use when a developer wants to send Arcus tests and elements from the repo, or asks what a push would do. Works in both modes (direct pushes tests to Arcus, qi pushes tests to QI as case versions and elements to Arcus). Checks the mode first, always runs arcus test push --dry-run, shows the plan in plain words, and pushes only after the user says yes. Then explains every result and refusal and gives the next step. Does not write tests or run them.
---

# Push: send tests and elements

A push changes what the team sees. Never push first. Show the plan, wait for a yes, push, then explain. The CLI decides what can be sent. You put its answers in words.

Exit `2` (not signed in, expired, or a region mismatch) or no project: run `/arcus:setup`. Never sign the user in.

## 1. Check the mode, then read one file

Run `arcus project mode show`. With several projects ask which one and pass `--project <folder name>` everywhere. Then read exactly one file, and do not read the other:

- `direct`: `${CLAUDE_PLUGIN_ROOT}/references/push-direct.md`
- `qi`: `${CLAUDE_PLUGIN_ROOT}/references/push-qi.md`

That file holds the files, the flags, the plan, the checks before the yes, the result and the failures for that mode. The user may want the other mode: that is `/arcus:mode`, not a push.

## 2. Dry run, always

```
arcus test push --dry-run --json [flags] [paths] --project <name>
```

Nothing is sent or written. It does read QI and Arcus, so it needs the sign-in. The exit code is `1` when any file is refused, conflicts or fails. All checks that stop a real push run here too, so a refusal here is a refusal there. The file of the mode says how to read the JSON.

## 3. Show the plan, in words

Begin with the place, in the words of the mode file. Then one line per file, then what stands out.

## 4. Ask

Ask for a clear yes to push exactly this, to that place. A past yes does not carry over. Say what the mode file asks you to say before the yes.

Refused or conflicting files: do not push them. Say which and why, and offer the fix. To send the clean files now, push with their paths only.

## 5. Push

```
arcus test push --json [flags] [paths] --project <name>
```

Compare the result with the plan and report any difference. Say where it went, in the past tense, with the same words as the plan. A push that stops half way is safe to run again. The mode file says what to tell the user after the push.

## Failures

The table is in the file of the mode. This row holds for both:

| You see | Tell the user |
|---|---|
| `failed` | An unexpected error. Report it as it is. A rerun is safe |

Automation turned off in Arcus is for a project admin. Never change project settings.

## Never

- Push without a dry run and a yes for this push, or read `summary` as the outcome.
- Sign in, delete anything, or change project settings.
