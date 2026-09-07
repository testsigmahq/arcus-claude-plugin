# ADR-0008: Detect a changed build, never diff it

## Status

Accepted.

## Context

ADR-0003 says probe the CLI and never pin a version, and ADR-0006 says the
plugin holds no catalogue and asks the installed build instead. Both leave the
same question open: when the build underneath a Migration changes, what happens
to the Platform Facts already recorded and the work already checked.

The obvious answer is to diff what the build declares — its Catalogues, its
Verbs, the Value Kinds each slot accepts — and act on the difference. That is
what the research into this recorded as outstanding for some time.

It is not available. The build has no command that enumerates what it declares;
facts are established one question at a time, through `validate --json` against
a hand-built scratch workspace, which answers about the verb or slot you name
and nothing else. Enumeration is possible only by regular expression over the
minified `dist` bundle, and that route was rejected: it fails by **matching
nothing**, and nothing is indistinguishable from a verb that does not exist. A
diff built on it would report an empty difference most confidently at exactly
the moment the bundle's shape changed.

The second half of the context is a policy. This is an internal tool. It does
not support a source suite against two builds at once, keeps no fallback for a
withdrawn spelling, and offers no backward compatibility: where a build stops
accepting something a converted row relied on, the Operator rewrites those rows
against the installed build. That is a cost paid by a person, and naming them is
part of the decision.

## Decision

The plugin detects that the build has changed and never establishes what
changed.

Detection is the build's identity, compared at the start of every session, as
`cli-probe.md` defines. On a difference, recorded Platform Facts go stale rather
than void — each is re-probed when next relied on — and every Unit of Work
checked under the old build is marked as not checked against the new one.

A differing build is treated as capable of having **withdrawn** a capability as
well as gained one. A withdrawal opens a Residue entry: a gap where the
capability may return, a refusal where it will not.

## Consequences

The response to a build change does not depend on what changed, which is what
makes the diff unnecessary rather than merely unavailable. Re-probe the facts,
re-check the Units, rewrite what the new build rejects — the same three actions
whichever direction the build moved.

The cost is proportionality. A build that changed one unrelated verb is treated
exactly like one that rewrote every catalogue, so a Migration re-establishes
facts it did not need to. That is accepted: the alternative is a diff that
cannot be trusted to be complete, and an incomplete diff is worse than none,
because work would be marked as checked against a capability nobody verified.

The `Standing` of a withdrawal is a judgement rather than a probe, since nothing
here can ask the build whether a missing verb is gone for good. Write `gap`
where it cannot be told, per the rule in `element-resolution.md`, because that
is the reading a later session looks at again.

If the CLI ever gains a command that enumerates what it declares, this decision
is worth reopening. The reason it was made is the absence of that command, not a
preference for detection.
