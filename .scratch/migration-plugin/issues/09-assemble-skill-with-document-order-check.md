# 09 — Assemble skill with the document-order check

**What to build:** Tests assembled from reviewed Step Map rows, and each finished test
checked for document order and block nesting before it is called done.

The order check is the one fault class a person caught by looking at the application: a
conditional whose body was numbered outside its own block, drawn empty and run late. The
property is arithmetic over the step tree. For every step with a parent, the child's order
lies strictly between its parent's order and the parent's next sibling's order, or beyond
it where there is no next sibling. The plugin computes this itself so it holds regardless
of what the installed CLI checks, which is the concrete case behind the decision to probe
rather than pin.

This check belongs to a whole test rather than a single step, because it describes a fault
that only exists between steps.

**Blocked by:** 07, 08

**Status:** ready-for-agent

- [ ] Only reviewed Step Map rows can reach an assembled test
- [ ] Every assembled test is checked for document order and block nesting before completion
- [ ] The order property is computed by the plugin from the step tree, not delegated to the CLI
- [ ] The check runs at the level of a whole test
- [ ] A test that fails the check is reported with the specific steps that are out of place
- [ ] A test referencing an unresolved element is refused
- [ ] Tests assert the assembly skill requires the order check as its own exit condition
