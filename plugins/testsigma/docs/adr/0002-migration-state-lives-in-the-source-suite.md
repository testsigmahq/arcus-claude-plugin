# A migration's state lives inside the source suite

The Migration Directory is `.testsigma/migration/` inside the source suite's own
folder, not a standalone directory beside it. The source repository then versions a
migration's state, so the Step Map, the Platform and Application Facts, and the
Residue travel with the code they describe.

## Considered Options

The alternative, and the earlier decision, was a standalone directory deliberately
outside both the source suite and the `.sigma` workspace, so that re-cloning either
would not destroy it. The reasoning inverts on inspection: a standalone directory is
not versioned by anything, so nothing recovers it, whereas a dot-directory committed
inside the source repository survives re-cloning precisely because the clone brings
it back.

The first conversion demonstrated the failure mode of the old choice. Its workspace
sat unversioned in a temp directory, with no history and no backup, and the zip
beside it held the original source only. A migration's entire evidence base existed
in one uncommitted copy.

## Consequences

A migration now depends on the source suite being under version control, which the
first one was not. A migration should refuse to start against a source folder that is
not version-controlled, rather than writing state into somewhere that cannot keep it.

Where the source repository is read-only to us, the directory is untracked inside
someone else's tree and has the old problem back. That case needs an explicit
durable copy, and it is the known limit of this decision rather than an oversight.
