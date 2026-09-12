# The build enumerates now, so ask it before interrogating it

ADR-0006 decided that the plugin never writes down what Testsigma can express,
and that it establishes each fact by compiling a throwaway working copy and
reading a named diagnostic. That decision stands. Its stated premise does not.

ADR-0006 records, under Consequences: *"No mechanism available to an installed
build can list the verbs."* The installed build now has two.

    testsigma list verbs                    315 verbs in 27 categories
    testsigma list verbs --category click
    testsigma list blocks                   13 block kinds and what each contains
    testsigma list blocks --kind api        attributes, sub-blocks, calls
    testsigma list blocks --kind api --json the whole subtree, arguments inlined

Both project the compiler's own schema rather than transcribing it, so they go
stale only when the compiler does — which is the property ADR-0006 wanted and
could not get.

## Why this needed a decision rather than an edit

Interrogation and enumeration answer different questions, and ADR-0006 conflated
them because only one was available. Interrogation answers *is this spelling
legal* — one question, one compile. Enumeration answers *what spellings are
there* — and until there was a way to ask it, the honest instruction was to
consult the format's documentation and the source.

An agent with no source and no enumeration does neither. It guesses, and it
guesses against a validator, which is slow and looks like progress. Measured on
a clean-room conversion of an API-heavy scenario: 18 brute-force loops through
`validate`, 274 tool calls, 1275 transcript lines, no test produced. Every one of
those loops was a question `list blocks --kind api` answers in a single call.

The rule "hold no catalogue" only produces good work where a probe exists. Where
none does, the same rule silently becomes "know it already", which nobody can.

## Consequences

**Enumerate first, interrogate second.** Reach for `list verbs` and `list blocks`
before composing anything, and use a compile to confirm a specific spelling
rather than to discover one. A `for` loop over candidate spellings piped into
`validate` is the shape this forbids.

**The plugin still holds no catalogue.** Nothing here licenses copying output
into a reference. The probes are named; their answers are not.

**A named probe is a Platform Fact like any other.** A build without these
commands is a build this plugin still works against — by ADR-0006's original
path — so record which probes the installed build answers, exactly as
`cli-probe.md` records which checks it runs. Absence downgrades the method; it
does not stop the work.

**ADR-0006's Consequences section is superseded in one sentence only** — the
claim that nothing can enumerate. Its decision, its rejection of a transcribed
reference, and its rejection of scraping the bundle are untouched, and the
scraping argument is strengthened: there is now a supported surface that answers
the same question and fails loudly instead of matching nothing.
