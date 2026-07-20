#!/usr/bin/env bash
# Run python.org "Install Certificates.command" once per machine.
# Fixes SSL CERTIFICATE_VERIFY_FAILED for python3 from python.org installer.
# Idempotent: skips if marker present.

set -u
MARKER="${HOME}/.cache/arcus/certs_installed"
mkdir -p "$(dirname "$MARKER")" 2>/dev/null || exit 0
[ -f "$MARKER" ] && exit 0

shopt -s nullglob 2>/dev/null || true
ran=0
for cmd in "/Applications/Python "*"/Install Certificates.command"; do
  [ -x "$cmd" ] || [ -f "$cmd" ] || continue
  bash "$cmd" >/dev/null 2>&1 && ran=1
done

[ "$ran" -eq 1 ] && date -u +"%Y-%m-%dT%H:%M:%SZ" > "$MARKER"
exit 0
