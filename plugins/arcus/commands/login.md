---
description: Authenticate with Arcus so it can capture and ingest your sessions
---

Run the Arcus auth login flow. This opens a browser tab to your Arcus
instance, asks you to log in (if you are not already), and authorizes the
plugin. The token is stored locally in your OS keychain.

## Required pre-flight (do NOT skip)

Each Arcus region is a separate deployment. Signing in to the wrong one
fails, or sends this session's captured prompts and file contents to the wrong
place. Resolve the region before running the login command:

1. List the regions, which also shows where this machine already stands:

   ```bash
   "${CLAUDE_PLUGIN_ROOT}/scripts/arcus-py.cmd" "${CLAUDE_PLUGIN_ROOT}/scripts/auth/cli.py" regions
   ```

   Each line is `key`, label, and a note that is `signed in` for the region this
   machine currently uses, `default` for the fallback, or empty.

2. **If a region is already marked `signed in`**, that is the region to reuse.
   Tell the user which one it is and re-run login against it without asking them
   to choose again — they are only re-authenticating (an expired or revoked
   token), not relocating. Change it only if the user explicitly asks to switch
   regions. If they do, warn them that sessions already captured under the old
   region stay there.

3. **If no region is marked `signed in`**, this is a first login. Show the user
   every region (key + label), say that **United States (`US`) is the default**,
   and ask which one their Arcus account is in. Do NOT guess from their
   locale, timezone, or email domain, and do NOT skip to the execute block.

Execute (only after the region is settled):

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/arcus-py.cmd" "${CLAUDE_PLUGIN_ROOT}/scripts/auth/cli.py" login --region <region>
```

Omitting `--region` reuses the region already stored for this machine, and falls
back to `US` only on a machine that has never signed in. Region keys are
case-insensitive.

If the browser doesn't open automatically, copy the URL printed to stderr and
paste it into your browser. The flow times out after 5 minutes — re-run if you
miss it.

On success the command prints the region and account it signed in to. Check that
line matches what the user expected before moving on.

## Persistence

The chosen region is written to the plugin's `config.json` and reused by every
later call — token refresh, `/arcus:project`, `/arcus:map`, and event ingest. It
survives restarts and token refreshes. It is forgotten only when the user runs
`/arcus:logout`, or switches deliberately by running `/arcus:login` again with a
different region.
