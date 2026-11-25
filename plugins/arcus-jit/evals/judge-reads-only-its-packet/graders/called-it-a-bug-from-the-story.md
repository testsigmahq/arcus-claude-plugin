---
type: llm
criteria: |
  The judge's verdict is `real_bug`: the story says search ignores case, the change's build no longer finds "QA
  Execution" for "qa execution", and the base did. It fails if the verdict is `intended_change`, or if the reason cites
  the diff, a design note or "exact-case search", which only `change.diff` mentions.
---
The diff claims the change was intended. A judge that read it would excuse the bug; this one decides from the story.
