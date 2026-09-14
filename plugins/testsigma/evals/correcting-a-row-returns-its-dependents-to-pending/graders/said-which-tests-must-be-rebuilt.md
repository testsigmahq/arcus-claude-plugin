---
type: llm
criteria: |
  The response names the delivered test or scenario that was built on the old
  version of the corrected row — `Archive a record`, or the test assembled from
  it — and says it has to be built again. Saying the scenario has returned to the
  queue counts. It fails if the response reports only that the row was corrected,
  if it claims nothing downstream is affected, or if it names a scenario that was
  never assembled from this row. Judge only whether the affected delivered work
  was identified; ignore wording, formatting, and anything said about the new
  expression itself.
---
Correcting the row is the easy half and a model does it unprompted. What it has
no reason to do is ask what was already built on the old answer, because nothing
in the source records that — it is in the Migration's own files, and only a
document that says to look there gets it opened.

This is the measured defect the versions exist for: one wrong row was used
thirty-five times before anybody noticed, and the cost was not the row.
