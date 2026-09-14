# Screening a suite for what cannot be converted

The second of two triage axes. The platform gate in survey's refusals settles
whether the suite's application can be converted at all; this settles which of its
scenarios can. Survey runs it during enumeration, before it quotes a size, because
a size that counts scenarios nothing could convert is a promise made in error.

A scenario can be pure web and still impossible. In a measured estate, six of seven
web-only scenarios seeded their data by rewriting a spreadsheet and importing it
through the application — which Testsigma cannot do, since it can attach an upload
but not edit a file mid-test. Screening step content is the only thing that finds
those; nothing about the application type gives them away.

## What to screen for

Screen the source for spreadsheet and CSV handling, data-loader or import steps, and
database, shell or version-control steps. Report those scenarios as out of scope
rather than counting them in the total.

## Anchor the classifier to step-definition names, never to the text of a line

A first attempt at this matched a scenario as native because a step read "Navigate
to WM Mobile" and the rule tested for a trailing "Mobile". That scenario was a web
test throughout, and excluding it would have dropped the very case the rest of this
plugin was built from. The text of a line is written by whoever wrote the scenario;
the step-definition name is what the suite actually dispatches to.

## An out-of-scope scenario is seeded, never omitted

Each screened scenario gets a `scenarios.md` row with status `out-of-scope` and the
reason that ruled it out, and is never omitted — see
`${CLAUDE_PLUGIN_ROOT}/references/migration-directory.md`. An absent row reads as
"nobody looked" rather than as somebody having looked and ruled it out, and only the
row can tell those apart. The Operator reports that count to the customer, so it has
to survive the session that produced it.

Being out of scope is a screening judgement about a scenario, not a Residue entry:
Residue is keyed by Source Step and records what the format could not express after
someone tried to express it.
