---
type: llm
focus: files
criteria: |
  The Testsigma test written for this scenario carries an empty marker block
  standing where the declined step would have been, and a document under
  `.testsigma/migration/residue/` names that marker and what the test therefore
  does not do. Any label is acceptable as long as the same label appears in both.
  It fails if the declined step is simply absent from the test with nothing
  standing in its place, if it was converted anyway into some approximate step,
  or if the marker exists and no per-test residue document names it. Judge only
  the marker and the document that names it; ignore the rest of the test, the
  other steps, and anything said in the response.
---
A declined step that is silently absent leaves a test that runs green over work
it never did, which is the one outcome worse than a test that is visibly
incomplete: the absent step is on a list, and the silent one is in a suite where
it reads as coverage.

The marker and the per-test document are one mechanism in two places, and
checking only one of them passes a run that produced a marker nobody can look up
or a document describing a marker that is not there.
