---
name: accept
description: Use when a developer asks to accept pushed test heads into Arcus in a qi-mode project ("accept CW-412", "push and accept"). Accepting puts the head in the accepted suite in Arcus as Dev accepted. Checks the policy and the file state first, asks for a clear yes, then runs arcus test accept and explains each result. Qi mode only. Not for pushing (use push) or for review in QI.
---

# Accept: take a pushed head into Arcus

In qi mode a push only adds a head to the case in QI. Accept makes that head the accepted version in Arcus, as
**Dev accepted**. This changes the suite the team trusts and runs. A reviewer normally decides it. A developer may do it
only when the policy lists the developer. See `${CLAUDE_PLUGIN_ROOT}/references/workflow.md`.

Direct project: `arcus test accept` stops with exit `3`. Say there is nothing to accept: a direct push is final. Not signed in
(exit `2`): `/arcus:setup`.

## 1. Check before you ask

1. Read the policy: `arcus issue show <KEY> --json`, field `policy.acceptBy`. If a developer is not on the list,
   stop and say the reviewer accepts in QI. QI also refuses with `policy_forbids`.
2. Run `arcus test status --json` (`/arcus:sync` explains it). Only a file in step with its head can be accepted: `pending` or `changed_after_accept`.
   Other states (`modified`, `behind`, `rework`, `rejected`, `unmapped`, `no_shadow`) refuse. Say what each needs
   (`states.md`).
3. Tell the user what will be accepted: each case label, the file, the issue, and that it goes into the accepted suite in
   Arcus. Say if the run on the file failed. Ask for a clear yes for exactly these files. A past yes does not carry over.

## 2. Accept

```
arcus test accept --json <paths> --project <name>
arcus test accept --json --issue <KEY> --project <name>
```

`--issue` needs a context for that key on this machine and takes every bound file of the issue. The CLI sends the
commit, branch and whether the tree is dirty as evidence. To push and accept in one step, `/arcus:push` has `--accept`:
only on the user's ask.

## 3. Read the answer

`ok`, `files[]` (`accepted` or `refused` with `reason`, `message`, `next`) and `retry`. Exit `1` when any file is
refused.

- `accepted`: say the label and the Arcus version. The human id (for example CW-TC-142) appears at the first accept. Tell
  the user to commit `arcus.lock`.
- `refused`: give the reason in plain words and the `next`. The reasons are in `states.md`. For `arcus_unavailable` and
  `arcus_error`, nothing changed: offer the `retry` command, and run it only after a yes. For `policy_forbids`, leave it
  to the reviewer. For `head_rejected`, show the comments (`arcus test status`). Never loop on a refusal.
- A file that is detached is `skipped`. It is a local test.

## Never

- Accept without the policy check and a yes, or accept a rejected or unmapped case.
- Edit `arcus.lock` or `.arcus/` to make a file acceptable.
- Add files to the accept that the user did not name.
