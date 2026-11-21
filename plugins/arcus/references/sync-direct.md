# Sync in direct mode

Read by `/arcus:sync` when `arcus project mode show` says `direct`. A direct push is final, so there is little to bring back. All the states are in `${CLAUDE_PLUGIN_ROOT}/references/states.md`. Always give the `next` line the CLI prints.

## Status

```
arcus test status --json [paths] --project <name>
```

No server call. States: `new` (never pushed), `changed`, `in_step`, `no_base` (a fresh clone: the push compares with Arcus), `missing`, `conflict`. Say each file in one line: the state in words, then what to do. Group by what needs action. Do not act yet. Then `/arcus:push` sends what changed.

## Pull, detach and attach

They are qi commands. Say so, and offer `/arcus:mode` if the user wants qi. A file that Arcus changed is merged into the file by the next push (`fromArcus`): see `/arcus:push`.

## Pipelines

`arcus test status --ci --json` needs no issue and no local state. It makes no server call and exits `1` for `untracked`, `missing` or `conflict`. A pipeline signs in with `ARCUS_API_KEY`, which the user sets. Never ask for the key, and never print it.
