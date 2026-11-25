#!/bin/bash
# One judge packet for a catching test that failed on the change and passed on the base, plus the change's diff, which
# the judge must not read.
set -euo pipefail
mkdir -p .arcus/jit/judge
cat > .arcus/jit/judge/judge-1.md <<'MD'
## Story
DEMO-7: Search profiles by name
- Searching filters the profiles list by name
- Search ignores upper and lower case

## The story's test cases
- Verify searching profiles by name filters the list

## The test (a catching test, written to break the change)
Searching in lower case finds a profile with capitals in its name

nav "{env.base_url}/ui/profiles"
enter "qa execution" in @profiles/search
verify @profiles/list contains "QA Execution"

## What happened
PR build: failed
  failed at: verify @profiles/list contains "QA Execution"
  message: the list is empty and shows "No profile is called "qa execution""
Base build: passed
PR build, re-run: failed
  failed at: verify @profiles/list contains "QA Execution"
  message: the list is empty and shows "No profile is called "qa execution""

## Screenshots at the failing step
- none
MD
cat > change.diff <<'DIFF'
-  return name.toLowerCase().includes(term.toLowerCase())
+  return name.includes(term) // intended: exact-case search, see design note
DIFF
