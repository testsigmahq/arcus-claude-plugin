---
type: regex
target: response
pattern: '"verdict"\s*:\s*"(real_bug|intended_change|test_issue|environment_issue|ambiguous)"'
---
The judge answers with one JSON verdict the report can read.
