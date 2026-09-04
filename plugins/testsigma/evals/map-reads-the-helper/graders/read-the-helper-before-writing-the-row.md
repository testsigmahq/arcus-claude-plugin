---
type: tool_order
before:
  tool: Read
  input_match: 'SearchPage\.java'
after:
  tool: Write
  input_match: 'step-map\.md'
---
The single most valuable assertion in this suite. The whole composite-step
discipline is one ordering property: the page object is opened before the row is
written. A row written first and justified afterwards is the fault this plugin
exists to prevent, and it is indistinguishable from a correct row by any check
of the row's content alone.
