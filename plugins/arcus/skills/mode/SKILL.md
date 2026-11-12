---
name: mode
description: Use when a developer asks which mode an Arcus project is in, wants to switch between direct and qi, or a command stops because arcus.lock and the project mode disagree. Shows the mode, plans the switch with a dry run, and switches only after a yes. Not for first-time setup (use setup).
---

# Mode: direct or qi

A project works in one mode. `direct` pushes tests straight to Arcus. `qi` pushes tests to QI as versions that a
reviewer accepts. Element files go to Arcus in both. See `${CLAUDE_PLUGIN_ROOT}/references/workflow.md`.

## 1. Show it

```
arcus project mode show --json
```

It gives `mode`, `stored` (false means `arcus.json` names no mode, so it is `direct`), and a `problem` when the lock and
the mode disagree. A command that stops with exit `3` for this reason says the same thing. With several projects, pass
`--project <name>`.

## 2. Switch to qi

Switching changes how every later push works. Ask the user first. Say: tests will go to QI, a reviewer accepts them,
and `arcus.lock` will link each test file to its QI case.

```
arcus project mode set qi --dry-run
```

This reads QI and writes nothing. It needs the sign-in (exit `2`: `/arcus:setup`). Show the plan: each test file and
the QI case it links to.

- A file can come back `not_in_qi` (QI has no case for its Arcus test case: a reviewer imports it first) or
  `no_working_line` (QI has the case but no version yet: a reviewer opens it in QI). Any such file stops the whole
  switch with exit `1`. Say which files and why. Do not work around it.
- After a clear yes: `arcus project mode set qi`. Then run `arcus test status`. Element lines do not change. Tell the user
  to commit `arcus.json` and `arcus.lock`.

## 3. Switch to direct

```
arcus project mode set direct
```

It works only while `arcus.lock` has no QI case lines. A project that has pushed to QI **cannot** go back: the CLI
cannot turn a case line into an Arcus document line, and it says so with exit `3`. Say this plainly. Do not edit
`arcus.lock` by hand. Offer a new project folder in direct mode if the user needs one. The alias `migration` and
`yolo` also mean `direct`.

## 4. Lock and mode disagree

The message says which: direct mode with case lines (`arcus project mode set qi` links them), or qi mode with Arcus
test lines (the same command links them). Show the message and the plan. Do not repair by editing files.

## Never

- Switch without a yes, or edit `arcus.json` or `arcus.lock` to change the mode.
- Switch to qi to get past a refusal in direct mode.
- Push or accept. Hand over to `/arcus:push` or `/arcus:setup` when the mode is right.
