"""The call-chain check: does a block do everything its source step does.

Both fixtures are the two defects found by hand in real conversions, reduced.
The check earns its place only by separating them from rows that were verified
correct, so the control cases matter as much as the failing ones.
"""
import subprocess
import sys
import pathlib

SCRIPT = pathlib.Path(__file__).resolve().parent.parent / "scripts" / "check_call_chain.py"

SOURCE = '''\
public class MenuPage {
    public static void searchMenu(String strText) {
        SeleniumActions.getElement(bySearchField).clear();
        CommonMethods.waitForPageLoading();
        SeleniumActions.sendTextToElement(bySearchField, strText, "search");
        KeyboardActions.pressEnterKey(bySearchField);
        SeleniumActions.click(By.xpath(menuLabel), strText);
    }
    public static void tidySearch(String strText) {
        SeleniumActions.getElement(bySearchField).clear();
        SeleniumActions.sendTextToElement(bySearchField, strText, "search");
    }
    public static void padded(String s) {
        GeneralUtils.checkKey(s);
        SeleniumActions.click(byThing, "thing");
    }
    public static void viaHelper(String s) {
        MenuPage.tidySearch(s);
    }
}
'''

DROPPED = '''test "x" {
  block "Search menu 'Create Order' at WM Mobile" {
    click(element.menuIcon)
    clearElementValue(element.menuSearchField)
    enterText("Create Order", element.menuSearchField)
  }
}
'''

COMPLETE = '''test "x" {
  block "Search menu 'Create Order' at WM Mobile" {
    clearElementValue(element.searchField)
    enterText("Create Order", element.searchField)
    pressEnter()
    clickWithText(element.menuLabel, "Create Order")
  }
}
'''


def run(tmp_path, sigma, symbol, block="Search menu", depth=2):
    src = tmp_path / "src"
    src.mkdir(exist_ok=True)
    (src / "MenuPage.java").write_text(SOURCE, encoding="utf-8")
    test = tmp_path / "t.sigma"
    test.write_text(sigma, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--source-root", str(src),
         "--symbol", symbol, "--block", block, "--depth", str(depth), str(test)],
        capture_output=True, text=True)


def test_a_dropped_submit_is_reported(tmp_path):
    r = run(tmp_path, DROPPED, "MenuPage.searchMenu")
    assert r.returncode == 1, r.stdout
    assert "more actions than the block" in r.stdout


def test_it_names_the_actions_on_both_sides(tmp_path):
    """A bare count tells a reader nothing about which action went missing."""
    r = run(tmp_path, DROPPED, "MenuPage.searchMenu")
    assert "pressEnterKey" in r.stdout and "clearElementValue" in r.stdout


def test_a_complete_block_passes(tmp_path):
    r = run(tmp_path, COMPLETE, "MenuPage.searchMenu")
    assert r.returncode == 0, r.stdout


def test_waits_are_excluded_from_both_sides(tmp_path):
    """A conversion reshapes waiting, so counting waits makes the check noise.

    `searchMenu` calls `waitForPageLoading`; if that counted, a faithful block
    that expresses waiting differently would be reported as incomplete.
    """
    r = run(tmp_path, COMPLETE, "MenuPage.searchMenu")
    assert "waitForPageLoading" not in r.stdout


def test_a_name_that_merely_contains_a_verb_is_not_an_action(tmp_path):
    """`checkKey` performs nothing, and padded a real drop to an equal count.

    This is the check's own fault class: a phantom action hides a missing one.
    """
    r = run(tmp_path, 'test "x" {\n  block "padded" {\n    click(element.a)\n  }\n}\n',
            "MenuPage.padded", block="padded")
    assert r.returncode == 0, r.stdout
    assert "checkKey" not in r.stdout


def test_it_follows_a_call_one_level_down(tmp_path):
    """A step definition rarely acts; it calls a page object that does.

    At depth 0 this finds nothing and would pass everything.
    """
    r = run(tmp_path, 'test "x" {\n  block "via" {\n    click(element.a)\n  }\n}\n',
            "MenuPage.viaHelper", block="via", depth=2)
    assert r.returncode == 1, r.stdout
    assert "sendTextToElement" in r.stdout


def test_a_symbol_that_is_not_found_is_not_a_pass(tmp_path):
    """Silence from a check that compared nothing is the fault it exists for."""
    r = run(tmp_path, COMPLETE, "MenuPage.noSuchMethod")
    assert r.returncode == 1
    assert "not a pass" in r.stdout


def test_a_missing_block_is_reported(tmp_path):
    r = run(tmp_path, COMPLETE, "MenuPage.searchMenu", block="nothing like this")
    assert r.returncode == 1
    assert "no block" in r.stdout


def test_an_owner_no_file_declares_is_reported(tmp_path):
    """A typo'd class must not resolve silently to a same-named method.

    The fallback is deliberate — a file name is not a class name in Python or
    JavaScript — but a confident answer to a question nobody asked is the
    failure this whole check exists to refuse.
    """
    r = run(tmp_path, DROPPED, "NoSuchClass.searchMenu")
    assert "no file under the source root is named" in r.stdout
