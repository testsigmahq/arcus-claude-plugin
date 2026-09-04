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

- [x] The skill produces a document that satisfies the adapter contract and passes the adapter tests
- [x] It requires an explicit value for each of the three properties and does not let one be left unstated
- [x] It requires a stated normalisation rule for what makes two source lines the same Source Step
- [x] It requires the author to identify where true sequence lives, and to say so even when the answer is that nothing is hidden
- [x] Both shipped adapters are referenced as examples, with their opposing property values called out
- [x] It warns that documentation about a source format may be wrong, since published claims about the Tosca export format were wrong about both its readability and its contents

**Done, 2026-09-04.** 508 tests pass, arcus untouched at 92. The skill is 1,389 words
and points at `adapters/README.md` for the contract rather than restating it, so there
is one definition of what an adapter must satisfy.

**Review walked the skill rather than only reading it**, which is the check the
document tests cannot perform. It followed the steps to draft a Robot Framework
adapter and confirmed the result satisfies the contract structurally: frontmatter,
all three properties with values in the fixed set, all six required sections, the
`hides-sequence != "no"` rule that the Sequence section must mention locators, and a
parseable worked example. Criterion 1 is a claim about what an agent following the
skill produces, and that is now evidence rather than assertion.

It also noted that a literal walkthrough is correctly *blocked* at Step 0 with no real
export in hand — the skill would rather stop than guess, which is the intended
behaviour.

**Writing this skill forced a fix to the adapter committed an hour earlier.** The
contract says the worked-example table lists the distinct Source Steps one row per
step, and that the suite checks the table against the adapter's own normalisation
rule. The Tosca table listed the top 8 of 19 with the rest summarised in prose —
flagged at low confidence by the previous review and left standing. That stopped
being defensible the moment a skill existed telling a stranger to satisfy that
contract, because the nearest worked example would be teaching them to violate it. A
partial table also cannot do the job the contract gives it: a rule cannot be checked
against a sample of its own output. All 19 rows are now listed and the test compares
for full equality, so a row added, dropped or renamed fails. Review re-derived every
row independently against the real export and they match.

A document that teaches a rule has to obey it, or the example quietly becomes the
rule.

**Five of fourteen mutations survived the first pass, and one had no test at all** —
the "list every row" instruction I had just written was unasserted. Two survived on a
single word appearing elsewhere in the same paragraph: "Reordering two steps fixed
it" kept "order" alive after the rule about step order was deleted, and
"documentation" is the section's own subject so requiring it proved nothing.

The most interesting was the refusal to write from a specification. Deleting it left
the section stating both "open a real export before writing a word" and "where you
cannot get one, write from the specification" — the document contradicting itself in
neutral language, with the primary rule intact to satisfy the assertion. That is the
class documented as open in `hedges_in`, but this instance had a positive handle and
is closed.
