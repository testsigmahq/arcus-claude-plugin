# 24 — Retire the Phase framing from the remaining documents

**What to build:** The contract half of the change. With Conversions in place, every
document that still describes mapping or assembly as a Phase of the Migration is
describing something that no longer exists.

The glossary and ADR-0012 are already written and are the authority. This ticket
brings the rest into line: the mapping and assembly skills, the check-order reference,
and anything else that frames its stage as a Phase, opens by telling a reader which
Phase blocks which, or assumes the whole Step Map is reviewed before any test is
assembled.

No behaviour changes here. The old framing simply stops existing, so that a reader
arriving at any one document is not told a model the rest of the plugin has left
behind. It is last because until the loop exists, the old framing is still the
accurate description.

**Blocked by:** 18, 20, 22.

**Status:** ready-for-agent

- [ ] No document describes mapping or assembly as a Phase of the Migration
- [ ] Survey is the only thing described as a Phase
- [ ] No document assumes the whole Step Map is reviewed before assembly begins
- [ ] The mapping skill's rules are otherwise untouched, including the comparison that
      gates a row and the loop-named-helper instruction
- [ ] The assembly skill's rules are otherwise untouched, including document order,
      block nesting, the residue marker and the refusal on an unresolved element
- [ ] The check order and what each check can see are unchanged
- [ ] Document tests assert the absence of the retired framing
- [ ] The full suite and the eval suite run green
