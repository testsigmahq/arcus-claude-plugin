# 25 — Name the flag that reads the Unified catalogue

**What to build:** The plugin says a Unified application is writable. `survey/SKILL.md`
says the command-line tool declares a catalogue for web and unified applications only,
and `authoring.md` says to write `applicationType = "unified"`. Both are correct.

What no document says is that reading the Unified catalogue needs `--dialect
unified`. There is no inference: the grammar kinds never open the marker, never
authenticate and never read the workspace, so standing inside an attached Unified
version and running `list verbs` answers with the **Web** catalogue.

**The catalogues are disjoint in practice.** Web has 315 verbs in 27 categories,
Unified has 110 in 20, and only 42 names appear in both. `click(` is web-only. So
an agent that enumerates Web for a Unified application is not working from a
slightly wrong list — roughly seven of eight entries do not exist in the target,
including the first verb anyone reaches for.

**This is wasted work, not a silent fault.** An earlier draft of this issue called
it the worst shape a hole takes, on the grounds that nothing errors. The
enumeration part is right: nothing at that moment says which platform the list is
for. The consequence is not. `attach` writes `applicationType` into the marker and
the workspace compiles against `schemaFor(applicationType)`, so a Unified working
copy meets the Unified catalogue whatever its author read, and a web verb in it is
refused at `validate` with `TSF2001` — offline, no tenant, first run.

So it costs a Conversion's worth of effort and sends the reader hunting for
spellings that were never going to resolve. It cannot reach the tenant and cannot
produce a passing test that tests the wrong thing. It does not belong with the
fault classes the checks exist to catch, which are the ones that survive compile
and round trip. What it defeats is ADR-0009's "enumerate first, then compile to
confirm": the enumeration was honest about its own catalogue and silent about
which one it was.

**The flag.** `--dialect` is consumed by the grammar kinds only — `verbs`,
`generators`, `blocks`, `layout` — which answer from the compiled-in schema. On
tenant reads such as `list applications` it parses and is then silently ignored,
so it must not be documented as accepted there. `layout` takes it and produces
identical output for both dialects today, so naming it there would be noise. Values
are `web` and `unified`, lowercase; `web` is the default. A bad value prints
`--dialect takes one of: web, unified.` and **exits 0**, so nothing may gate on the
exit code.

It is read-side only: no `push`, `pull`, `attach`, `validate` or `run` accepts it,
and the written catalogue is decided solely by the marker.

**Blocked by:** nothing.

**Status:** ready-for-agent

- [ ] `authoring.md` names `--dialect unified` where it tells the reader to enumerate
- [ ] `cli-probe.md` records the flag beside the web/unified platform gate
- [ ] `cli-probe.md` records that the two catalogues are disjoint, with the counts
- [ ] Every place naming the flag says what happens without it, and where that lands
- [ ] The flag is named only for the grammar kinds, never for a tenant read
- [ ] Nothing tells a reader to gate on the exit code of a bad `--dialect` value
- [ ] A document test fails if a document claims Unified support without naming the dialect

**Dropped from this checklist:** *"The `map` skill carries the dialect where it
reaches for the catalogue."* `map` reaches for no catalogue — it holds no
`testsigma` command at all and defers every such question to `authoring.md`
(`skills/map/SKILL.md:117`). A flag put there would be a second copy of a command
with one owner.
