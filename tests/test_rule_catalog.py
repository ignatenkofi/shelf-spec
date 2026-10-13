"""SPEC 9.1 lists exactly the rules the engine emits, at the severity it emits them.

CONTRIBUTING.md asks that every ``Finding`` rule land with its 9.1 entry,
and nothing checked it: ``reserved-m1`` was emitted for a season without a
9.1 line (#55 item 4), and the reverse — a 9.1 line that no code emits —
would be just as silent (shelf-spec#60).

The engine's side is read from the source rather than from a registry:
every ``Finding(...)`` and ``ManifestError(...)`` call under
``src/shelf_spec`` with its rule id and severity. A rule id that is not a
string literal cannot be reconciled, so it fails here — except the one
re-wrap of the manifest gate, ``Finding(rule=exc.rule,
severity="config-error")`` in ``validate_shelf``, whose ids are the
``ManifestError`` literals themselves.
"""

from __future__ import annotations

import ast
import re

from tests.conftest import REPO_ROOT

SRC = REPO_ROOT / "src" / "shelf_spec"
SPEC = REPO_ROOT / "spec" / "SPEC.md"

_SEVERITY_HEADING = re.compile(r"^(config-error|error|warning|info)\b[^:]*:$")
_RULE_BULLET = re.compile(r"^- `([a-z0-9][a-z0-9-]*)` — ")


def _literal(node: ast.expr | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _argument(call: ast.Call, index: int, keyword: str) -> ast.expr | None:
    if len(call.args) > index:
        return call.args[index]
    return next((kw.value for kw in call.keywords if kw.arg == keyword), None)


def engine_rules() -> dict[str, set[str]]:
    """Rule id -> the severities the package emits it with."""
    emitted: dict[str, set[str]] = {}
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for call in ast.walk(tree):
            if not isinstance(call, ast.Call):
                continue
            func = call.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
            if name not in ("Finding", "ManifestError"):
                continue
            where = f"{path.relative_to(REPO_ROOT)}:{call.lineno}"
            rule = _argument(call, 0, "rule")
            if name == "ManifestError":
                severity = "config-error"  # validate_shelf reports the gate at this severity
            else:
                severity = _literal(_argument(call, 1, "severity"))
                assert severity, f"{where}: Finding() severity is not a string literal"
            if _literal(rule):
                emitted.setdefault(_literal(rule), set()).add(severity)
            elif (
                name == "Finding"
                and severity == "config-error"
                and isinstance(rule, ast.Attribute)
                and rule.attr == "rule"
            ):
                continue  # the manifest gate re-wrapped: its ids are the ManifestError literals
            else:
                raise AssertionError(
                    f"{where}: {name}() rule id is not a string literal, "
                    "so SPEC 9.1 cannot be reconciled with it"
                )
    return emitted


def spec_rules() -> dict[str, str]:
    """Rule id -> severity, from the bullet lists of SPEC section 9.1."""
    text = SPEC.read_text(encoding="utf-8")
    section = re.search(r"^### 9\.1 Rules\n(.*?)^### 9\.2 ", text, re.DOTALL | re.MULTILINE)
    assert section, "SPEC.md has no '### 9.1 Rules' section followed by '### 9.2'"
    listed: dict[str, str] = {}
    severity: str | None = None
    for line in section.group(1).splitlines():
        heading = _SEVERITY_HEADING.match(line)
        if heading:
            severity = heading.group(1)
            continue
        bullet = _RULE_BULLET.match(line)
        if bullet:
            rule = bullet.group(1)
            assert severity, f"9.1 lists `{rule}` before any severity heading"
            assert rule not in listed, f"9.1 lists `{rule}` twice"
            listed[rule] = severity
        elif line.startswith("- "):
            raise AssertionError(f"9.1 bullet not in the '- `rule-id` — ...' form: {line!r}")
    return listed


def test_parsers_see_both_catalogs() -> None:
    # Guard against a vacuous pass: an empty parse on either side would make
    # the comparisons below compare nothing. Both name the same anchor rules.
    spec, engine = spec_rules(), engine_rules()
    for rule in ("manifest-missing", "docs-root-missing", "no-policy", "reserved-m1"):
        assert rule in spec, f"9.1 parse lost `{rule}`"
        assert rule in engine, f"engine parse lost `{rule}`"


def test_spec_9_1_lists_exactly_the_rules_the_engine_emits() -> None:
    spec, engine = spec_rules(), engine_rules()
    not_in_spec = sorted(set(engine) - set(spec))
    never_emitted = sorted(set(spec) - set(engine))
    assert not not_in_spec, f"emitted by the engine, missing from SPEC 9.1: {not_in_spec}"
    assert not never_emitted, f"listed in SPEC 9.1, emitted nowhere: {never_emitted}"


def test_spec_9_1_severities_match_the_engine() -> None:
    spec, engine = spec_rules(), engine_rules()
    mismatched = {
        rule: {"spec": spec[rule], "engine": sorted(severities)}
        for rule, severities in sorted(engine.items())
        if rule in spec and severities != {spec[rule]}
    }
    assert not mismatched, f"severity differs between SPEC 9.1 and the engine: {mismatched}"
