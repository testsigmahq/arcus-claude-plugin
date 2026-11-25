#!/bin/bash
# A repo with a base recipe, but a tracked file changed and not committed: serving the base would check out over it.
set -euo pipefail
mkdir -p tests/arcus/demo/tests src
cat > arcus.json <<'JSON'
{"arcusDir": "tests/arcus", "projects": {"demo": {"projectId": "00000000-0000-4000-8000-000000000001", "region": "us", "folderId": "00000000-0000-4000-8000-000000000002", "platforms": ["web"]}}}
JSON
cat > arcus-jit.json <<'JSON'
{"url": "http://localhost:4399", "base": {"serve": "./jit-base.sh base", "restore": "./.arcus/jit/jit-base.sh back", "branch": "main"}, "vars": {}, "budget": "low", "catch": "auto"}
JSON
printf '#!/bin/bash\necho "serving the base" > served.txt\n' > jit-base.sh && chmod +x jit-base.sh
printf '.arcus/\nserved.txt\n' > .gitignore
printf 'export const match = (a, b) => a.toLowerCase().includes(b.toLowerCase());\n' > src/search.ts
git init -q -b feat/search && git add -A && git -c user.email=e@x -c user.name=e commit -qm "search"
printf 'export const match = (a, b) => a.includes(b);\n' > src/search.ts
