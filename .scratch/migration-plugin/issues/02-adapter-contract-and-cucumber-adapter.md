# 02 — Source Adapter contract and the Cucumber adapter

**What to build:** The format for a Source Adapter, and the first one. An adapter is a
document that tells an agent how to read one source format into Source Steps, and it must
state three things about its format up front: whether the real action sequence hides
behind a helper layer, whether the source carries locators, and whether values carry a
small language of their own. Then the Cucumber-over-Java-page-objects adapter written
against that format.

When this lands, an agent handed a Cucumber suite can enumerate its distinct Source Steps
with occurrence counts and say which of the three properties apply.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] An adapter document format is defined and documented, including how the three properties are declared
- [ ] The Cucumber adapter declares all three properties with an explicit value for each, and declares that this source hides sequence, carries locators, and has no value language
- [ ] The adapter states the normalisation rule that decides when two source lines are the same Source Step, precisely enough that two people applying it get the same count
- [ ] The adapter says where to find the layer that holds true sequence, and that it must be opened for sequence and not only for locators
- [ ] Tests assert that any adapter document declares all three properties, so an adapter missing one fails
- [ ] Demonstrated against a small fixture suite: distinct Source Steps enumerated with occurrence counts
