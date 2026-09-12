---
type: tool_order
before:
  tool: Read
  input_match: 'JournalPage\.java'
after:
  tool: Edit
  input_match: 'step-map\.md'
---
The page object is opened before the row is written.

**Edit, not Write, and that is the assertion doing the work.** Survey seeds
`step-map.md` with a row per Source Step, so the file exists before mapping
starts and filling a row is an edit. The map skill says so directly, and says
not to do it "via a generated script that rewrites the whole table" — a run that
did exactly that lost every row to one syntax error. So `Write` to `step-map.md`
is the forbidden spelling, and a grader demanding it penalised the plugin for
obeying its own instruction.

That was measured, not reasoned: this grader passed once and failed the next
time on the same commit, depending on which verb the agent happened to reach
for, and it is why this case read as unstable rather than as miscalibrated. Especially load-bearing
here: the step's own name says wait, so the only way to learn it is a loop is to
read the method, and a row written from the line alone will say wait.
