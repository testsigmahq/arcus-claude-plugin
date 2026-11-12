# Platforms when writing

A project lists its platforms (`web`, `android`, `ios`). `arcus check` compiles **every test against every one of
them**, and a step that a platform skips is an error (`ARC2001`).

## The consequence

Platforms belong to the project, not to a test. A test with a web-only step (`nav`, `hover`, `press`, cookies…) cannot
live in a project whose platforms include `android` or `ios`: `check` fails on the mobile ones. And a test with
mobile-only steps (`swipe`, `launch app`, `press back`…) fails on `web`.

So before writing, compare what the user wants to test with the project's platforms:

- **They match:** go on.
- **The test is for one platform, and the project has more:** tell the user. Options: a separate Arcus project for that
  platform (`arcus init --project <id>` adds it to the same repo), or changing this project's platforms with
  `arcus project platforms add|remove` (their decision, since it makes `check` stricter or looser for every test).
  Do not rewrite a test into a weaker form just to make it compile everywhere.

## Writing for several platforms

- Default `arcus docs --project <name>` lists only the forms that compile on all of the project's platforms. Write from
  that list.
- A locator mode that a platform lacks is skipped there. For a target that has to work everywhere, make an element with
  one locator per platform (`only <platform>`). See `${CLAUDE_PLUGIN_ROOT}/references/elements.md`.
- Looping over an element and some condition forms are web only. `arcus docs --all` marks the platforms of every form.

## Mobile

Authoring for Android and iOS works like web: `arcus docs` lists the device actions. `arcus run` and `arcus verify` run
**web and Android**. They do not run iOS. How a run finds its tools, device and app is in
`${CLAUDE_PLUGIN_ROOT}/references/running.md`. `arcus run` and `arcus verify` first make the same check as
`arcus check`, but for the platform of the run only. A web-only step on an Android run is refused (`ARC2001`), not run.

### Writing for Android

`arcus docs` is the source for the language, and `arcus check` is the judge. The notes below are what real runs on an
Android emulator showed. Use them where `arcus docs` is wrong or says nothing. If `arcus check` and a note disagree,
`arcus check` wins.

**Steps that work:** `launch app`, `click` (also `double`, `hold <duration>`, and `at x%,y%`), `type`, `clear`,
`hide keyboard`, `press back`, `swipe`, `scroll by`, `scroll to`, `screenshot`, `wait until`, `verify … visible` and
`verify … absent`, and `{env.name}` values given with `--var`. Element files work when their locators are
`only android`, used through `@path`.

**The target of a gesture comes after the direction:** `swipe up locate …`, `scroll by 0,400 locate …`,
`pinch out locate …`.

**Locators that work:** `locate text "<full text>"` (the whole text only), `locate label`, `locate name`,
`locate xpath`, `locate nth`, `locate accessibility-id`, `locate class`, `locate android-id` and
`locate android-uiautomator`. For part of a text, use xpath `contains(@text,'…')` or uiautomator `textContains`.

Apps built with Jetpack Compose often have no ids and no content descriptions. Find buttons by their visible text. Find
text fields by position, for example `locate xpath "(//android.widget.EditText)[1]"`.

**`arcus check` refuses these on Android, so do not write them:**

- the locators `text ~`, `label ~`, `role`, `placeholder`, `title`, `alt`, `attribute` and `where`;
- `nav`, and `scroll top` and `scroll bottom`;
- `for x in locate …`;
- the text comparisons `^=`, `$=`, `<`, `<=`, `>` and `>=`;
- page and tab conditions.

**Web view only.** `locate css`, and the element locators `css`, `tag` and `link-text`, work only inside a web view,
after `switch context webview`.

**Do not use on Android:** an element file `locator chain` passes `arcus check` but the runner rejects it. An element
`image` locator does not work.

**Not tested on a device yet.** Device actions (rotate, lock, wifi, bluetooth, mobile data), alerts, web views, install
and uninstall of an app, and image actions. They may work. Do not promise it. If the user needs one, write it, run it,
and say what happened. A physical phone and Windows have not been tested either.

## What cannot be written yet

If the user asks for one of these, say it is not supported yet, and do not work around it:

- `api` steps and add-on steps (blocked by the compile).
- Groups and calls to groups.
- `host` lines in an element.
- Header lines above a test (`sigmascript`, `platform`, `tags`).
- Sub-folders under `tests/`.
- Any action or form that `arcus docs --all` does not list.
