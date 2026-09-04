---
type: regex
pattern: '\|[^|\n]*\?[^|\n]*\|'
target:
  source: file
  path: .testsigma/migration/open-questions.md
match: contains
---
A question reached `open-questions.md` as a table row rather than living only in
the transcript. Deterministic, and the whole reason that file exists: a question
asked once and recorded nowhere is the failure this plugin was designed against.
