---
type: llm
criteria: |
  The response says the test cannot be run because device runs (Android or iOS) are not supported yet, or because the
  project has no web platform. It fails if it says the test ran, or if it gives no reason. Judge only these points.
---
The CLI refuses a project without `web` with a plain message. The skill must relay it, and not hunt for another way.
