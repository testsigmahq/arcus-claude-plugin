# Arcus (Claude Code plugin)

Write Arcus tests in your repo with Claude, check them offline, and push them to an Arcus project. The plugin is a set
of skills for Claude Code. The `arcus` command-line tool does all the work and all the talking to Arcus. The plugin
itself sends nothing anywhere.

## What you need

- Claude Code.
- The `arcus` CLI, on your `PATH`: `npm i -g @testsigma/arcus-cli`. It needs Node 22 or newer.
- An Arcus account. You sign in yourself, in a terminal: `arcus auth login --region us|in|eu`.

The plugin holds no list of steps, forms or locators. Claude asks the installed CLI (`arcus docs`) what the language
can say, and `arcus check` decides what is valid. So what you can write is whatever your CLI version accepts.

## Install

This repo is also a marketplace.

**From GitHub:**

```bash
claude plugin marketplace add testsigmahq/arcus-claude-plugin
claude plugin install arcus@testsigma
```

**From a local clone, for development:**

```bash
git clone git@github.com:testsigmahq/arcus-claude-plugin.git
cd arcus-claude-plugin
claude plugin marketplace add ./
claude plugin install arcus@testsigma
```

`claude plugin list` should show `arcus@testsigma` as enabled. To update after a change, bump `version` in
`plugins/arcus/.claude-plugin/plugin.json` and run `claude plugin update arcus@testsigma`.

## Skills

| Skill | What it does |
|---|---|
| `/arcus:setup` | Checks the CLI is installed, you are signed in, and the repo is bound to a project with the right platforms. Stops with the exact next step |
| `/arcus:author [what to test]` | Writes tests and elements as `.sigma` files, learns the language from `arcus docs`, and loops `arcus check` and `arcus fmt` until clean |
| `/arcus:push [files]` | Runs `arcus push --dry-run`, shows the plan in words, pushes after your yes, and explains every result |
| `/arcus:help` | Shows the commands and the usual flow |

**Typical flow:** `/arcus:setup` once per repo, then `/arcus:author <what to test>`, look at the files, then
`/arcus:push`.

## How it behaves

- **Nothing is pushed without a plan you have seen.** `/arcus:push` always starts with a dry run and asks.
- **The CLI decides.** Claude never decides a file is valid, and never writes a step it did not see in `arcus docs`.
- **You sign in, not Claude.** The plugin never handles credentials.
- **Claude does not weaken a test to make it pass the check.** If the only fix loses what a test verifies, it stops
  and tells you.
- **Arcus is the source of truth.** There is no `pull` yet. When Arcus and your file disagree, the push says so, and
  Claude tells you, and does not work around it.

## This version

- Tests are checked and pushed, **not run**. Running comes in the next version.
- Not supported yet, because the CLI refuses them: `api` steps, groups, `host` lines, header lines such as `tags`,
  and sub-folders under `tests/`.
- Sprint and story mapping, and session capture, from earlier versions of this plugin, are gone.

## Privacy

The plugin sends nothing by itself: it has no hooks and no scripts. When you push, the `arcus` CLI sends your tests and
elements to the Arcus project you chose, using your own sign-in. See the
[Testsigma Privacy Policy](https://testsigma.com/privacy-policy).

## Layout

```
.claude-plugin/marketplace.json     the marketplace (name: testsigma)
plugins/arcus/
  .claude-plugin/plugin.json        the plugin manifest
  commands/help.md                  /arcus:help
  skills/{setup,author,push}/       one SKILL.md each
  references/                       notes the skills read when they need them
  tests/                            tests of the documents (pytest)
notes/                              design notes
```

## Tests

The plugin is documents, so its tests check documents: the manifests parse, every skill has a name and a description
and stays inside a size budget, every pointer resolves, and no document names a CLI command or option that does not
exist. Run them from `plugins/arcus/` with `python -m pytest`.
