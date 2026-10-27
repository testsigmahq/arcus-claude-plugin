#!/bin/bash
# A one-project repo with a local page. The page is opened as a file: address, so no server is needed.
#
# The runner's workspace starts empty and add_dirs only grants read access, so the files are written here.
set -euo pipefail
mkdir -p tests/arcus/demo/tests tests/arcus/demo/elements
cat > arcus.json <<'JSON'
{
  "arcusDir": "tests/arcus",
  "projects": {
    "demo": {
      "projectId": "00000000-0000-4000-8000-000000000001",
      "region": "us",
      "folderId": "00000000-0000-4000-8000-000000000002",
      "platforms": ["web"]
    }
  }
}
JSON
printf '.arcus/\n' > .gitignore
cat > page.html <<'HTML'
<!doctype html>
<html><head><title>Shop</title></head><body><h1>Shop</h1></body></html>
HTML
