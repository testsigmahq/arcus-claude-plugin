---
description: Clear locally stored Testsigma credentials for Atto
---

Removes the stored refresh token from your OS keychain and clears the local config file. Future hook events will not be ingested until you run `/atto:login` again.

Server-side session revocation is not yet supported — sign out only clears local state.

Execute:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/auth/cli.py" logout
```
