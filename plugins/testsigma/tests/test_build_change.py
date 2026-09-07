"""What a changed CLI build means for work already done.

The plugin probes the build and pins nothing (ADR-0003), holds no catalogue and
asks the build instead (ADR-0006). Both leave one question: what happens to
facts and finished work when the build underneath changes.

Every statement of that rule used to be gain-shaped — "gained a check",
"capability the new build has gained", "it grows". That framing is why diffing
the Catalogues across builds looked necessary: if builds only ever grow, you
need a diff to know what you gained. It is also why nothing could express the
case that actually forces work to be redone, which is a build that stops
accepting something it used to.

ADR-0008 settles it: the plugin detects that the build changed and never
diffs what changed, because the response is the same either way.
"""

import pytest

from support import CONTEXT, REFERENCES_DIR, adr_files, document, has_paragraph_with

CHECKS = document(REFERENCES_DIR / "checks.md")
PROBE = document(REFERENCES_DIR / "cli-probe.md")


def _adr(number):
    matching = [p for p in adr_files() if p.name.startswith(number)]
    assert len(matching) == 1, (
        f"expected one ADR-{number}, found {[p.name for p in adr_files()]}"
    )
    return document(matching[0])


# --- the rule runs in both directions ----------------------------------------


@pytest.mark.parametrize("doc", (CHECKS, PROBE), ids=("checks", "cli-probe"))
def test_a_build_change_can_withdraw_a_capability_not_only_add_one(doc):
    # The asymmetry. A build that removes a verb, narrows a slot's accepted
    # kinds, or renames a value kind turns expressible work into work that
    # cannot be expressed — and that, not a gained check, is what makes the
    # Operator rewrite. A document describing only gains cannot say it
    # happened.
    assert "withdraw" in doc.flat or "stops accepting" in doc.flat, (
        "this document states the build-change rule only as a gain, so a "
        "losing build reads as nothing having happened"
    )


def test_the_glossary_says_a_build_change_moves_in_both_directions():
    flat = " ".join(CONTEXT.read_text(encoding="utf-8").split()).lower()
    # The half that was already true stays verbatim; a skill is forbidden from
    # restating it, so it has to keep its exact words.
    assert "a build change can close a gap and can never close a refusal" in flat
    assert "open" in flat and "withdraw" in flat, (
        "a build change can open a gap or a refusal as well as close one, and "
        "that is the mechanism by which a rewrite reaches a Step Map row"
    )


# --- facts go stale rather than void -----------------------------------------


def test_platform_facts_go_stale_and_are_reprobed_on_use():
    # Voiding every fact on a build change is the obvious alternative and is
    # wrong: ADR-0006 makes probing one question at a time, so there is no
    # bulk re-establish, and wholesale voiding discards facts that are
    # probably still true and cannot be recovered in one pass.
    assert has_paragraph_with(PROBE.body, "stale", "probe"), (
        "cli-probe must say recorded Platform Facts go stale and are "
        "re-established when next used"
    )


# --- the decision not to diff ------------------------------------------------


def test_adr_0008_records_detection_without_diffing():
    body = _adr("0008").flat
    assert "diff" in body, "the ADR must name the thing it declines to do"
    assert "detect" in body or "detection" in body, (
        "and what it does instead"
    )
    assert "same" in body, (
        "the reason: the response to a build change is the same whatever "
        "changed, so knowing what changed buys nothing"
    )


def test_adr_0008_records_the_rejected_route():
    # Enumeration is only possible by regex over the minified dist, which was
    # rejected because it fails by matching nothing — and nothing is
    # indistinguishable from a verb that does not exist. Without this a reader
    # concludes diffing was never considered.
    body = _adr("0008").flat
    assert "minified" in body or "regex" in body, (
        "the alternative that exists must be named, or the decision reads as "
        "an oversight"
    )
    assert "matching nothing" in body or "matches nothing" in body, (
        "and why it was rejected: it fails silently in the safe-looking "
        "direction"
    )


def test_adr_0008_records_the_premise_that_makes_no_fallback_reasonable():
    # Nothing else in the plugin says this is an internal tool, and that
    # premise is what makes refusing backward compatibility a decision rather
    # than negligence.
    body = _adr("0008").flat
    assert "internal" in body, "the internal-tool premise must be stated"
    assert "backward" in body or "fallback" in body, (
        "and the policy it licenses"
    )


def test_adr_0008_says_who_does_the_rewriting():
    body = _adr("0008").flat
    assert "operator" in body, (
        "the cost lands on a person, and the ADR must say which one"
    )


# --- a promise one document makes about another ------------------------------


def test_cli_probe_states_the_limit_that_checks_promises_it_states():
    # checks.md sends the reader to cli-probe.md for "what that comparison can
    # and cannot see". Until ADR-0008 was written, cli-probe stated only what
    # it *can* see, so the cross-reference promised something that was not
    # there — the class of defect a per-commit review cannot catch, because
    # each file is coherent on its own.
    assert "can and cannot see" in CHECKS.flat, (
        "this test exists to hold cli-probe to a promise checks.md makes; if "
        "that promise is gone, so is the reason for the test"
    )
    assert "cannot enumerate" in PROBE.flat or "no command that enumerates" in PROBE.flat, (
        "cli-probe must state the limit of the comparison, not only how to "
        "make it: what it cannot see is that a build declares something "
        "different, only that it differs"
    )
