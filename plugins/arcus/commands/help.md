---
description: Show what the Arcus plugin does and how to use it
---

The Arcus plugin helps you write Arcus tests in your repo and send them to an Arcus project. Tests and elements are
`.sigma` files. The `arcus` command-line tool checks them offline and pushes them. The plugin teaches Claude to use it
well, and it sends nothing to Arcus by itself.

## Skills

- `/arcus:setup` — Check that the `arcus` CLI is installed, that you are signed in, and that this repo is bound to an
  Arcus project with the right platforms. Stops with the one thing to do when something is missing.
- `/arcus:author [what to test]` — Write a test (and the elements it needs) as `.sigma` files. Claude learns the
  language from `arcus docs`, writes, runs `arcus check`, fixes, and formats. It does not stop until the check is clean.
- `/arcus:push [files]` — Send tests and elements to Arcus. Always starts with `arcus push --dry-run` and shows you the
  plan. Pushes only after you say yes, then explains every result.

## Typical flow

1. `/arcus:setup` once per repo. Sign in yourself when it asks (`arcus auth login --region us|in|eu`).
2. `/arcus:author login flow` — Claude writes the files and checks them.
3. Look at the files, and at `git diff`.
4. `/arcus:push` — read the plan, say yes, and commit `arcus.lock` with the tests.

## This version

- It does not run tests. Tests are checked and pushed, not run. A clean check means the CLI accepts a test, not that it
  passes against the app.
- There is no `pull`. Arcus is the source of truth. If Arcus has newer edits to a test, the push says so and you bring
  the file to Arcus's text by hand.
- Not supported yet (the CLI refuses them): `api` steps, groups, `host` lines, and sub-folders under `tests/`.

## Files

- `arcus.json` — which Arcus projects this repo holds, their platforms, and where their folders are. Written by
  `arcus init`.
- `arcus.lock` — which file is which Arcus test or element. Commit it.
- `.arcus/` — local state. Not committed.
- `<folder>/<project>/tests/` and `elements/` — the documents.

## Troubleshooting

- `arcus: command not found` — `npm i -g @testsigma/arcus-cli` (needs Node 22 or newer), then `/arcus:setup`.
- `Not signed in` or exit code `2` — run `arcus auth login` yourself, then try again.
- `Which project?` — the repo holds several projects. Say which one, or run from inside its folder.
- A push is refused or in conflict — the plan says which file and why. Run `arcus docs --topic gotchas` for the common
  mistakes.
- Automation is turned off — a project admin must turn it on in Arcus.
