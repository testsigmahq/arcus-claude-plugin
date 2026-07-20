---
description: Author Testsigma script e2e tests for this repo, validate them, and offer to run them
---

Author end-to-end tests for the current repository in **Testsigma script**.

Invoke the **testsigma-tests** skill and follow it end to end: detect the
application type, pull the DSL reference from the `testsigma` CLI, author the
spec(s) under the repo's tests tree, validate them offline, and offer to run them.

If the user passed a feature/area as `$ARGUMENTS`, scope the tests to it
(e.g. `/arcus:test login flow`); otherwise ask what to cover.
