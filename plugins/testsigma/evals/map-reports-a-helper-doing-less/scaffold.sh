#!/bin/bash
# Put the surveyed suite in the agent's working directory.
#
# The runner's workspace starts empty, and `add_dirs` only grants read access to
# a path rather than seeding the workspace — established by running a case with
# add_dirs alone, where the agent globbed an empty cwd and correctly refused to
# map anything. Cases that need files in cwd scaffold them.
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
