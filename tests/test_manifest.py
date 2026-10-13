"""Manifest loading and the config-error gate."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from shelf_spec.engine.manifest import ManifestError, load_manifest, load_schema
from tests.conftest import legacy_manifest


def test_load_valid_manifest(memshelf_like: Path) -> None:
    m = load_manifest(memshelf_like)
    assert m.spec_version == "0.1"
    assert m.mode == "single"
    assert m.profile == "memory"
    assert m.categories == ["topics", "research", "sessions"]
    assert m.index_generated_by == "docshelf-mcp"
    assert m.docs_root_path == memshelf_like / "docs"


def test_defaults_applied(tmp_path: Path) -> None:
    (tmp_path / "shelf.yml").write_text('spec_version: "0.1"\nmode: single\n', encoding="utf-8")
    m = load_manifest(tmp_path)
    assert m.profile == "document"
    assert m.docs_root == "docs"
    assert m.index_path == "INDEX.md"
    assert m.index_generated_by == "docshelf-mcp"
    assert m.ledger_path == "ledger.tsv"
    assert m.policy_path == "POLICY.md"
    assert m.categories == []
    assert not m.has_agents and not m.has_provenance


def test_missing_manifest_is_config_error(tmp_path: Path) -> None:
    with pytest.raises(ManifestError) as exc:
        load_manifest(tmp_path)
    assert exc.value.rule == "manifest-missing"


def test_unparseable_yaml_is_config_error(tmp_path: Path) -> None:
    (tmp_path / "shelf.yml").write_text("spec_version: [unclosed\n", encoding="utf-8")
    with pytest.raises(ManifestError) as exc:
        load_manifest(tmp_path)
    assert exc.value.rule == "manifest-invalid"


@pytest.mark.parametrize(
    "line",
    [
        "name: 2026-02-30",  # an impossible date: ValueError from the date constructor
        "name: !!int abc",  # ValueError
        "name: !!bool maybe",  # KeyError
    ],
)
def test_value_yaml_cannot_build_is_config_error(tmp_path: Path, line: str) -> None:
    # PyYAML raises these as plain exceptions, not YAMLError: before #59 they
    # escaped the gate as a traceback instead of a config-error.
    (tmp_path / "shelf.yml").write_text(f'spec_version: "0.1"\nmode: single\n{line}\n', "utf-8")
    with pytest.raises(ManifestError) as exc:
        load_manifest(tmp_path)
    assert exc.value.rule == "manifest-invalid"


def test_non_utf8_manifest_is_config_error(tmp_path: Path) -> None:
    (tmp_path / "shelf.yml").write_bytes(b'spec_version: "0.1"\nmode: single\nname: \xe9t\xe9\n')
    with pytest.raises(ManifestError) as exc:
        load_manifest(tmp_path)
    assert exc.value.rule == "manifest-invalid"
    assert "UTF-8" in exc.value.detail


def test_schema_violation_is_config_error(tmp_path: Path) -> None:
    (tmp_path / "shelf.yml").write_text('spec_version: "0.1"\nmode: banana\n', encoding="utf-8")
    with pytest.raises(ManifestError) as exc:
        load_manifest(tmp_path)
    assert exc.value.rule == "manifest-invalid"
    assert "banana" in exc.value.detail


def test_unknown_top_level_key_is_config_error(tmp_path: Path) -> None:
    (tmp_path / "shelf.yml").write_text(
        'spec_version: "0.1"\nmode: single\ntypo_field: 1\n', encoding="utf-8"
    )
    with pytest.raises(ManifestError) as exc:
        load_manifest(tmp_path)
    assert exc.value.rule == "manifest-invalid"


def test_policy_patterns_accepted(tmp_path: Path) -> None:
    """``policy.patterns`` names the machine-readable pattern file (SPEC 4.5).

    memshelf-mcp writes it into every manifest it scaffolds; a schema that
    refused the key made every live memshelf shelf a config-error.
    """
    (tmp_path / "shelf.yml").write_text(
        'spec_version: "0.1"\n'
        "mode: single\n"
        "profile: memory\n"
        "policy:\n"
        "  path: POLICY.md\n"
        "  patterns: POLICY.patterns\n",
        encoding="utf-8",
    )
    m = load_manifest(tmp_path)
    assert m.policy_path == "POLICY.md"
    assert m.raw["policy"]["patterns"] == "POLICY.patterns"


def test_policy_patterns_escaping_path_is_config_error(tmp_path: Path) -> None:
    """Same path contract as ``policy.path``: relative to the root, no ``..``."""
    (tmp_path / "shelf.yml").write_text(
        'spec_version: "0.1"\nmode: single\npolicy:\n  patterns: ../POLICY.patterns\n',
        encoding="utf-8",
    )
    with pytest.raises(ManifestError) as exc:
        load_manifest(tmp_path)
    assert exc.value.rule == "manifest-invalid"
    assert "patterns" in exc.value.detail


def test_unknown_policy_key_is_config_error(tmp_path: Path) -> None:
    """Opening ``policy`` for ``patterns`` must not open it for typos."""
    (tmp_path / "shelf.yml").write_text(
        'spec_version: "0.1"\nmode: single\npolicy:\n  path: POLICY.md\n  typo_field: 1\n',
        encoding="utf-8",
    )
    with pytest.raises(ManifestError) as exc:
        load_manifest(tmp_path)
    assert exc.value.rule == "manifest-invalid"
    assert "typo_field" in exc.value.detail


def test_missing_required_field_is_config_error(tmp_path: Path) -> None:
    (tmp_path / "shelf.yml").write_text("mode: single\n", encoding="utf-8")
    with pytest.raises(ManifestError) as exc:
        load_manifest(tmp_path)
    assert exc.value.rule == "manifest-invalid"
    assert "spec_version" in exc.value.detail


def test_external_manifest_path(legacy_like: Path) -> None:
    m = load_manifest(legacy_like, legacy_manifest())
    assert m.shelf_root == legacy_like
    assert m.docs_root == "DOCS/markdown"
    assert m.index_generated_by == "external"
    assert m.extra_dirs == ["DOCS/compressed"]
    # The tree itself still has no manifest of its own.
    assert not (legacy_like / "shelf.yml").exists()


def test_reserved_fields_accepted(tmp_path: Path) -> None:
    (tmp_path / "shelf.yml").write_text(
        'spec_version: "0.1"\n'
        "mode: multi\n"
        "agents: {path: agents.yml}\n"
        "provenance: {dir: provenance/, required: true}\n",
        encoding="utf-8",
    )
    m = load_manifest(tmp_path)
    assert m.mode == "multi"
    assert m.has_agents and m.has_provenance


# --- path rules (SPEC 3, shelf-spec#58) ---------------------------------------
#
# Every path field carries one pattern. Each bad value below passed the old
# one in Python's `re` — `$` matches before a final newline, `.` matches a
# carriage return and U+2028/U+2029 — while ECMA-262, the dialect of JSON
# Schema patterns, refused it (or, for the rest of the control characters,
# both engines let it through). The value reaches the schema intact: PyYAML
# refuses a raw control character in the stream itself, so the manifest
# spells it as an escape and the helper checks what YAML hands over — a
# refusal at the YAML layer would prove nothing about the schema.

#: field -> YAML that sets it, keyed by the path the schema error names.
PATH_FIELDS = {
    "docs_root": "docs_root: {v}",
    "categories/0": "categories:\n  - {v}",
    "index/path": "index:\n  path: {v}",
    "ledger/path": "ledger:\n  path: {v}",
    "policy/path": "policy:\n  path: {v}",
    "policy/patterns": "policy:\n  patterns: {v}",
    "extra_dirs/0": "extra_dirs:\n  - {v}",
    "agents/path": "agents:\n  path: {v}",
    "provenance/dir": "provenance:\n  dir: {v}",
}

BAD_PATH_VALUES = {
    "trailing-newline": "docs\n",
    "carriage-return": "docs\r",
    "tab": "do\tcs",
    "nul": "docs\x00",
    "del": "docs\x7f",
    "c1-nel": "docs\x85",
    "line-separator": "docs\u2028",
    "paragraph-separator": "do\u2029cs",
}


def _yaml_quoted(value: str) -> str:
    """``value`` as a YAML double-quoted scalar, control characters escaped."""
    out = []
    for char in value:
        code = ord(char)
        if char in '"\\':
            out.append("\\" + char)
        elif code < 0x20 or 0x7F <= code <= 0x9F:
            out.append(f"\\x{code:02x}")
        elif code in (0x2028, 0x2029):
            out.append(f"\\u{code:04x}")
        else:
            out.append(char)
    return '"' + "".join(out) + '"'


def _manifest_with(shelf: Path, field: str, value: str) -> Path:
    text = (
        f'spec_version: "0.1"\nmode: single\n{PATH_FIELDS[field].format(v=_yaml_quoted(value))}\n'
    )
    node = yaml.safe_load(text)
    for part in field.split("/"):
        node = node[int(part)] if part.isdigit() else node[part]
    assert node == value, "the YAML layer changed the value before the schema saw it"
    (shelf / "shelf.yml").write_text(text, encoding="utf-8")
    return shelf


@pytest.mark.parametrize("field", list(PATH_FIELDS))
@pytest.mark.parametrize("value", list(BAD_PATH_VALUES.values()), ids=list(BAD_PATH_VALUES))
def test_path_with_control_character_or_separator_is_config_error(
    tmp_path: Path, field: str, value: str
) -> None:
    with pytest.raises(ManifestError) as exc:
        load_manifest(_manifest_with(tmp_path, field, value))
    assert exc.value.rule == "manifest-invalid"
    assert "fails shelf.schema.json" in exc.value.detail
    assert f"{field}: " in exc.value.detail


def test_category_dot_is_config_error(tmp_path: Path) -> None:
    # "." is docs_root itself: init created no directory for it and validate
    # said valid (#58).
    with pytest.raises(ManifestError) as exc:
        load_manifest(_manifest_with(tmp_path, "categories/0", "."))
    assert exc.value.rule == "manifest-invalid"
    assert "categories/0: " in exc.value.detail


@pytest.mark.parametrize("field", list(PATH_FIELDS))
@pytest.mark.parametrize("value", ["a.b", ".hidden", "my notes", "заметки"])
def test_path_rules_keep_ordinary_names(tmp_path: Path, field: str, value: str) -> None:
    assert load_manifest(_manifest_with(tmp_path, field, value)).raw


def test_schema_is_itself_valid() -> None:
    import jsonschema

    jsonschema.Draft202012Validator.check_schema(load_schema())
