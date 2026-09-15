# An empty block means Residue, and nothing else

A block with an empty body says **nobody could express this step**. It is the
marker that keeps a declined step present in the test rather than absent from it,
so a reviewer sweeping a converted suite for what a Migration did not do can find
every one of them by shape.

Where a construct absorbs several source steps, the absorbed steps are **claimed
by the block that performs them** — named in its label, separated by ` | ` — and
no empty block stands for them. They were converted. Nothing declined them.

## Considered Options

The rule until now was one block per source step, labelled with that step's text,
which the coverage check reads to prove nothing was silently dropped. It met a
construct that is genuinely several steps at once — `api` is the request, its
send and its assertions — and the only way to keep the count was to emit an empty
block for each step with no statement of its own, with a parenthetical in the
label saying it was handled next door.

That was measured before it was decided. Across four converted tests and 648
blocks: 85 empty, of which **79 were absorbed and 6 were genuinely declined**.
The signal that means *look here, this is what was not done* carried thirteen
impostors for every real instance, which is worse than having no signal, because
a reviewer learns to skip it. A reader going top to bottom met a fifth of one
test as empty blocks and would reasonably conclude the conversion was threadbare.

**Marking the real ones with a fixed prefix** was rejected *as the fix*. It would
have made the six findable again — cheap, and needing no change to the check. But
it fixes the sweep and not the shape: 79 blocks would still *be* empty, still say
structurally that nothing was written there, in a file a person reads. The prefix
makes the markers greppable; it does not stop the file lying to whoever reads it.

That reasoning stands, and the prefix came back anyway, for a job this ADR did
not consider. Once claims exist, coverage reads labels and never bodies, so an
*empty* block claiming five steps accounts for all five — the shape restored here
can be written directly as a fake. The Cause a marker names is what separates the
two, and it has to be findable mechanically, so it takes a fixed prefix. That is
a discriminator on top of claims rather than a substitute for them, and with six
markers left rather than eighty-five the readability objection above no longer
applies.

**Recording the absorption in the Migration Directory** and dropping the blocks
was rejected for a stronger reason than the coverage count. A record the same run
writes about its own completeness is not evidence. This check's whole value is
that it compares the test artifact against the source, so a claim living anywhere
but the artifact lets an assembler assert the thing the check exists to doubt.

**A positional claim** — this block covers the next N source lines — was rejected
on the same measurement. Twelve of the absorbed steps sat a line or two after
their absorber because the source interleaves a wait, so a positional form is
wrong for a fifth of the worst case and wrong invisibly.

## Consequences

**The check widens in one dimension only.** One label may account for more than
one step. A segment still matches a step whole, or whole with a bracketed
qualifier, and a segment matching nothing is reported as an extra exactly as an
unmatched label always was. Coverage remains a multiset, so a step written twice
needs two claims, and a label naming one step twice is refused rather than
absorbed — that is a claim to coverage the block does not have.

**The label is load-bearing twice over.** It is what the coverage check reads and
what the application shows as the step's name, so the absorber's own step comes
first and every segment is the source's own spelling. A synthesised summary would
read better and account for nothing.

**An empty block regains its meaning, and then declares it.** Once absorbed steps
are claimed, the only empty blocks left are Residue — but a shape nothing checks
can still be written by hand, so an empty block names its Cause and the check
refuses one that does not. The rule is one-way: a block naming a Cause *and*
carrying a body is a partly converted step, which is how the format refuses a
Divergence, so only the empty one has to declare itself.

**A claim is generated text.** It is assembled by a program from several source
lines, which is precisely where the format's escape set bites (`authoring.md`):
a serialiser's `\uXXXX` arrives with the backslash dropped and nothing raised.

ADR-0010 keeps its place in the check order — coverage is still a check and
still runs first — but not one of its sentences: it said a scenario is assembled
one block per source step, and that line is amended there rather than left to be
contradicted from here. What changes is what one block may account for, not when
the arithmetic happens.
