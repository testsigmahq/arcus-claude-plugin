# The working copy lives inside the source suite, at a recorded path

The `.sigma` files a Migration authors go inside the source suite's own folder,
under a directory named in `migration.md`. `tests/testsigma/` at the suite root is
the default, and the recorded path is what every later stage and gate reads.

ADR-0002 settled where a Migration's *state* lives and said nothing about where its
*output* lives. The two were treated as one question and only one was answered.

## Considered Options

The alternative was to leave it unstated, which is what the plugin did. That is not
a neutral default: it is a choice made independently by each run.

Two measured runs of the same plugin, from the same prompt shape, chose
differently. One wrote to `tests/testsigma/` inside the suite. The other wrote to a
sibling `work/tests/testsigma/`. Both readings are consistent with what the plugin
said, because the plugin said nothing.

A second alternative was to fix the path absolutely and record nothing. That fails
the case ADR-0002 already admits — a suite whose layout is not ours — and it makes
the gates depend on a convention rather than on a fact the Migration wrote down.

## Consequences

Three failures on the sibling layout, all verified on a live run, and all of them
silent:

The sibling directory is not a git repository, so the converted tests had no
history at all. The run that wrote inside the suite got history by accident of
location rather than by decision, which means neither run was relying on anything.

`migration.md` did not record the path, so a resumed session reading the Migration
Directory could not find the work the previous session produced. That is the
resume story failing at exactly the point it exists for, and it is what makes
adoption unreachable on a resumed Migration: `existing/` is locatable and the work
in progress is not.

`check_committed.py` found two modified files while missing more than forty
`.sigma` files. A gate reporting "nearly clean" over an entirely untracked working
copy is the fault class the gate exists to catch, reproduced inside the gate.

Writing the first tests that script ever had showed that had **two** independent
causes, and the path was the lesser one. `git status --porcelain` collapses an
entirely untracked directory to a single entry — `?? tests/` — so a substring test
for `tests/testsigma` matched nothing at all, and it would have missed the working
copy even on the layout it was written for. The collapse hides more the more work
is uncommitted, which is backwards for a gate. It reads `-uall` now. The lesson is
the narrower one: a live run's symptom was diagnosed from one plausible cause, and
the second was only found by a test that reproduced the layout.

Recording the path rather than assuming it costs one line in `migration.md` and
makes all three answerable by reading rather than by convention. The gates take the
recorded path; a suite that keeps its tests somewhere else says so once.

The known limit is the same one ADR-0002 carries. Where the source repository is
read-only to us, the working copy is untracked inside someone else's tree, and that
case needs an explicit durable copy rather than a path.
