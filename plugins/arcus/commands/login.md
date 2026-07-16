---
description: Authenticate with Testsigma so Arcus can capture and ingest your sessions
---

Run the Arcus auth login flow. This will open a browser tab to your Testsigma instance, ask you to log in (if not already), and authorize the plugin. The token is stored locally in your OS keychain.

Execute:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/auth/cli.py" login
```

If the browser doesn't open automatically, copy the URL printed to stderr and paste it into your browser. The flow times out after 5 minutes — re-run if you miss it.

After login, future hook events will be ingested into Testsigma automatically. To sign out, run `/arcus:logout`.
