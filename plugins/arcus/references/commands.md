# The commands of the QI workflow, in one place

Every command string that the QI workflow uses is in this table and in the skill that owns it. A name change in the CLI
then means changing these two places and nothing else. The skills say what each command does and what to do with the
answer. The CLI says the rest: run `arcus <command> --help` when you are unsure of a flag.

Add `--json` to any command to get one JSON object on stdout. Add `--project <folder name or id>` when a repo holds
several projects.

| Step | Command | Mode | Needs sign-in | Owner skill |
|---|---|---|---|---|
| Show the project mode | `arcus project mode` | both | no | `mode` |
| Switch the mode (plan, then do) | `arcus project mode set <direct\|qi> --dry-run` then `arcus project mode set <direct\|qi>` | both | qi only | `mode` |
| Set the mode at the start | `arcus init --project <id> --mode <direct\|qi>` | both | yes | `setup` |
| Read an issue and its cases | `arcus context --issue <KEY>` | qi | yes | `context` |
| Read the manual steps of one case | `arcus context --case <id>` | qi | yes | `context` |
| Check, format, learn the language | `arcus check`, `arcus fmt`, `arcus docs` | both | no | `author` |
| Run one test here | `arcus run <file>` | both | no | `run` |
| Run one test, with a note for reviewers | `arcus run <file> --note "<why>"` | both | no | `run` |
| Run on a platform | `arcus run <file> --platform <web\|android>` | both | no | `run` |
| List the devices | `arcus devices list` | both | no | `setup`, `run` |
| Run every case of an issue | `arcus verify --issue <KEY>` | qi | yes | `verify` |
| Plan a push | `arcus push --dry-run [paths]` | both | yes | `push` |
| Push | `arcus push [paths]` | both | yes | `push` |
| Bind a file to a case on its first push | `arcus push <path> --case <id>` | qi | yes | `push` |
| Push a new case | `arcus push <path> --new` | qi | yes | `push` |
| Push a new case with no issue | `arcus push <path> --new --unmapped [--issue <KEY>]` | qi | yes | `push` |
| Move a file to another case | `arcus push <path> --rebind <id>` | qi | yes | `push` |
| Push and accept | `arcus push [paths] --accept` | qi | yes | `push`, `accept` |
| Accept pushed heads | `arcus accept <paths>` or `arcus accept --issue <KEY>` | qi | yes | `accept` |
| Show where files stand | `arcus status [paths]` | both | qi: yes. direct: no | `sync` |
| Show where files stand in a pipeline | `arcus status --ci` | both | qi: yes | `sync` |
| Bring QI's head into a file | `arcus pull [paths]` | qi | yes | `sync` |
| Take QI's head, drop local changes | `arcus pull <paths> --theirs` | qi | yes | `sync` |
| Keep the file, push onto QI's head next | `arcus pull <paths> --ours` | qi | yes | `sync` |
| Rebuild local records on a fresh clone | `arcus pull --rebuild` | qi | yes | `sync` |
| Keep a file as a local test | `arcus detach <paths>` | qi | no | `sync` |
| Sync a local test with its case again | `arcus attach <paths>` | qi | no | `sync` |
| Android tools folder | `arcus config set android.toolsDir <folder>` | both | no | `setup` |

## A rename

The names `context`, `pull`, `accept`, `status`, `attach`, `detach` and `verify` may change to a noun and verb form
later. When that happens: change the table above, the command strings in the owner skill of each row, and the
`CLI_SURFACE` table in `tests/support.py`. Run the tests. They fail on every string that the CLI no longer has.
The README and the help command name no flags, so they need no change.
