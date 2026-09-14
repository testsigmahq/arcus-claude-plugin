---
type: tool_order
before:
  tool: Read
  input_match: 'SearchPage\.java'
after:
  tool: Edit
  input_match: 'step-map\.md'
---
The single most valuable assertion in this suite. The whole composite-step
discipline is one ordering property: the page object is opened before the row is
written. A row written first and justified afterwards is the fault this plugin
exists to prevent, and it is indistinguishable from a correct row by any check
of the row's content alone.

What the no-plugin arm does instead: it reads the feature file, recognises the
phrasing, and writes a plausible row from the step line. Opening the page object
first is not something a capable model does unprompted on a step that reads like
one action — which is exactly why the composite step is the fault worth
measuring.
