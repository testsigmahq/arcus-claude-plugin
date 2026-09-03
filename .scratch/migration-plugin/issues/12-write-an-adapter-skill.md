# 12 — write-an-adapter skill

**What to build:** A skill that produces a new Source Adapter, so a third source format
does not require us. It walks whoever is writing it through establishing the three
properties for their format, finding where true sequence lives, and stating the
normalisation rule that decides when two source lines are the same Source Step.

The two shipped adapters are the worked examples, and they are useful precisely because
they sit at opposite corners of all three properties. Cucumber hides sequence behind
helpers, carries locators, and has no value language. Tosca is the inverse on all three.
Between them every property is demonstrated in both directions.

**Blocked by:** 02, 11

**Status:** ready-for-agent

- [ ] The skill produces a document that satisfies the adapter contract and passes the adapter tests
- [ ] It requires an explicit value for each of the three properties and does not let one be left unstated
- [ ] It requires a stated normalisation rule for what makes two source lines the same Source Step
- [ ] It requires the author to identify where true sequence lives, and to say so even when the answer is that nothing is hidden
- [ ] Both shipped adapters are referenced as examples, with their opposing property values called out
- [ ] It warns that documentation about a source format may be wrong, since published claims about the Tosca export format were wrong about both its readability and its contents
