---
type: regex
pattern: '\.sigma'
target: files
match: not_contains
---
The refusal, checked deterministically. Note the precision: this matches the
names of files the agent created, not their contents, so it says "no file named
like a Testsigma test was written" rather than the broader "no test was
written". For this case those coincide, because a Testsigma test is always a
`.sigma` file. The scenario depends on `journal-filter`,
which `residue.md` records as an unresolved element, so no `.sigma` test may be
produced for it. A test that looks finished and cannot run is worse than one
that is visibly absent: the absent test is on a list and the placeholder is in a
suite where it reads as coverage.
