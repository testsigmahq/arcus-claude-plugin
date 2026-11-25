#!/bin/bash
# A committed Arcus repo with a story test and no arcus-jit.json: the repo has no way to serve its base.
set -euo pipefail
mkdir -p tests/arcus/demo/tests
cat > arcus.json <<'JSON'
{"arcusDir": "tests/arcus", "projects": {"demo": {"projectId": "00000000-0000-4000-8000-000000000001", "region": "us", "folderId": "00000000-0000-4000-8000-000000000002", "platforms": ["web"]}}}
JSON
printf '.arcus/\n' > .gitignore
printf 'test "Search finds a profile" {\n  nav "{env.base_url}/ui/profiles"\n  verify page title == "Profiles"\n}\n' > tests/arcus/demo/tests/search.sigma
git init -q -b feat/search && git add -A && git -c user.email=e@x -c user.name=e commit -qm "search by name"
