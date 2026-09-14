# 20 — Element resolution inside a Conversion

**What to build:** Element resolution stops being a stage of its own and becomes
something that happens inside a Conversion, in three places in a fixed order: the
source, then the target project, then the Operator.

Where the adapter declares that the source carries locators, the first place answers,
in the same reading that recovers the helper's sequence. That is unchanged and must
stay unchanged — separating the two readings was four of the six measured faults in
the conversion that produced this plugin, and the file is already open.

Where the source carries none, the first place is empty and the target project
answers most of what is left. Only when all three are exhausted does the Conversion
park on the Operator. For a page-object source that should essentially never happen,
and the documents should read that way rather than presenting Operator capture as the
normal path.

When it does park, the whole screen goes to the Operator, not the one element that
blocked it. Capture is cheap per screen and expensive per visit: someone already
looking at a screen can capture eight controls nearly as fast as one.

`resolve-elements` keeps its procedure and loses its framing. Its description
currently declares it the way into a Migration Phase; it becomes something `convert`
calls, scoped to one screen.

**Blocked by:** 18, 19.

**Status:** ready-for-agent

- [ ] The three places are documented in order, with the Operator last
- [ ] Resolution from the source happens in the same reading that recovers sequence,
      unchanged
- [ ] The target project is consulted before the Operator is asked for anything
- [ ] A Conversion parks on elements only when all three places are exhausted
- [ ] When it parks, the whole screen is put to the Operator, not the single element
- [ ] `resolve-elements`' description no longer presents it as the way into a Phase
- [ ] Nothing in the plugin still calls element resolution a Phase of the Migration
- [ ] The shared element-resolution reference remains the single definition of the
      procedure, read by both skills
- [ ] Document tests cover the ordering, the whole-screen rule and the changed framing
