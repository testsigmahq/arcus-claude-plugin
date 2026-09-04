---
type: tool_order
before:
  tool: Read
  input_match: 'ReceivingPage\.java'
after:
  tool: Write
  input_match: 'step-map\.md'
---
The page object is opened before the row is written. This is the ordering
assertion that expresses the whole composite-step discipline: a row written
first and justified afterwards cannot be told apart from a correct row by any
check of the row's own content.
