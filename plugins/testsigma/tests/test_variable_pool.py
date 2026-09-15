"""The variable pool, its environments, and the mask a pulled secret comes back as.

The plugin already ran `pull variables --write` and `pull env <name-or-id>
--write` and said where the files land. What it never said is what they *mean*,
and each silence has a failure behind it:

- the pool is the **key registry** — server-side resolution is one
  `coalesce(ev.value, variable.value)` over a LEFT JOIN, so an environment can
  only put a value over a key the pool already holds. A session that helpfully
  completes each env file from the pool spells one server state as N files,
  each stale the moment the pool changes.
- the two commands and the `TSS1431` notice each miss what the other catches:
  the notice never fires for an *empty* pool, and the commands go stale the
  moment an environment is added server-side.
- both kinds are refused by `push` at the kind, before a credential is read.
  Until ADR-0014 the plugin pushed nothing, so "unpushable" needed saying to
  nobody; `delivery.md` now enumerates what a Delivery may do.
- a pulled secret comes back as a run of bullets. The rule must not carry a
  length: a file holding four bullets is the same leak as one holding eight,
  and a guard that matches on eight waves the other through.
"""

from support import (
    REFERENCES_DIR,
    SKILLS_DIR,
    document,
    has_paragraph_with,
)

ADOPTION = document(REFERENCES_DIR / "adoption.md").body
DELIVERY = document(REFERENCES_DIR / "delivery.md").body
FAULTS = document(REFERENCES_DIR / "fault-classes.md").body
SURVEY = document(SKILLS_DIR / "survey" / "SKILL.md").body


# --- the pool is a registry, not a set of defaults ---------------------------

class TestThePoolIsTheKeyRegistry:
    def test_the_pool_holds_every_key_and_an_env_holds_only_overrides(self):
        assert has_paragraph_with(
            ADOPTION, "every key", "overrides")

    def test_an_environment_cannot_introduce_a_key(self):
        # The LEFT JOIN is why, and it is the whole reason the rule holds.
        assert has_paragraph_with(ADOPTION, "cannot add a key the pool")

    def test_completing_an_env_file_from_the_pool_is_named_as_a_second_copy(self):
        assert has_paragraph_with(
            ADOPTION, "never complete an environment file from the pool",
            "second copy")

    def test_the_measurement_argues_for_pulling_them(self):
        # From a Migration, not from a schema: 585 entities, 1550 unresolved
        # environment references, 4 left once the pool and five environments
        # were pulled.
        # Not the bare "4": `has_paragraph_with` matches substrings, so a lone
        # digit is satisfied by any number in the paragraph and asserts nothing.
        assert has_paragraph_with(ADOPTION, "1550", "environments left **4**")


# --- run both, and read the notice -------------------------------------------

class TestSurveyRunsBothAndReadsTheNotice:
    def test_the_two_commands_run_unconditionally(self):
        assert has_paragraph_with(SURVEY, "variables", "unconditionally")

    def test_the_notice_is_surfaced_beside_them(self):
        assert has_paragraph_with(SURVEY, "TSS1431")

    def test_each_is_said_to_catch_what_the_other_misses(self):
        assert has_paragraph_with(ADOPTION, "TSS1431", "empty pool")

    def test_a_present_empty_pool_file_means_looked_and_found_nothing(self):
        assert has_paragraph_with(ADOPTION, "variables { }", "found nothing")


# --- neither kind is ever delivered ------------------------------------------

class TestDeliveryExcludesBothKinds:
    def test_both_kinds_are_excluded_by_kind(self):
        assert has_paragraph_with(DELIVERY, "TSS1301", "variables", "environment")

    def test_the_refusal_lands_before_a_credential_is_read(self):
        assert has_paragraph_with(DELIVERY, "before any credential is read")

    def test_the_reason_is_the_second_encryption_and_not_tidiness(self):
        # A reader told only "pull-only" can still build a sync affordance.
        assert has_paragraph_with(DELIVERY, "a second time", "destroy")

    def test_the_pull_only_set_is_per_kind_and_has_changed(self):
        # Uploads were in it and left, so nothing generalises from these two.
        assert has_paragraph_with(DELIVERY, "per kind", "uploads")


# --- the mask ----------------------------------------------------------------

class TestAMaskedValueIsARunOfBullets:
    def test_the_rule_is_a_run_of_bullets(self):
        assert has_paragraph_with(FAULTS, "run of bullets")

    def test_no_paragraph_about_bullets_carries_a_count(self):
        """The defect this closes is a guard written against the eight the
        product happens to write. Four bullets is the same leak, and a rule
        naming a width is also the pinned magnitude ADR-0003 forbids.

        Every paragraph mentioning bullets is bound, not only the one holding
        the canonical phrase — a count reintroduced in the sentence beside it
        would read as the rule just the same.
        """
        import re
        # "one" is left out deliberately: it is a pronoun far more often than a
        # length here ("the same leak as a longer one"), and a signal that fires
        # on ordinary prose is one a later edit learns to work around.
        counts = re.compile(
            r"\b(two|three|four|five|six|seven|eight|nine|ten|\d+)\b", re.I)
        seen = 0
        for block in FAULTS.split("\n\n"):
            flat = " ".join(block.split())
            if "bullet" not in flat.lower():
                continue
            seen += 1
            assert not counts.search(flat), f"a bullet count is stated: {flat}"
        assert seen, "no paragraph mentions bullets at all"

    def test_a_mask_is_kept_out_of_the_record_like_any_credential(self):
        assert has_paragraph_with(
            FAULTS, "mask", "question", "commit message")

    def test_the_push_refusal_is_the_precedent(self):
        assert has_paragraph_with(FAULTS, "TSS1116")
