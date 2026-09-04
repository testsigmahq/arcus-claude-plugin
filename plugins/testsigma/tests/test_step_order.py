"""The document-order and block-nesting arithmetic.

The only executable code in this plugin, and it exists because the property is
exact by construction. Everything else a Migration does is judgement.

The fault: a conditional whose body is numbered outside its own block, so the
block draws empty and its steps run after everything else. It compiles, the
tenant accepts it, and a round trip cannot see it, because the round trip
rebuilds the tree from parentage and order is not parentage.
"""

import importlib.util
import json
import sys

import pytest

from support import PLUGIN_ROOT

_spec = importlib.util.spec_from_file_location(
    "check_step_order", PLUGIN_ROOT / "scripts" / "check_step_order.py"
)
order = importlib.util.module_from_spec(_spec)
sys.modules["check_step_order"] = order
_spec.loader.exec_module(order)


#: A test with one conditional. Ids are deliberately NOT in document order:
#: the body's id is the highest because it was authored last, which is the real
#: shape measured on a converted suite and the trap the parser must not fall in.
ONE_CONDITIONAL = '''test "probe" [id = 10] {
  storeValue("unset", "marker") [id = 20]

  if compare("1", "==", "1") [id = 21] {
    storeValue("first", "marker") [id = 99]
  }

  verifyComparison(runtime.marker, "==", "first") [id = 22]
}
'''

NESTED = '''test "nested" [id = 1] {
  for row in tdp["d"].rows() [id = 2] {
    enterText(row.a, element.b) [id = 3]

    for row in tdp["d"].rows("1") [id = 4] {
      pressEnter() [id = 5]
    }

    click(element.after) [id = 7]
  }

  click(element.done) [id = 6]
}
'''


class TestParsingTheTree:
    def test_it_finds_the_root_and_its_children(self):
        root = order.parse(ONE_CONDITIONAL)
        assert root.identity == 10
        assert [child.identity for child in root.children] == [20, 21, 22]

    def test_a_block_body_is_a_child_of_the_block(self):
        root = order.parse(ONE_CONDITIONAL)
        conditional = root.children[1]
        assert [child.identity for child in conditional.children] == [99]

    def test_nesting_goes_as_deep_as_the_document(self):
        root = order.parse(NESTED)
        outer = root.children[0]
        inner = outer.children[1]
        assert outer.identity == 2
        assert inner.identity == 4
        assert [child.identity for child in inner.children] == [5]

    def test_an_id_is_never_read_as_an_order(self):
        # The correction this whole module turns on. A step authored last
        # carries the highest id and may sit anywhere in the document.
        root = order.parse(ONE_CONDITIONAL)
        assert all(step.order is None for step in order.walk(root))

    def test_a_file_with_no_steps_yields_no_tree(self):
        assert order.parse('folder "Key Extensions" [id = 140] {\n}\n').children == []
        assert order.parse("\n\n") is None

    def test_a_step_whose_annotation_is_not_last_on_the_line_is_still_found(self):
        # `as <alias>` names a step's result and is a normal shape — the real
        # sign-in step group uses it. Anchoring the pattern to end-of-line
        # dropped these steps from the tree entirely: not reported as faults
        # and not reported as unchecked, so the check went silently blind.
        text = (
            'test "t" [id = 1] {\n'
            "  enterText(env.appUsername, element.usernameField) [id = 1584] as username\n"
            "  enterText(env.appPassword, element.passwordField) [id = 1585] as password\n"
            "  click(element.signIn) [id = 1586]\n"
            "}\n"
        )
        root = order.parse(text)
        assert [child.identity for child in root.children] == [1584, 1585, 1586]

    def test_a_step_is_not_invented_from_an_argument(self):
        text = 'test "t" [id = 1] {\n  enterText("[id = 7]", element.a) [id = 2]\n}\n'
        root = order.parse(text)
        assert [child.identity for child in root.children] == [2]


class TestARefusalBeatsALostStep:
    """A step missing from the tree is checked by nothing and reported by
    nothing, so the parser refuses rather than returning a tree it has lost
    part of."""

    def test_a_duplicate_id_is_refused(self):
        text = 'test "t" [id = 1] {\n  click(element.a) [id = 2]\n  click(element.b) [id = 2]\n}\n'
        with pytest.raises(ValueError, match="duplicate step id"):
            order.parse(text)

    def test_a_second_top_level_step_is_refused(self):
        text = 'test "t" [id = 1] {\n}\ntest "u" [id = 2] {\n}\n'
        with pytest.raises(ValueError, match="top level"):
            order.parse(text)

    def test_an_unclosed_block_is_refused(self):
        text = 'test "t" [id = 1] {\n  if compare("1","==","1") [id = 2] {\n    click(element.a) [id = 3]\n}\n'
        with pytest.raises(ValueError, match="left open"):
            order.parse(text)


class TestDerivingTheCorrectOrder:
    def test_it_is_the_pre_order_walk_of_the_lexical_tree(self):
        # The working copy is the authority: its document order is correct by
        # construction, which is why the plugin computes this rather than
        # asking the platform.
        assert order.derive_order(order.parse(ONE_CONDITIONAL)) == {
            10: 0,
            20: 1,
            21: 2,
            99: 3,
            22: 4,
        }

    def test_a_body_sorts_between_its_block_and_the_next_step(self):
        derived = order.derive_order(order.parse(ONE_CONDITIONAL))
        assert derived[21] < derived[99] < derived[22]

    def test_the_derived_order_satisfies_the_property_by_construction(self):
        for text in (ONE_CONDITIONAL, NESTED):
            root = order.parse(text)
            order.apply_orders(root, order.derive_order(root))
            assert order.violations(root) == []


class TestTheProperty:
    def _check(self, text, orders):
        root = order.parse(text)
        missing = order.apply_orders(root, orders)
        assert not missing, f"fixture does not cover {missing}"
        return order.violations(root)

    def test_a_body_numbered_after_the_next_step_is_a_fault(self):
        # The measured fault: push numbered conditional bodies after every
        # top-level step, so each assertion read the value the body had not set.
        found = self._check(ONE_CONDITIONAL, {10: 0, 20: 1, 21: 2, 22: 3, 99: 4})
        assert len(found) == 1
        assert found[0]["id"] == 99
        assert found[0]["order"] == 4
        assert found[0]["parent_order"] == 2
        assert found[0]["limit"] == 3
        assert "draws empty" in found[0]["reason"]

    def test_a_body_numbered_before_its_own_block_is_a_fault(self):
        found = self._check(ONE_CONDITIONAL, {10: 0, 20: 1, 21: 3, 99: 2, 22: 4})
        assert [entry["id"] for entry in found] == [99]
        assert "before its own block" in found[0]["reason"]

    def test_a_body_sharing_its_parents_order_is_a_fault(self):
        # "Strictly between" is the specification word. Both bounds are
        # exclusive, and an off-by-one at either survived every other test here.
        found = self._check(ONE_CONDITIONAL, {10: 0, 20: 1, 21: 2, 99: 2, 22: 3})
        assert [entry["id"] for entry in found] == [99]
        assert "before its own block" in found[0]["reason"]

    def test_a_body_sharing_the_next_siblings_order_is_a_fault(self):
        found = self._check(ONE_CONDITIONAL, {10: 0, 20: 1, 21: 2, 99: 3, 22: 3})
        assert 99 in [entry["id"] for entry in found]

    def test_a_body_with_no_next_sibling_has_no_upper_bound(self):
        text = 'test "t" [id = 1] {\n  if compare("1","==","1") [id = 2] {\n    click(element.a) [id = 3]\n  }\n}\n'
        assert self._check(text, {1: 0, 2: 1, 3: 900}) == []

    def test_that_body_must_still_come_after_its_block(self):
        text = 'test "t" [id = 1] {\n  if compare("1","==","1") [id = 2] {\n    click(element.a) [id = 3]\n  }\n}\n'
        found = self._check(text, {1: 0, 2: 5, 3: 1})
        assert [entry["id"] for entry in found] == [3]

    def test_the_first_two_siblings_transposed_is_a_fault(self):
        # Review found a mutation that skipped the sibling comparison for the
        # first pair under any parent and stayed green: every existing fixture
        # put its swap somewhere that also tripped a later pair or a
        # parent/child bound. This confines the fault to the 0-1 pair.
        found = self._check(ONE_CONDITIONAL, {10: 0, 20: 20, 21: 10, 99: 15, 22: 30})
        assert [entry["id"] for entry in found] == [21]
        assert "document order" in found[0]["reason"]

    def test_siblings_out_of_document_order_are_a_fault(self):
        found = self._check(ONE_CONDITIONAL, {10: 0, 20: 3, 21: 2, 99: 4, 22: 1})
        ids = [entry["id"] for entry in found]
        assert 21 in ids or 22 in ids, f"nothing reported for shuffled siblings: {found}"

    def test_a_deeply_nested_body_is_checked_against_its_own_parent(self):
        # The inner loop's body must sit inside the inner loop, not merely
        # inside the outer one.
        # The inner loop now has a next sibling, so its body has an upper
        # bound. Without one the property gives it none, which is correct and
        # was my fixture's mistake rather than the code's.
        found = self._check(NESTED, {1: 0, 2: 1, 3: 2, 4: 3, 5: 6, 7: 5, 6: 7})
        assert [entry["id"] for entry in found] == [5]
        assert found[0]["parent_order"] == 3
        assert found[0]["limit"] == 5

    def test_a_clean_test_reports_nothing(self):
        assert self._check(NESTED, {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 7: 5, 6: 6}) == []

    def test_every_fault_names_the_step_and_its_window(self):
        # A report that says only "this test is wrong" cannot be acted on.
        found = self._check(ONE_CONDITIONAL, {10: 0, 20: 1, 21: 2, 22: 3, 99: 4})
        for key in ("line", "id", "order", "parent_order", "text", "reason"):
            assert key in found[0]


class TestAnUnreportedStepIsNotAPass:
    def test_a_step_with_no_reported_order_is_named(self):
        root = order.parse(ONE_CONDITIONAL)
        missing = order.apply_orders(root, {10: 0, 20: 1, 21: 2, 22: 3})
        assert missing == [99], "a step with no reported order must not read as clean"

    def test_it_is_not_silently_treated_as_in_place(self):
        root = order.parse(ONE_CONDITIONAL)
        order.apply_orders(root, {10: 0, 20: 1, 21: 2, 22: 3})
        # No fault is invented for it either; the caller is told it is missing.
        assert order.violations(root) == []


class TestTheCommandLine:
    def test_it_exits_non_zero_when_a_step_is_out_of_place(self, tmp_path, capsys):
        sigma = tmp_path / "t.sigma"
        sigma.write_text(ONE_CONDITIONAL, encoding="utf-8")
        orders = tmp_path / "o.json"
        orders.write_text(json.dumps({"10": 0, "20": 1, "21": 2, "22": 3, "99": 4}))
        code = order.main(["prog", str(sigma), "--orders", str(orders)])
        assert code == 1
        assert "out of place" in capsys.readouterr().out

    def test_it_exits_zero_on_a_clean_test(self, tmp_path, capsys):
        sigma = tmp_path / "t.sigma"
        sigma.write_text(ONE_CONDITIONAL, encoding="utf-8")
        orders = tmp_path / "o.json"
        orders.write_text(json.dumps({"10": 0, "20": 1, "21": 2, "99": 3, "22": 4}))
        assert order.main(["prog", str(sigma), "--orders", str(orders)]) == 0
        assert "clean" in capsys.readouterr().out

    def test_it_exits_non_zero_when_a_step_has_no_reported_order(self, tmp_path, capsys):
        sigma = tmp_path / "t.sigma"
        sigma.write_text(ONE_CONDITIONAL, encoding="utf-8")
        orders = tmp_path / "o.json"
        orders.write_text(json.dumps({"10": 0, "20": 1, "21": 2, "22": 3}))
        assert order.main(["prog", str(sigma), "--orders", str(orders)]) == 1
        assert "not checked" in capsys.readouterr().out

    def test_without_orders_it_prints_the_order_it_derived(self, tmp_path, capsys):
        sigma = tmp_path / "t.sigma"
        sigma.write_text(ONE_CONDITIONAL, encoding="utf-8")
        assert order.main(["prog", str(sigma)]) == 0
        assert "correct order" in capsys.readouterr().out
