"""Reading a Tosca subset export, for the tests only.

Test tooling. Never imported outside `tests/`. By ADR-0004 an adapter is a
document rather than a parser, and the plugin ships no Tosca parser; this exists
so the adapter's stated rules can be checked against a real export instead of
being taken on trust, exactly as `gherkin.py` does for the Cucumber adapter.

Every rule here is transcribed from `adapters/tosca-subset-export.md`. If the two
disagree, one of them is wrong and the suite should say so.
"""

import collections
import gzip
import json
import re

#: An action token in a value, e.g. `{Click}` or `{SENDKEYS[OH065M]}`.
_TOKEN = re.compile(r"\{([A-Za-z_]+)(\[[^\]]*\])?\}")

#: Association keys that carry ordered children, in the order to try them.
_CHILD_KEYS = ("Items", "TestSteps", "TestStepFolders")

#: What a TestStepFolderReference may dereference to.
_BLOCK_CLASSES = ("TestStepFolder", "ReuseableTestStepBlock")


class Export:
    """A loaded export: the flat entity list plus lookup by surrogate."""

    def __init__(self, entities):
        self.entities = entities
        self.by_surrogate = {e["Surrogate"]: e for e in entities}

    @classmethod
    def load(cls, path):
        with gzip.open(path) as handle:
            return cls(json.load(handle)["Entities"])

    def of_class(self, object_class):
        return [e for e in self.entities if e["ObjectClass"] == object_class]

    def attribute_names(self):
        return {k for e in self.entities for k in (e.get("Attributes") or {})}

    def dangling(self):
        """Surrogates referenced by some entity but absent from the file.

        The adapter claims the export is transitively closed; this is what
        checks it rather than repeating it.
        """
        missing = set()
        for entity in self.entities:
            for value in (entity.get("Assocs") or {}).values():
                for surrogate in value if isinstance(value, list) else [value]:
                    if isinstance(surrogate, str) and surrogate not in self.by_surrogate:
                        missing.add(surrogate)
        return missing

    # --- sequence ------------------------------------------------------------

    def _children(self, entity):
        assocs = entity.get("Assocs") or {}
        for key in _CHILD_KEYS:
            if assocs.get(key):
                return [
                    self.by_surrogate[s] for s in assocs[key] if s in self.by_surrogate
                ]
        return []

    def _dereference(self, entity):
        """Follow a TestStepFolderReference to the block it points at."""
        if entity["ObjectClass"] != "TestStepFolderReference":
            return entity
        for value in (entity.get("Assocs") or {}).values():
            surrogate = value[0] if isinstance(value, list) and value else (
                value if isinstance(value, str) else None
            )
            target = self.by_surrogate.get(surrogate)
            if target is not None and target["ObjectClass"] in _BLOCK_CLASSES:
                return target
        return entity

    def sequence(self, entity, seen=None, out=None):
        """The XTestStep surrogates of a test, in recovered document order.

        Order comes from position within the association arrays and nothing
        else. The visited set is not defensive: the entity graph cycles, and
        without one this recurses until the interpreter stops.
        """
        seen = set() if seen is None else seen
        out = [] if out is None else out
        surrogate = entity["Surrogate"]
        if surrogate in seen:
            return out
        seen.add(surrogate)
        if entity["ObjectClass"] == "XTestStep":
            out.append(surrogate)
        for child in self._children(self._dereference(entity)):
            self.sequence(child, seen, out)
        return out

    def cycles(self):
        """True when following associations revisits an entity already on the path."""
        colour = {}

        def visit(entity):
            surrogate = entity["Surrogate"]
            if colour.get(surrogate) == "open":
                return True
            if colour.get(surrogate) == "closed":
                return False
            colour[surrogate] = "open"
            for child in self._children(self._dereference(entity)):
                if visit(child):
                    return True
            colour[surrogate] = "closed"
            return False

        return any(visit(e) for e in self.of_class("TestCase"))

    def populated_test_cases(self):
        """Test cases from which at least one XTestStep is reachable."""
        return [tc for tc in self.of_class("TestCase") if self.sequence(tc)]

    def orphan_steps(self):
        """XTestStep surrogates reachable from no test case at all."""
        reachable = set()
        for test_case in self.of_class("TestCase"):
            reachable.update(self.sequence(test_case))
        return [e["Surrogate"] for e in self.of_class("XTestStep")
                if e["Surrogate"] not in reachable]

    # --- enumeration ---------------------------------------------------------

    def module_of(self, step):
        """The XModule surrogate a step references, or None."""
        for value in (step.get("Assocs") or {}).values():
            for surrogate in value if isinstance(value, list) else [value]:
                target = self.by_surrogate.get(surrogate) if isinstance(surrogate, str) else None
                if target is not None and target["ObjectClass"] == "XModule":
                    return surrogate
        return None

    def source_steps(self):
        """Occurrences per distinct Source Step, keyed by module name.

        The adapter's rule: two XTestStep entities are the same Source Step when
        they reference the same XModule surrogate. Counted by surrogate and
        reported by name, because names are edited and carry trailing space.
        """
        counts = collections.Counter()
        for step in self.of_class("XTestStep"):
            surrogate = self.module_of(step)
            if surrogate is None:
                continue
            name = (self.by_surrogate[surrogate].get("Attributes") or {}).get("Name")
            counts[name] += 1
        return counts

    def collapse_ratio(self):
        counts = self.source_steps()
        return round(sum(counts.values()) / len(counts), 2) if counts else 0.0

    # --- values --------------------------------------------------------------

    def values(self):
        return [
            str((e.get("Attributes") or {}).get("Value") or "")
            for e in self.of_class("XTestStepValue")
        ]

    def action_names(self):
        """Token counts under the adapter's normalisation.

        Action name only, upper-cased, bracketed argument dropped. Without this
        the same action counts as two: a real export spells it `{Click}` and
        `{CLICK}`.
        """
        counts = collections.Counter()
        for value in self.values():
            for name, _argument in _TOKEN.findall(value):
                counts[name.upper()] += 1
        return counts

    def literal_tokens(self):
        """Distinct token spellings before normalisation, for comparison."""
        return collections.Counter(
            match.group(0) for value in self.values() for match in re.finditer(r"\{[^}]*\}", value)
        )

    def multi_action_values(self):
        """Values holding more than one token: a sequence inside one string."""
        return [v for v in self.values() if len(_TOKEN.findall(v)) > 1]

    def wildcard_values(self):
        """Values that are loose comparisons rather than actions."""
        return [
            v for v in self.values()
            if not _TOKEN.findall(v) and (v.startswith("*") or v.endswith("*"))
        ]
