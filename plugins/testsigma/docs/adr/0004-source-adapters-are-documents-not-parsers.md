# Source adapters are documents, not parsers

A Source Adapter is prose that tells an agent how to read one source format. It is
not a parser, and adding support for a new source format is writing a document
rather than shipping code. Each adapter declares three properties of its format up
front: whether the real action sequence hides behind a helper layer, whether the
source carries locators, and whether values carry a small language of their own.

## Considered Options

Writing parsers is the obvious path and looks especially obvious for Tosca, whose
`.tsu` subset turns out to be gzipped JSON with a clean entity graph. We are
deliberately not doing that, so this is the decision most likely to be "fixed" by
someone later.

The reason is that the hard part of reading a source is judgement, not parsing. The
most productive fault class in the first conversion was the Composite Step, where a
source line hides a helper that does less or more than the line implies. Recovering
that means opening the helper and deciding what it really does. No schema expresses
it, and a parser that extracted the source line faithfully would reproduce the fault
perfectly.

A schema-shaped view of a format would also have been wrong about Tosca twice. Public
documentation suggested the export was opaque binary, and it is readable JSON. The
same documentation describes locator identification living on module attributes, and
the real export contains no module attributes and no locators of any kind.

## Consequences

The three declared properties are load-bearing rather than descriptive, because they
are independent and every combination we have seen differs. A Java page-object suite
hides sequence and carries locators. A Tosca export shows the full sequence and
carries no locators. A plain Selenium script hides nothing and carries locators
inline. The first property decides whether source comparison is costly or nearly
free; the second decides whether Element Resolution is its own Phase; the third
decides whether a value has to be read as a sequence.

A wildcard or substring comparison in the source is not licence to write a weak
comparison in Testsigma. It is a question about what was being checked.
