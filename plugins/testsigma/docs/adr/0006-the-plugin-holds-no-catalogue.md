# The plugin holds no catalogue, and interrogates the build for one

The plugin never writes down what Testsigma can express. To establish whether a
verb exists, whether it is deprecated, or which kinds of value a slot will hold,
it compiles a throwaway working copy against the installed build and reads a
named diagnostic. ADR-0003 governs the epistemics — probe, never pin, and name
the code a check leans on; this decision governs the object, which is the step
catalogue rather than the build's checks.

## Considered Options

**A reference document listing the catalogue.** An earlier draft proposed one.
It was retired before it was written: the catalogue is generated from the
server's own seed and carries hundreds of verbs, a third of the web ones already
deprecated, so a hand-copied subset is stale from the moment it is committed and
stale in a document nobody re-reads. Faster to consult and always available,
which is exactly what makes a wrong answer from it expensive.

**Scraping the installed bundle.** The catalogue survives minification in the
CLI's shipped `dist` as plain object literals, so a regex over it recovers every
verb and every slot. This is the only way to *enumerate* the catalogue from an
install, and it was rejected anyway: it is unsupported, it breaks on any
bundler change, and it breaks by matching nothing — which is indistinguishable
from a verb that does not exist. A mechanism whose failure reads as a negative
answer is the one thing this plugin's checks are built to refuse.

**Asking the build one question at a time.** Chosen. The compiler names what it
refuses: a value of the wrong kind is refused with the slot's full list of
accepted kinds in the message, and a deprecated verb is reported with its
template id. So a question about a specific row is answerable exactly, offline,
through the CLI's own supported surface.

## Consequences

**The catalogue is interrogated and never enumerated.** No mechanism available
to an installed build can list the verbs, so "which verb expresses this" stays a
judgement made against the format's own documentation and the source, and only
the answer is checked. A stage that wants a list must ask the Operator or read
the format's examples; it must not conclude from silence that nothing exists.

**Every catalogue fact is a Platform Fact with a code beside it.** The
diagnostics this leans on are named where the rule is stated, so an absent code
downgrades its check rather than passing it, exactly as ADR-0003 requires of the
build's other checks.

**One place holds the procedure.** `references/authoring.md` carries it, because
the questions it answers are all about writing the target. `cli-probe.md`
records at survey which of the named codes the installed build produces.
