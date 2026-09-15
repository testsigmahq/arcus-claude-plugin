# 32 — The format decodes five escapes, and JSON emits more

**What to build:** `.sigma` decodes exactly five escapes in a quoted string: `"`, `\`,
newline, tab, and `${`. Anything else that arrives as a backslash escape has **the
backslash dropped and no diagnostic raised**.

So `"before\u001fafter"` reads back as the literal `beforeu001fafter`, and `"C:\path"`
silently becomes `C:path`. Nothing refuses either. Nothing reports either. The value is
simply not what was written, and the first time anyone notices is when a test drives the
wrong string.

**Why this reaches a Migration.** Anything generating `.sigma` text with a JSON serialiser
emits `\uXXXX` for control characters and `\\` conventions the format does not share. A
Windows path, a regex, a tab written as `\t` by a tool rather than by the format's own
escape — each lands as quietly corrupted text. The plugin never says which escapes exist,
so nothing tells an author to quote with the format's five rather than with a language's.

**Why this is worse than an ordinary authoring mistake.** It is the fault class the checks
are built around: it compiles, it passes preflight, and it survives a round trip, because
the mangled string is a perfectly valid string. `references/fault-classes.md` exists for
faults with exactly this shape.

**What to say, and where.** `authoring.md` owns what a correct file looks like and already
has a section on the layout the validator enforces. The five escapes belong there, with
the consequence stated: an unknown escape loses its backslash, in silence. Name the
generated-text case, because that is how it arrives — a claim, a locator, a body, anything
assembled by code rather than typed.

**Blocked by:** nothing.

**Status:** ready-for-agent

- [ ] `authoring.md` names the five escapes the format decodes
- [ ] It says an unknown escape drops its backslash and raises nothing
- [ ] Both measured cases appear: a `\uXXXX` sequence, and a Windows path
- [ ] It says to quote with the format's escapes rather than a serialiser's
- [ ] `fault-classes.md` carries it, since it compiles and survives a round trip
- [ ] A document test holds the escape set, so a sixth cannot be assumed
