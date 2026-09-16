---
description: Clear locally stored Arcus credentials
---

Removes the stored refresh token from your OS keychain and clears the local config file. Future hook events will not be ingested until you run `/arcus:login` again.

Server-side session revocation is not yet supported — sign out only clears local state.

Execute:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/arcus-py.cmd" "${CLAUDE_PLUGIN_ROOT}/scripts/auth/cli.py" logout
```
