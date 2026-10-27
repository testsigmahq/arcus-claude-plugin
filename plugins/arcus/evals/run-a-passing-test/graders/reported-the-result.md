---
type: llm
criteria: |
  The response says the test passed, and names the browser (for example Chrome for Testing) or the time it took.
  It does not say the test was pushed or sent to Arcus, and it may say a local run sends nothing to Arcus. Offering
  to push is fine. It fails if it reports a failure, if it claims the test passed in Arcus, or if it gives no result.
  Judge only these points.
---
A model answering freehand may run the test and print the raw JSON. The point is a result a person can read, with the browser named and no claim beyond a local run.
