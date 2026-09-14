# 27 — Describe the `url` command

**What to build:** `cli-probe.md` lists the seven commands this plugin needs, and `url`
is one of them. It is described nowhere else. A reader meets the name in a table and
never learns what it is for.

`url` resolves an upload version's download link, or fetches the bytes with
`--output <path>`. It is uploads-only — every other entity's content is already in
the workspace — and it performs no writes through the API.

**It reads the workspace's memory of the tenant, not the tenant.** This is the
part an earlier draft of this issue got wrong. The version it signs is the
*file's* newest, not the server's latest, and `--version` matches the file's
version blocks too. That is deliberate: a workspace was reconciled against a
particular version, and signing whatever is latest would hand back bytes the
workspace never named.

The consequence has to be written down. Pull uploads on Monday, someone adds a
version on Tuesday, run `url` on Wednesday: you get Monday's bytes, correctly, and
nothing in the output says a newer version exists. The target's steps were
repointed to Tuesday's the moment it landed (ADR-0014). So bytes filed under
`existing/` as evidence can be bytes nothing in the target runs any more.

Two things close it, and the document does both: `pull uploads --write`
immediately before `url`, in the same sitting, because the pull is what re-reads
the tenant and `url` never does — and record the version name beside the fetched
bytes, which `url` prints on its first line. Evidence whose version is recorded
stays true later; a bare file does not.

So what `url` answers that `pull uploads --write` does not is narrower than "is
this the right file": the pull says an upload exists and what it is called, and
`url` produces the bytes of the version this workspace names, which is the only
question it can answer.

**The link.** With no flags it prints the upload, the version, a presigned
object-store URL and how long it lasts — about three hours, and not single-use.
It carries no tenant credentials: the signature is the whole authorisation, which
is what makes it safe to paste in the sense that it cannot open the tenant, and
unsafe in the sense that it is an unauthenticated link to a real file for three
hours. `--json` carries `expiresInSeconds` so nothing parses the URL.

**The flags.** `--output <path>` writes exactly the stored bytes and touches no
`.sigma` and no baseline, which is what makes filing them under `existing/` sound.
Given a directory it uses the server's name for the bytes; a trailing separator is
how a directory that does not exist yet is named. `--force` overwrites a file
already sitting at that path and means nothing else — without it an existing file
is `TSS1426`, and `--force` without `--output` is refused rather than ignored.

**Refusals worth naming.** `TSS1406` the tenant has no such upload, `TSS1402` the
name matches more than one. `TSS1407` is the one a Migration meets: the tenant has
it and this workspace holds no reference file, which the exit resolves by naming
the pull that would create one. `TSS1425` names a version the file does not hold
and lists the ones it does.

**Blocked by:** nothing.

**Status:** ready-for-agent

- [ ] `adoption.md` describes `url` where it describes the upload inventory
- [ ] `--output`, `--version` and `--force` are named with what each is for
- [ ] It says `url` reads the file's version, never the server's latest
- [ ] The staleness that follows is stated, with the pull that closes it
- [ ] The version name is recorded beside the bytes, so the evidence stays true
- [ ] Fetched bytes are stated to be evidence, under the existing rule
- [ ] The link is described as unauthenticated and time-limited, both halves
- [ ] Read-only is claimed as "no writes through the API", never as "unrecorded"
- [ ] No document leaves a command from the seven-command table undescribed
