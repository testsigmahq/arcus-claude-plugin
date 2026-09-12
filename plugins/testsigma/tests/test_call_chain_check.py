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
    # Either phrasing is a report: the families name what is missing when they
    # can, and the count speaks when every family is accounted for.
    assert ("actions the block does not" in r.stdout
            or "more actions than the block" in r.stdout)


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
    """Silence from a check that compared nothing is the fault it exists for.

    Exit 2, not 1: "could not compare" and "the block is short" are different
    answers. A caller that merges them reports most of a test as failing, which
    is how a check earns being ignored.
    """
    r = run(tmp_path, COMPLETE, "MenuPage.noSuchMethod")
    assert r.returncode == 2
    assert "not a pass" in r.stdout


def test_a_missing_block_is_reported(tmp_path):
    r = run(tmp_path, COMPLETE, "MenuPage.searchMenu", block="nothing like this")
    assert r.returncode == 2
    assert "no block" in r.stdout


def test_an_owner_no_file_declares_is_reported(tmp_path):
    """A typo'd class must not resolve silently to a same-named method.

    The fallback is deliberate — a file name is not a class name in Python or
    JavaScript — but a confident answer to a question nobody asked is the
    failure this whole check exists to refuse.
    """
    r = run(tmp_path, DROPPED, "NoSuchClass.searchMenu")
    assert "no file under the source root is named" in r.stdout


def test_a_callee_is_resolved_beside_its_caller_first(tmp_path):
    """The same method name in two page objects with different bodies.

    Resolving a bare callee globally picked the namesake carrying an extra
    keypress and reported a correct block as short — the inverse fault, from
    ambiguity rather than from comments.
    """
    src = tmp_path / "src"
    src.mkdir(exist_ok=True)
    (src / "HomePage.java").write_text('''\
public class HomePage {
    public static void navigate() { HomePage.searchMenu("x"); SeleniumActions.click(byMenu, "m"); }
    public static void searchMenu(String s) {
        SeleniumActions.clear(bySearch, "s");
        SeleniumActions.sendTextToElement(bySearch, s, "s");
    }
}
''', encoding="utf-8")
    (src / "OtherPage.java").write_text('''\
public class OtherPage {
    public static void searchMenu(String s) {
        SeleniumActions.clear(bySearch, "s");
        SeleniumActions.sendTextToElement(bySearch, s, "s");
        KeyboardActions.pressEnterKey(bySearch);
        SeleniumActions.click(byLabel, s);
    }
}
''', encoding="utf-8")
    test = tmp_path / "t.sigma"
    test.write_text('''test "x" {
  block "Navigate" {
    clearElementValue(element.s)
    enterText("x", element.s)
    click(element.menu)
  }
}
''', encoding="utf-8")
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--source-root", str(src),
         "--symbol", "HomePage.navigate", "--block", "Navigate", str(test)],
        capture_output=True, text=True)
    assert r.returncode == 0, r.stdout
    assert "pressEnterKey" not in r.stdout, "resolved the namesake in OtherPage"


TAIL_SOURCE = '''\
public class Form {
    public static void save(String s) {
        SeleniumActions.clear(byField, "f");
        SeleniumActions.sendTextToElement(byField, s, "f");
        KeyboardActions.pressEnterKey(byField);
        SeleniumActions.click(bySubmit, "submit");
    }
}
'''

TAIL_DROPPED = '''test "x" {
  block "Save it" {
    click(element.openPanel)
    clearElementValue(element.field)
    enterText("v", element.field)
    click(element.someIcon)
  }
}
'''


def test_a_dropped_tail_is_caught_even_when_the_counts_match(tmp_path):
    """Four actions against four, and the whole tail is gone.

    Every measured defect was the tail of a sequence — a helper's final submit,
    a scenario's last steps. A block that drops two tail actions while adding
    two of its own scores an equal count, and a check that only counts passes
    it: blind to the exact fault it exists for. Families are compared as a
    multiset so the drop shows whatever was added in its place.
    """
    src = tmp_path / "src"
    src.mkdir(exist_ok=True)
    (src / "Form.java").write_text(TAIL_SOURCE, encoding="utf-8")
    test = tmp_path / "t.sigma"
    test.write_text(TAIL_DROPPED, encoding="utf-8")
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--source-root", str(src),
         "--symbol", "Form.save", "--block", "Save it", str(test)],
        capture_output=True, text=True)
    assert r.returncode == 1, r.stdout
    assert "4 actions" in r.stdout, "the counts really are equal"
    assert "PRESS" in r.stdout, "the missing family must be named"


def test_a_value_returning_helper_is_not_walked_into(tmp_path):
    """A getter returns a locator; it does not perform the step.

    Recursing into one found an action in something it called and reported
    three correct verify blocks as missing an action nothing performs.
    """
    src = tmp_path / "src"
    src.mkdir(exist_ok=True)
    (src / "Glue.java").write_text('''\
public class Glue {
    public void verify(String s) {
        By by = Glue.locatorFor(s);
        SeleniumActions.VerifyText(by, s);
    }
    public static By locatorFor(String s) {
        SeleniumActions.click(byCache, "warm the cache");
        return By.id(s);
    }
}
''', encoding="utf-8")
    test = tmp_path / "t.sigma"
    test.write_text('test "x" {\n  block "Verify it" {\n    verifyElementText(element.a, "b")\n  }\n}\n',
                    encoding="utf-8")
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--source-root", str(src),
         "--symbol", "Glue.verify", "--block", "Verify it", str(test)],
        capture_output=True, text=True)
    assert "click" not in r.stdout, "walked into the getter"
