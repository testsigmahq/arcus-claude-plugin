---
type: regex
target: trace
pattern: 'arcus run\b[^\n]*--json'
---
The test was run with `arcus run --json`, so the result is read from the object and not guessed from the exit code.
