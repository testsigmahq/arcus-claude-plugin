# 11 — Tosca adapter, and Element Resolution as its own Phase

**What to build:** The second Source Adapter, and the Phase that only a source like this
one needs.

A Tosca subset export is gzipped JSON: one flat list of entities, each with a class, a
unique surrogate, string attributes, and associations to other entities by surrogate. Two
properties of it drive the adapter. First, order exists nowhere as a value. No entity
carries an order, index or sequence attribute, and the only ordering signal is the position
of a surrogate inside an association list, so a reader that walks the entity list in file
order produces a scrambled sequence that looks complete. Second, the export is
transitively closed, so the reusable blocks a test references travel with it and true
sequence is recoverable from the file alone.

It carries no locators of any kind. Not one. That is what forces Element Resolution into a
separate Phase here, where for a page-object source it is part of mapping. This adapter is
therefore also the ticket that proves the Phase structure follows the source rather than
being fixed.

Values in this source carry their own small language, so a single value can encode a
sequence of several actions with no helper anywhere to open. That is the second shape of the
composite-step problem and the mapping skill has to read it as a sequence.

**Blocked by:** 02, 08

**Status:** ready-for-agent

- [ ] The adapter declares all three properties: sequence not hidden behind a helper, no locators carried, values do carry their own language
- [ ] The adapter states that order comes from association list position, and that walking the entity list instead is wrong
- [ ] Reusable block references are resolved so true sequence is recovered from the export alone
- [ ] A value written in the source's own language is read as a sequence of actions
- [ ] A wildcard comparison in the source raises a question rather than becoming a weak comparison
- [ ] Element Resolution runs as its own Phase for this source, and the element names the Step Map references are carried forward for it to satisfy
- [ ] A data-driven test is recognised as a template plus instances, so the template is migrated rather than producing one duplicated test per instance
- [ ] Demonstrated against a real export: correct step order recovered, and the absence of locators reported rather than silently producing none
