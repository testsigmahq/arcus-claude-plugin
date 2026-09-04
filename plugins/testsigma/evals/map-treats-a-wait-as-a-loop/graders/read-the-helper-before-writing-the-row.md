---
type: tool_order
before:
  tool: Read
  input_match: 'JournalPage\.java'
after:
  tool: Write
  input_match: 'step-map\.md'
---
The page object is opened before the row is written. Especially load-bearing
here: the step's own name says wait, so the only way to learn it is a loop is to
read the method, and a row written from the line alone will say wait.
