# The commands of the QI workflow, in one place

Every command string that the QI workflow uses is in this table and in the skill that owns it. A name change in the CLI
then means changing these two places and the few other documents that name the command (search for `arcus `). The
skills say what each command does and what to do with the answer. The CLI says the rest: run
`arcus <entity> <command> --help` when you are unsure of a flag.

**The source of truth is the CLI.** Every command has the form `arcus <entity> <command> [args]`. `arcus help --json`
prints the full command tree as JSON: every entity, command, argument and option. When this table and that output
differ, the output is right. Say so to the user, and use the CLI's name.

Add `--json` to any command to get one JSON object on stdout. Add `--project <folder name or id>` when a repo holds
several projects.

| Step | Command | Mode | Needs sign-in | Owner skill |
|---|---|---|---|---|
| Show the project mode | `arcus project mode show` | both | no | `mode` |
| Show the platforms of the project | `arcus project platforms list` (change: `arcus project platforms add\|remove <platform>`) | both | no | `setup`, `run` |
| Switch the mode (plan, then do) | `arcus project mode set <direct\|qi> --dry-run` then `arcus project mode set <direct\|qi>` | both | qi only | `mode` |
| Set the mode at the start | `arcus project init --project <id> --mode <direct\|qi>` | both | yes | `setup` |
| Read an issue and its cases | `arcus issue show <KEY>` | qi | yes | `context` |
| Read the manual steps of one case | `arcus case show <id>` | qi | yes | `context` |
| Check and format | `arcus test check`, `arcus test fmt` | both | no | `author` |
| Learn the language | `arcus docs list` (every action), `arcus docs show <action>`, `arcus docs show --topic <id>` | both | no | `author` |
| List the browsers (the web run needs the local agent) | `arcus browser list` | both | no | `setup`, `run` |
| Run one test here | `arcus test run <file>` | both | no | `run` |
| Run one test, with a note for reviewers | `arcus test run <file> --note "<why>"` | both | no | `run` |
| Run on a platform | `arcus test run <file> --platform <web\|android>` | both | no | `run` |
| Run on a device, with an app | `arcus test run <file> --platform android --device <serial> --app <apk>` | both | no | `run` |
| List the devices (state `device` is ready) | `arcus device list` or `arcus device list --json` | both | no | `setup`, `run` |
| Run every case of an issue | `arcus issue verify <KEY>` | qi | yes | `verify` |
| Run every case on Android | `arcus issue verify <KEY> --platform android [--device <serial>] [--app <apk>]` | qi | yes | `verify` |
| Plan a push | `arcus test push --dry-run [paths]` | both | yes | `push` |
| Push | `arcus test push [paths]` | both | yes | `push` |
| Bind a file to a case on its first push | `arcus test push <path> --case <id>` | qi | yes | `push` |
| Push a new case | `arcus test push <path> --new` | qi | yes | `push` |
| Push a new case with no issue | `arcus test push <path> --new --unmapped [--issue <KEY>]` | qi | yes | `push` |
| Move a file to another case | `arcus test push <path> --rebind <id>` | qi | yes | `push` |
| Push and accept | `arcus test push [paths] --accept` | qi | yes | `push`, `accept` |
| Accept pushed heads | `arcus test accept <paths>` or `arcus test accept --issue <KEY>` | qi | yes | `accept` |
| Show where files stand | `arcus test status [paths]` | both | qi: yes. direct: no | `sync` |
| Show where files stand in a pipeline | `arcus test status --ci` | both | qi: yes | `sync` |
| Bring QI's head into a file | `arcus test pull [paths]` | qi | yes | `sync` |
| Take QI's head, drop local changes | `arcus test pull <paths> --theirs` | qi | yes | `sync` |
| Keep the file, push onto QI's head next | `arcus test pull <paths> --ours` | qi | yes | `sync` |
| Rebuild local records on a fresh clone | `arcus test pull --rebuild` | qi | yes | `sync` |
| Keep a file as a local test | `arcus test detach <paths>` | qi | no | `sync` |
| Sync a local test with its case again | `arcus test attach <paths>` | qi | no | `sync` |
| Android tools folder | `arcus config set android.toolsDir <folder>` (stores an absolute path) | both | no | `setup` |
| Show the CLI settings | `arcus config show` | both | no | `setup` |

## When a command name changes

Every command follows one rule: `arcus <entity> <command> [args]`. The entities are `auth`, `config`, `project`
(with `platforms`, `sources` and `mode` below it), `test`, `issue`, `case`, `docs`, `browser` and `device`. Old names
are gone, and there are no aliases. When a name changes again: change the table above, the command strings in the owner
skill of each row, the other documents that name the command (the README, `commands/help.md`, `references/` and the
eval cases), and the `CLI_SURFACE` table in `tests/support.py`. Run the tests. They fail on every string that the CLI
no longer has.

## Android settings that are not commands

`ARCUS_ANDROID_TOOLS_DIR` (the tools folder) is read from the shell environment, then from a `.env` file. A `.env` value
must be an absolute path outside the repository. `ARCUS_ANDROID_APPIUM_URL` (use an Appium that already runs) is read
from the shell environment only. The order, the limits and the `android` block of `arcus.json` are in
`${CLAUDE_PLUGIN_ROOT}/references/running.md`.
