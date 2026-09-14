#!/bin/bash
# Put the surveyed suite in the agent's working directory.
#
# The runner's workspace starts empty, and `add_dirs` only grants read access to
# a path rather than seeding the workspace. Cases that need files in cwd
# scaffold them.
#
# $PWD is the run's workspace; ${BASH_SOURCE[0]} is this file at its real path in
# the repository, in both the single-case and whole-suite invocations.
#
# Copying rather than linking: the agent writes into the Migration Directory,
# and a symlink would write those edits back into the repository.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/fixtures/cucumber-java/." .
cp -R "$here/fixtures/migration-part-done/." .

# The reason-code fact, answered. The scenario the queue puts first turns on
# whether choosing a reason code commits the change, and with that outstanding a
# correct run parks rather than delivering — which is the case next door, not
# this one. Answered here so the only thing left to measure is stopping.
cat >> .testsigma/migration/application-facts.md <<'FACT'
| 2026-09-11 | Does choosing a reason code commit the change on its own, or does the receiving screen need a separate save before the record is updated? | It commits on its own; the receiving screen has no separate save. | the Operator |
FACT
