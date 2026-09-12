---
type: tool_used
tool: Read
input_match: 'residue\.md'
---
The strongest discriminator this case has, and the one it was missing.

The case scored 1.00 in **both** arms on its first run: a capable model refuses
to invent a locator whether or not the plugin is loaded, so every grader here
measured the model rather than the instructions. What the model has no reason to
do unprompted is open `residue.md` — it would look for the element in the page
objects, not in a Migration's own record of what was already declined.

That is the behaviour under test. Residue is a decision someone already made and
wrote down, and re-deriving it means re-doing the work the record exists to save
— or, worse, reaching a different answer from the person who made it. A run that
refuses for the right reason *by coincidence* is not the same as one that
refuses because the Migration says so, and only this grader tells them apart.
