# Source Adapter format

A **Source Adapter** is the document that tells an agent how to read one source
format into Source Steps. One per format, and the only part of a Migration that
knows the format.

An adapter is prose, not a parser (ADR-0004). Adding support for a new source
format means writing a document here, not shipping code. The reason is that the
hard part of reading a source is judgement: the most productive fault class is
the Composite Step, where a source line hides a helper that does less or more
than the line implies, and recovering that means opening the helper and deciding
what it really does. A parser that extracted the source line faithfully would
reproduce the fault perfectly.

## Frontmatter

Every adapter opens with frontmatter declaring its name, a one-line description
of the format, and **all three properties**. An adapter missing any of the three
fails the suite.

```yaml
---
name: cucumber-java
source: Cucumber feature files over a Java page-object layer
hides-sequence: "yes"
carries-locators: "yes"
value-language: "no"
---
```

Each property takes `"yes"`, `"no"`, or `"sometimes"`. Quote the value, because
unquoted `yes` and `no` are booleans in YAML and the point of the field is that
somebody stated it deliberately. Use `"sometimes"` where the answer genuinely
varies within one format, and say in the body how to tell which case you are in.

### The three properties

**`hides-sequence`** — does the real action sequence hide behind a helper layer?
When yes, no source line can be trusted at face value and every one has to be
read through to its implementation. This is what decides whether comparing a
converted step against its source is costly or nearly free.

**`carries-locators`** — does the source carry the information needed to find an
element on screen? When yes, Element Resolution is part of mapping, because the
locators sit in the same files that hold the sequence and both are recovered in
one reading. When no, it is a Phase of its own that has to follow mapping.

**`value-language`** — do values in this source carry a small language of their
own? When yes, a single value can encode a sequence of actions with no helper
anywhere to open, which is the second shape of the Composite Step.

The three are independent. Every combination we have met differs, so none can be
inferred from the others:

| Source | `hides-sequence` | `carries-locators` | `value-language` |
|---|---|---|---|
| Cucumber over Java page objects | yes | yes | no |
| Tosca subset export | no | no | yes |
| Plain script with no helper layer | no | yes | no |

## Required sections

An adapter must carry all six of these headings. The suite checks they are
present; it never checks their wording, so rewording the prose inside them is
free.

- `## Source Step` — what counts as one Source Step in this format
- `## Normalisation` — the rule deciding when two source lines are the same Source Step. It must be precise enough that two people applying it independently get the same count. State it as numbered steps applied in order
- `## Sequence` — where the true action sequence lives, and how to recover it. Where `hides-sequence` is anything but `"no"`, this section must say plainly that the helper is opened for sequence and not only for locators
- `## Locators` — where locators come from, or that the format carries none
- `## Values` — whether values carry their own language, and what it means if so
- `## Enumeration` — how to produce the distinct Source Steps with occurrence counts, ending in a worked example against a fixture

## The worked example

The `## Enumeration` section ends with a table of the distinct Source Steps found
in a fixture suite, with their occurrence counts, one row per step:

```
| `I am signed in` | 2 |
```

This is not decoration. The suite applies the adapter's own normalisation rule to
the fixture and checks the result against this table, so an adapter whose stated
rule and stated counts disagree fails. That is what makes "precise enough that
two people get the same count" a checked property rather than a claim.

## Writing a new one

Do not trust published documentation about a source format. For the Tosca
adapter, the public claims were wrong twice over: the export was described as
opaque binary and is readable gzipped JSON, and identification was described as
living on module attributes which the real export does not contain at all. Open a
real export before writing the document.
