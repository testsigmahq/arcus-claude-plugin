"""Executable form of the Cucumber adapter's normalisation rule.

Test tooling only. A Source Adapter is a document an agent reads (ADR-0004) and
nothing in this module ships with the plugin. It exists so the adapter's stated
rule can be checked against the adapter's stated counts, which turns "precise
enough that two people applying it get the same count" into something the suite
verifies rather than something the document claims.

If the rule in `adapters/cucumber-java.md` and this module ever disagree, the
adapter's own enumeration test fails.
"""

import re
from collections import Counter

#: Gherkin step keywords. `And` and `But` inherit the previous step's keyword,
#: and the keyword is dropped by normalisation anyway, so all are equivalent.
KEYWORDS = ("Given", "When", "Then", "And", "But", "*")

#: `*` is a valid step keyword and takes no word boundary after it, unlike the
#: word keywords.
_KEYWORD = re.compile(r"^\s*(?:(?:Given|When|Then|And|But)\b|\*)\s*")
_OUTLINE = re.compile(r"<[^<>]*>")
_DOUBLE_QUOTED = re.compile(r'"[^"]*"')
#: A single-quoted span is a parameter only when both quotes sit on a boundary.
#: Without that, "I don't see the user's name" reads `'t see the user'` as one.
_SINGLE_QUOTED = re.compile(r"(?<![\w'])'([^']*)'(?![\w])")
#: A number is a parameter only when it stands alone, so `3` in `3 results` is
#: one and `05` in `ILPN05` is not. Comma groups stay a single number.
_NUMBER = re.compile(r"(?<![\w.])\d+(?:,\d{3})*(?:\.\d+)?(?![\w.])")
#: Gherkin allows localised keywords via a `# language:` pragma. This reader
#: only knows the English ones, and a localised file would otherwise yield zero
#: steps and a Collapse Ratio of nothing, which reads as a valid answer.
_LANGUAGE_PRAGMA = re.compile(r"^\s*#\s*language\s*:\s*([A-Za-z-]+)", re.MULTILINE)
_WHITESPACE = re.compile(r"\s+")
_TRAILING_PUNCTUATION = ".,;:!"

#: Used while rewriting so a replacement cannot be re-matched by a later pass.
#: A quoted span holding an outline placeholder produced nested quotes without it.
_SENTINEL = "\x00param\x00"

PARAM = '"<param>"'
NUMBER = "<number>"


class UnsupportedLanguage(ValueError):
    """The feature file declares localised keywords this reader cannot read."""


def check_language(feature_text):
    """Raise when a feature file declares a language other than English.

    Silence here would be worse than an error: a localised suite would produce
    no Source Steps at all, and a report of zero looks like an answer.
    """
    match = _LANGUAGE_PRAGMA.search(feature_text)
    if match and match.group(1).lower() not in ("en", "en-us", "en-gb"):
        raise UnsupportedLanguage(
            f"feature file declares '# language: {match.group(1)}'; this reader "
            "knows only the English Gherkin keywords"
        )


def step_lines(feature_text):
    """Every step line in a feature file, in order, as written.

    Skips comments, data-table rows, and anything inside a docstring, so a line
    that merely looks like a step in prose is not counted as one.
    """
    check_language(feature_text)
    lines = []
    in_docstring = False
    for raw in feature_text.splitlines():
        stripped = raw.strip()
        if stripped.startswith('"""') or stripped.startswith("'''"):
            in_docstring = not in_docstring
            continue
        if in_docstring or not stripped:
            continue
        if stripped.startswith("#") or stripped.startswith("|") or stripped.startswith("@"):
            continue
        if _KEYWORD.match(stripped):
            lines.append(stripped)
    return lines


def normalise_step(line):
    """The canonical form of one step line, per the adapter's rule.

    Two lines with the same canonical form are the same Source Step. Raises
    ValueError for a line that is not a step.
    """
    if not _KEYWORD.match(line or ""):
        raise ValueError(f"not a step line: {line!r}")

    text = _KEYWORD.sub("", line, count=1)

    # Quoted spans first, so a placeholder written inside one is swallowed with
    # it rather than rewritten into nested quotes. Every literal becomes one
    # sentinel, so quoting style is not part of a Source Step's identity, and
    # the sentinel carries no angle brackets for a later pass to re-match.
    text = _DOUBLE_QUOTED.sub(_SENTINEL, text)
    text = _SINGLE_QUOTED.sub(_SENTINEL, text)
    text = _OUTLINE.sub(_SENTINEL, text)
    # Trailing punctuation goes before the number pass, not after. A number
    # abutting a full stop is excluded by the pattern's trailing lookahead,
    # which exists to leave version-like `1.2.3` alone, so stripping the stop
    # afterwards left `I see 5.` and `I see 5` as two different Source Steps.
    text = _WHITESPACE.sub(" ", text).strip()
    text = text.rstrip(_TRAILING_PUNCTUATION)
    text = _NUMBER.sub(NUMBER, text)
    return text.replace(_SENTINEL, PARAM)


def distinct_source_steps(feature_texts):
    """Map each distinct Source Step to how many times it occurs."""
    counts = Counter()
    for text in feature_texts:
        for line in step_lines(text):
            counts[normalise_step(line)] += 1
    return dict(counts)


def total_step_occurrences(feature_texts):
    """How many step lines there are in total, distinct or not."""
    return sum(len(step_lines(text)) for text in feature_texts)


def collapse_ratio(feature_texts):
    """Total source steps divided by distinct Source Steps."""
    distinct = distinct_source_steps(feature_texts)
    if not distinct:
        return 0.0
    return total_step_occurrences(feature_texts) / len(distinct)
